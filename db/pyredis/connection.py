import os
import socket
import threading
from itertools import chain
from queue import LifoQueue, Empty, Full
from time import time


class Connection:  # Manages TCP communication to and from a Redis server

    def __init__(self,
                 host='localhost',
                 port=6379,
                 db=0,
                 password=None,
                 socket_timeout=None,
                 socket_connect_timeout=None,
                 socket_keepalive=False,
                 socket_keepalive_options=None,
                 socket_type=0,
                 retry_on_timeout=False,
                 encoding='utf-8',
                 encoding_errors='strict',
                 decode_responses=False,
                 parser_class=DefaultParser,
                 socket_read_size=65536,
                 health_check_interval=0,
                 client_name=None,
                 username=None
                 ):
        self.pid = os.getpid()  # 注意
        self.host = host
        self.port = int(port)
        self.db = db
        self.username = username
        self.client_name = client_name
        self.password = password
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout or socket_timeout
        self.socket_keepalive = socket_keepalive
        self.socket_keepalive_options = socket_keepalive_options or {}
        self.socket_type = socket_type
        self.retry_on_timeout = retry_on_timeout
        self.health_check_interval = health_check_interval
        self.next_health_check = 0
        self._sock = None
        self._parser = parser_class(socket_read_size=socket_read_size)

    def __del__(self):  # 为什么要定义__del__
        self.disconnect()

    def can_read(self, timeout=0):  # Poll the socket to see if there's data that can be read.
        pass

    def connect(self):  # Connects to the Redis server if not already connected
        if not self._sock:
            self._sock = self._connect()
            try:
                self.on_connect()
            except RedisError:
                self.disconnect()
                raise

    def _connect(self):  # Create a TCP socket connection
        for res in socket.getaddrinfo(self.host, self.port, self.socket_type, socket.SOCK_STREAM):
            family, socktype, proto, canonname, socket_address = res
            sock = None
            try:
                sock = socket.socket(family, socktype, proto)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                if self.socket_keepalive:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                    for k, v in iteritems(self.socket_keepalive_options):
                        sock.setsockopt(socket.IPPROTO_TCP, k, v)
                '''
                socket_connect_timeout: 连接redis资源时的超时时间,可通过rds = redis.Redis(host='10.1.169.215', port=6379, socket_connect_timeout=3,socket_timeout=1)验证
                socket_timeout: 每条命令执行的超时时间,可以通过rds.eval("while(true) do local a=1; end",0)验证
                '''
                sock.settimeout(self.socket_connect_timeout)  # 注意,set the socket_connect_timeout before we connect
                sock.connect(socket_address)
                sock.settimeout(self.socket_timeout)  # 注意,set the socket_timeout now that we're connected
                return sock

            except socket.error as _:
                if sock is not None:
                    sock.close()

    def on_connect(self):  # Initialize the connection, authenticate and select a database(连接数据库)
        if self.username or self.password:  # if username and/or password are set, authenticate
            if self.username:
                auth_args = (self.username, self.password or '')
            else:
                auth_args = (self.password,)
            self.send_command('AUTH', *auth_args,
                              check_health=False)  # avoid checking health here -- PING will fail if we try to check the health prior to the AUTH

        if self.db:
            self.send_command('SELECT', self.db)

    def disconnect(self):  # Disconnects from the Redis server
        if self._sock:
            if os.getpid() == self.pid:  # 判断是否是当前进程
                shutdown(self._sock, socket.SHUT_RDWR)
            self._sock.close()
            self._sock = None

    def check_health(self):
        '''
        Connections maintain an open socket to the Redis server. Sometimes these sockets are interrupted or disconnected for a variety of reasons.
        When a connection becomes disconnected, the next command issued on that connection will fail and redis-py will raise a ConnectionError to the caller. 
        Health checks(health_check_interval) are performed just before a command is executed if the underlying connection has been idle for more than health_check_interval seconds. 
        If your application is running in an environment that disconnects idle connections after 30 seconds you should set the health_check_interval option to a value less than 30.
        '''
        if self.health_check_interval and time() > self.next_health_check:
            try:
                self.send_command('PING',
                                  check_health=False)  # Check the health of the connection with a PING/PONG,没有socket连接的话会先建立连接(此处check_health=False防止无穷调用)
                if nativestr(self.read_response()) != 'PONG':  # 更新next_health_check
                    raise ConnectionError('Bad response from PING health check')
            except (ConnectionError, TimeoutError):
                self.disconnect()
                self.send_command('PING', check_health=False)  # 重新建立连接
                if nativestr(self.read_response()) != 'PONG':
                    raise ConnectionError('Bad response from PING health check')

    def send_command(self, *args, **kwargs):  # Send an already packed command to the Redis server
        command = args
        if not self._sock:
            self.connect()
        if kwargs.get('check_health', True):
            self.check_health()
        try:
            for item in command:
                sendall(self._sock, item)
        except BaseException:
            self.disconnect()
            raise

    def read_response(self):
        try:
            response = self._parser.read_response()
        except BaseException:
            self.disconnect()
            raise
        if self.health_check_interval:
            self.next_health_check = time() + self.health_check_interval
        return response


