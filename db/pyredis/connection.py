from itertools import chain,os,threading
from queue import LifoQueue, Empty, Full
from redis.exceptions import ConnectionError
import socket,sys

class Connection:
    '''
    socket_connect_timeout: 连接redis资源时的超时时间,可通过rds = redis.Redis(host='10.1.169.215', port=6379, socket_connect_timeout=3,socket_timeout=1)验证
    socket_timeout: 每条命令执行的超时时间,可以通过rds.eval("while(true) do local a=1; end",0)验证
    '''
    def __init__(self,host='localhost',port=6379,db=0,password=None,socket_timeout=None,socket_connect_timeout=None,
        socket_keepalive=False,socket_keepalive_options=None,socket_type=0,retry_on_timeout=False):
        self.host = host
        self.port = int(port)
        self.db = db
        self.password = password
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout or socket_timeout
        self.socket_keepalive = socket_keepalive
        self.socket_keepalive_options = socket_keepalive_options or {}
        self.socket_type = socket_type
        self.retry_on_timeout = retry_on_timeout

    def connect(self): # Connects to the Redis server if not already connected
        try:
            self._sock = self._connect()
        except socket.timeout:
            raise("Timeout connecting to server")
        except socket.error:
            print(sys.exc_info()[1])
            raise('ConnectionError')

        if self.password:        # if a password is specified, authenticate
            self.send_command('AUTH', self.password)
        if self.db:              # if a database is specified, switch to it
            self.send_command('SELECT', self.db)
            
    def _connect(self):
        '''
        Create a TCP socket connection
        we want to mimic what socket.create_connection does to support ipv4/ipv6 
        but we want to set options prior to calling socket.connect()
        '''
        for res in socket.getaddrinfo(self.host, self.port, self.socket_type,socket.SOCK_STREAM):
            family, socktype, proto, canonname, socket_address = res
            sock = None
            try:
                sock = socket.socket(family, socktype, proto)
                # TCP_NODELAY
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

                # TCP_KEEPALIVE
                if self.socket_keepalive:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                    for k, v in self.socket_keepalive_options:
                        sock.setsockopt(socket.IPPROTO_TCP, k, v)

                # set the socket_connect_timeout before we connect
                sock.settimeout(self.socket_connect_timeout)

                # connect
                sock.connect(socket_address)

                # set the socket_timeout now that we're connected
                sock.settimeout(self.socket_timeout)
                return sock

            except socket.error as _:
                if sock is not None:
                    sock.close()

        if err is not None:
            raise err
           
        raise socket.error("socket.getaddrinfo returned an empty list")
        
        
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
                if self.pid == os.getpid():  # 思考为啥这里还需要再判断一次
                    return
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
