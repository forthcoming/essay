from itertools import chain
from time import time
import io, os, socket, threading

class Connection: # Manages TCP communication to and from a Redis server

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
        self.pid = os.getpid()   # 注意
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
        self.encoder = Encoder(encoding, encoding_errors, decode_responses)
        self._sock = None
        self._parser = parser_class(socket_read_size=socket_read_size)

    def __del__(self):  # 为什么要定义__del__
        self.disconnect()

    def can_read(self, timeout=0): # Poll the socket to see if there's data that can be read.
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
        for res in socket.getaddrinfo(self.host, self.port, self.socket_type,socket.SOCK_STREAM):
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
                sock.settimeout(self.socket_connect_timeout)    # 注意,set the socket_connect_timeout before we connect
                sock.connect(socket_address)
                sock.settimeout(self.socket_timeout)            # 注意,set the socket_timeout now that we're connected
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
            self.send_command('AUTH', *auth_args, check_health=False)  # avoid checking health here -- PING will fail if we try to check the health prior to the AUTH

        if self.db:
            self.send_command('SELECT', self.db)

    def disconnect(self):   # Disconnects from the Redis server
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
                self.send_command('PING', check_health=False)  # Check the health of the connection with a PING/PONG,没有socket连接的话会先建立连接(此处check_health=False防止无穷调用)
                if nativestr(self.read_response()) != 'PONG':  # 更新next_health_check
                    raise ConnectionError('Bad response from PING health check')
            except (ConnectionError, TimeoutError):
                self.disconnect()
                self.send_command('PING', check_health=False)   # 重新建立连接
                if nativestr(self.read_response()) != 'PONG':
                    raise ConnectionError('Bad response from PING health check')

    def send_command(self, *args, **kwargs): # Send an already packed command to the Redis server
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
    
        
class ConnectionPool: # 连接池只有在进程里有多线程时才会发挥其效率优势

    def __init__(self, connection_class=Connection, max_connections=None, **connection_kwargs):
        self.connection_class = connection_class
        self.connection_kwargs = connection_kwargs
        self.max_connections = max_connections or 2 ** 31
        self.reset()

    def reset(self):
        self.pid = os.getpid()
        self._created_connections = 0
        self._available_connections = []  # 数据来自_in_use_connections,so不会重复,append and pop operations are atomic
        self._in_use_connections = set()  # 去重,存在的意义仅仅是方便disconnect和统计用(比如查看当前有哪些连接正在被使用)
        self._check_lock = threading.Lock()

    def _checkpid(self):  # 在多进程中传递redis实例会被重置,应为多进程下类实例变量(_in_use_connections等)并不能共享,多线程不受影响
        if self.pid != os.getpid():
            with self._check_lock:  # 如果一个进程有多个线程,一个线程关闭后,另外一个线程也可能执行关闭操作,所以此处使用了锁
                if self.pid != os.getpid():  # 思考为啥这里还需要再判断一次
                    self.reset()

    def make_connection(self):
        "Create a new connection"
        if self._created_connections >= self.max_connections:
            raise ConnectionError("Too many connections")
        self._created_connections += 1  # 非线程安全,不过这无关紧要,因为你不可能在极短时间内创建许多连接,即使不准,统计误差也不会有2个
        return self.connection_class(**self.connection_kwargs)

    def get_connection(self, *keys, **options):
        "Get a connection from the pool"
        self._checkpid()
        try:
            connection = self._available_connections.pop()
        except IndexError:
            connection = self.make_connection()
        self._in_use_connections.add(connection)
        try:
            # ensure this connection is connected to Redis
            connection.connect()
            # connections that the pool provides should be ready to send a command. 
            # if not, the connection was either returned to the pool before all data has been read or the socket has been closed. 
            # either way, reconnect and verify everything is good.
            if not connection.is_ready_for_command():
                connection.disconnect()
                connection.connect()
                if not connection.is_ready_for_command():
                    raise ConnectionError('Connection not ready')
        except:
            self.release(connection) # release the connection back to the pool so that we don't leak it
            raise
        return connection

    def release(self, connection):
        self._checkpid()
        if connection.pid != self.pid:
            return
        self._in_use_connections.remove(connection)
        self._available_connections.append(connection)

    def disconnect(self):
        "Disconnects all connections in the pool"
        self._checkpid()
        all_conns = chain(self._available_connections,self._in_use_connections)
        for connection in all_conns:
            connection.disconnect()


class BlockingConnectionPool(ConnectionPool):
    """
    Thread-safe blocking connection pool::
    from redis.client import Redis
    client = Redis(connection_pool=BlockingConnectionPool())

    It performs the same function as the default ConnectionPool implementation, in that,
    it maintains a pool of reusable connections that can be shared by multiple redis clients (safely across threads if required).

    Use timeout to tell it either how many seconds to wait for a connection to become available, or to block forever:
    pool = BlockingConnectionPool(timeout=None) # Block forever.
    pool = BlockingConnectionPool(timeout=5)    # Raise a ConnectionError after five seconds if a connection is not available.
    """
    def __init__(self, max_connections=50, timeout=20,connection_class=Connection, **connection_kwargs):
        self.timeout = timeout
        # 调用父类构造函数,由于父类构造函数调用了reset,并且子类进行了重构,so子类的reset随后会被调用
        super(BlockingConnectionPool, self).__init__(connection_class=connection_class,max_connections=max_connections,**connection_kwargs)

    def reset(self):
        self.pid = os.getpid()
        self._check_lock = threading.Lock()
        self.pool = LifoQueue(self.max_connections)  # Create and fill up a thread safe queue with ``None`` values.
        while True:
            try:
                self.pool.put_nowait(None)   # 等价于self.pool.put(None,False)
            except Full:  # 队列超过上限
                break
        self._connections = []   # Keep a list of actual connection instances so that we can disconnect them later.

    def make_connection(self):
        "Make a fresh connection."
        connection = self.connection_class(**self.connection_kwargs)
        self._connections.append(connection)
        return connection

    def get_connection(self, *keys, **options):
        """
        Get a connection, blocking for self.timeout until a connection is available from the pool.
        If the connection returned is None then creates a new connection.
        Because we use a last-in first-out queue, the existing connections(having been returned to the pool after the initial None values were added) will be returned before None values. 
        This means we only create new connections when we need to, i.e.: the actual number of connections will only increase in response to demand.
        """
        self._checkpid()  # Make sure we haven't changed process.
        # Try and get a connection from the pool. If one isn't available within self.timeout then raise a ConnectionError.
        connection = None
        try:
            connection = self.pool.get(block=True, timeout=self.timeout)
        except Empty:
            # Note that this is not caught by the redis client and will be raised unless handled by application code. If you want never to
            raise ConnectionError("No connection available.")
        if connection is None:
            connection = self.make_connection()
        try:
            connection.connect()
            if not connection.is_ready_for_command():
                connection.disconnect()
                connection.connect()
                if not connection.is_ready_for_command():
                    raise ConnectionError('Connection not ready')
        except:
            self.release(connection)
            raise
        return connection

    def release(self, connection):
        self._checkpid()  # Make sure we haven't changed process.
        if connection.pid != self.pid:
            return
        try:
            self.pool.put_nowait(connection) # Put the connection back into the pool.
        except Full:  # perhaps the pool has been reset() after a fork? regardless, we don't want this connection
            pass

    def disconnect(self):  # Disconnects all connections in the pool.
        self._checkpid()
        for connection in self._connections:
            connection.disconnect()