class ConnectionPool:

    def __init__(self, connection_class=Connection, max_connections=None, **connection_kwargs):
        self.connection_class = connection_class
        self.connection_kwargs = connection_kwargs
        self.max_connections = max_connections or 2 ** 31  # 相当于sqlalchemy的pool_size + max_overflow
        self.reset()

        # this lock is acquired when the process id changes, such as after a fork. during this time, multiple threads in the child process could attempt to acquire this lock. 
        # the first thread to acquire the lock will reset the data structures and lock object of this pool. 
        # subsequent threads acquiring this lock will notice the first thread already did the work and simply release the lock.
        self._fork_lock = threading.Lock()

    def reset(self):
        self._lock = threading.RLock()
        self._created_connections = 0  # 已创建的连接数
        self._available_connections = []  # 连接池
        self._in_use_connections = set()  # 应为有删除(remove)操作,所以用set更高效,应为有ConnectionPool.disconnect操作,才需要_in_use_connections

        # this must be the last operation in this method. while reset() is called when holding _fork_lock(不然会出现某个线程获得了_fork_lock锁,更改了自身的pid,但还没来得及销毁_available_connections,就被其他线程直接使用了), 
        # other threads in this process can call _checkpid() which compares self.pid and os.getpid() without holding any lock (for performance reasons). 
        # keeping this assignment as the last operation ensures that those other threads will also notice a pid difference and block waiting for the first thread to release _fork_lock. 
        # when each of these threads eventually acquire _fork_lock, they will notice that another thread already called reset() and they will immediately release _fork_lock and continue on.
        self.pid = os.getpid()

    def _checkpid(self):
        # _checkpid() attempts to keep ConnectionPool fork-safe on modern systems. this is called by all ConnectionPool methods that manipulate the pool's state such as get_connection() and release().
        # when the process ids differ, _checkpid() assumes that the process has forked and that we're now running in the child process. the child process cannot use the parent's file descriptors (e.g., sockets).
        # therefore, when _checkpid() sees the process id change, it calls reset() in order to reinitialize the child's ConnectionPool. this will cause the child to make all new connection objects.
        # _checkpid() is protected by self._fork_lock to ensure that multiple threads in the child process do not call reset() multiple times.
        # there is an extremely small chance this could fail in the following scenario(很容易模拟,在with self._fork_lock代码块内部添加sleep方便构造场景):
        #   1. process A calls _checkpid() for the first time and acquires self._fork_lock.
        #   2. while holding self._fork_lock, process A forks (the fork() could happen in a different thread owned by process A)
        #   3. process B (the forked child process) inherits the ConnectionPool's state from the parent. that state includes a locked _fork_lock. 
        #      process B will not be notified when process A releases the _fork_lock and will thus never be able to acquire the _fork_lock.
        if self.pid != os.getpid():
            with self._fork_lock:  # 极小概率出现死锁
                # time.sleep(2)    # 构造死锁场景
                if self.pid != os.getpid():
                    self.reset()  # reset() the instance for the new process if another thread hasn't already done so

    def make_connection(self):  # Create a new connection
        if self._created_connections >= self.max_connections:
            raise ConnectionError("Too many connections")
        self._created_connections += 1  # 非线程安全,不过无关紧要,因为你不可能在极短时间内创建许多连接,即使不准,统计误差也不会有2个
        return self.connection_class(**self.connection_kwargs)

    def get_connection(self):  # Get a connection from the pool
        self._checkpid()
        with self._lock:
            try:
                connection = self._available_connections.pop()
            except IndexError:
                connection = self.make_connection()
            self._in_use_connections.add(connection)
            try:
                connection.connect()  # ensure this connection is connected to Redis,connections that the pool provides should be ready to send a command(只有第一次使用才会建立连接)
                try:
                    if connection.can_read():
                        raise ConnectionError('Connection has data')
                except ConnectionError:
                    connection.disconnect()
                    connection.connect()
                    if connection.can_read():
                        raise ConnectionError('Connection not ready')
            except BaseException:
                self.release(connection)  # release the connection back to the pool so that we don't leak it
                raise
            return connection

    def release(self, connection):  # Releases the connection back to the pool
        self._checkpid()
        with self._lock:
            if connection.pid == self.pid:
                self._in_use_connections.remove(connection)
                self._available_connections.append(connection)

    def disconnect(self):  # Disconnects all connections in the pool
        self._checkpid()
        with self._lock:
            for connection in chain(self._available_connections, self._in_use_connections):
                connection.disconnect()


class BlockingConnectionPool(ConnectionPool):
    """
    Thread-safe blocking connection pool:
    from redis.client import Redis
    client = Redis(connection_pool=BlockingConnectionPool())
    It performs the same function as the default ConnectionPool implementation,The difference is that,
    in the event that a client tries to get a connection from the pool when all of connections are in use, rather than raising a ConnectionError,
    it makes the client wait ("blocks") for a specified number of seconds until a connection becomes available.
    """

    def __init__(self, max_connections=50, timeout=20, connection_class=Connection, queue_class=LifoQueue,
                 **connection_kwargs):
        self.queue_class = queue_class
        self.timeout = timeout  # how many seconds to wait for a connection to become available, or to block forever
        super().__init__(connection_class=connection_class, max_connections=max_connections,
                         **connection_kwargs)  # 调用父类构造函数,由于父类构造函数调用了reset,并且子类进行了重构,so子类的reset随后会被调用

    def reset(self):
        self.pool = self.queue_class(self.max_connections)
        while True:
            try:
                self.pool.put(None, block=False)  # 用None将连接池填满
            except Full:
                break
        self._connections = []  # Keep a list of actual connection instances so that we can disconnect them later.
        self.pid = os.getpid()  # 必须放最后赋值

    def make_connection(self):  # Make a fresh connection
        connection = self.connection_class(**self.connection_kwargs)
        self._connections.append(connection)
        return connection

    def get_connection(self):
        """
        Get a connection, blocking for self.timeout until a connection is available from the pool.
        If the connection returned is ``None`` then creates a new connection.Because we use a last-in first-out queue,
        """
        self._checkpid()
        try:
            connection = self.pool.get(block=True, timeout=self.timeout)
        except Empty:
            raise ConnectionError("No connection available.")
        if connection is None:
            connection = self.make_connection()

        try:
            connection.connect()
            try:
                if connection.can_read():
                    raise ConnectionError('Connection has data')
            except ConnectionError:
                connection.disconnect()
                connection.connect()
                if connection.can_read():
                    raise ConnectionError('Connection not ready')
        except BaseException:
            self.release(connection)
            raise
        return connection

    def release(self, connection):
        self._checkpid()
        if connection.pid == self.pid:
            try:
                self.pool.put_nowait(connection)
            except Full:  # perhaps the pool has been reset() after a fork? regardless,we don't want this connection
                pass

    def disconnect(self):
        self._checkpid()
        for connection in self._connections:
            connection.disconnect()
