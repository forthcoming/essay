import os
import socket
import threading
from itertools import chain
from queue import Empty, Full, LifoQueue

from redis.exceptions import ChildDeadlockedError


# 仅包含unix代码实现部分,参考 https://github.com/redis/redis-py/blob/master/redis/connection.py


class Connection:
    def __init__(self, socket_timeout=None, socket_connect_timeout=None, host="localhost", port=6379,
                 socket_keepalive=False, socket_keepalive_options=None, socket_type=0):
        self.pid = os.getpid()
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self._sock = None
        self.host = host
        self.port = port
        self.socket_keepalive = socket_keepalive
        self.socket_keepalive_options = socket_keepalive_options or {}
        self.socket_type = socket_type

    def connect(self):  # Create a TCP socket connection to the Redis server
        sock = None
        for res in socket.getaddrinfo(self.host, self.port, self.socket_type, socket.SOCK_STREAM):
            family, sock_type, proto, _, socket_address = res
            try:
                sock = socket.socket(family, sock_type, proto)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                if self.socket_keepalive:  # TCP_KEEPALIVE
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                    for k, v in self.socket_keepalive_options.items():
                        sock.setsockopt(socket.IPPROTO_TCP, k, v)
                sock.settimeout(self.socket_connect_timeout)  # set the socket_connect_timeout before we connect
                sock.connect(socket_address)  # connect
                sock.settimeout(self.socket_timeout)  # set the socket_timeout now that we're connected
            except OSError as _:
                if sock is not None:
                    sock.close()
        self._sock = sock

    def unix_domain_socket_connect(self, path: str):
        """
        socket以tcp/ip协议族为传输协议,用于跨主机通信,而unix domain socket(UDS)就是在socket的框架上发展出一种允许同一主机上的进程间通信(IPC)机制
        UDS可以在进程间传递数据、双向通信,并支持多个进程同时对同一个套接字进行读写操作,由于无需经过网络协议栈的处理,因此通信速度快,只是将数据从一个进程拷贝到另一个进程
        UDS只能使用在unix/linux系统,提供面向流和面向数据包两种API接口,其中SOCK_STREAM提供可靠的连接机制,确保数据的可靠传输和顺序传递
        """
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.socket_connect_timeout)
        sock.connect(path)
        sock.settimeout(self.socket_timeout)

    def disconnect(self):  # Disconnects from the Redis server
        if self._sock is None:
            return
        conn_sock, self._sock = self._sock, None
        if os.getpid() == self.pid:
            conn_sock.shutdown(socket.SHUT_RDWR)
        conn_sock.close()


class ConnectionPool:
    def __init__(self, max_connections=None, **connection_kwargs):
        assert isinstance(max_connections, int) and max_connections >= 0
        self.connection_class = Connection
        self.connection_kwargs = connection_kwargs
        self.max_connections = max_connections or 2 ** 31
        self._fork_lock = threading.Lock()
        self.reset()

    def reset(self):
        self._lock = threading.Lock()
        self._created_connections = 0
        self._available_connections = []
        self._in_use_connections = set()
        # 这必须是该方法中的最后一个操作,确保其他线程也将注意到pid差异并阻塞等待第一个线程释放_fork_lock,释放时子进程已更新完毕ConnectionPool
        self.pid = os.getpid()

    def _check_pid(self):
        """
        所有更改池状态的ConnectionPool方法都会调用_check_pid,子进程不能使用父进程的文件描述符(如sockets)
        当进程id改变(比如分叉)时获取_fork_lock锁,在此期间子进程的多个线程可以尝试获取此锁,持有此锁时最多调用一次reset
        第一个获取锁的线程将重置数据结构和锁等对象,后续线程获取此锁会注意到第一个线程已经完成了工作,直接释放锁
        在以下情况下有极小可能性失败：
        1. 进程A第一次调用_check_pid并获取_fork_lock
        2. 在持有_fork_lock同时,进程A进行分叉(fork可能发生在进程A的不同线程中)产生进程B
        3. 进程B从进程A继承ConnectionPool状态,该状态包括锁定的_fork_lock
        当进程A释放_fork_lock时,进程B不会收到通知,因此永远无法获取_fork_lock
        为了缓解这种可能的死锁,_check_pid最多只会等待5秒获取_fork_lock,超时抛出异常
        """
        if self.pid != os.getpid():
            acquired = self._fork_lock.acquire(timeout=5)
            if not acquired:
                raise ChildDeadlockedError
            try:
                if self.pid != os.getpid():
                    self.reset()
            finally:
                self._fork_lock.release()

    def get_connection(self, *keys, **options):  # 核心
        self._check_pid()
        with self._lock:
            try:
                connection = self._available_connections.pop()
            except IndexError:
                connection = self.make_connection()
            self._in_use_connections.add(connection)
        try:
            connection.connect()  # 这一步才开始真正建立连接
            # connections that the pool provides should be ready to send a command.
            # if not, the connection was either returned to the pool before all data has been read
            # or the socket has been closed. either way, reconnect and verify everything is good.
            if connection.can_read():
                raise ConnectionError("Connection not ready")
        except BaseException:
            self.release(connection)
            raise
        return connection

    def make_connection(self):
        if self._created_connections >= self.max_connections:
            raise ConnectionError("Too many connections")
        self._created_connections += 1
        return self.connection_class(**self.connection_kwargs)

    def release(self, connection):
        self._check_pid()
        with self._lock:
            self._in_use_connections.discard(connection)
            if connection.pid == self.pid:
                self._available_connections.append(connection)
            else:  # 池不拥有此连接,减少计数并且不要将其添加回池
                self._created_connections -= 1
                connection.disconnect()

    def disconnect(self, inuse_connections=True):  # __del__中执行
        self._check_pid()
        with self._lock:
            if inuse_connections:
                connections = chain(self._available_connections, self._in_use_connections)
            else:
                connections = self._available_connections
            for connection in connections:
                connection.disconnect()


class BlockingConnectionPool(ConnectionPool):  # 线程安全的阻塞连接池,当所有连接都在使用时,如果客户试图从池中获得连接,会被阻塞最多指定秒数,直到连接可用
    def __init__(self, max_connections=50, timeout=20, queue_class=LifoQueue, **connection_kwargs):
        self.queue_class = queue_class
        self.timeout = timeout
        super().__init__(max_connections=max_connections, **connection_kwargs)

    def reset(self):
        # Create and fill up a thread safe queue with ``None`` values.
        self.pool = self.queue_class(self.max_connections)
        while True:
            try:
                self.pool.put_nowait(None)
            except Full:
                break
        # Keep a list of actual connection instances so that we can disconnect them later.
        self._connections = []
        self.pid = os.getpid()

    def make_connection(self):
        connection = self.connection_class(**self.connection_kwargs)
        self._connections.append(connection)
        return connection

    def get_connection(self, *keys, **options):
        """
        Get a connection, blocking for ``self.timeout`` until a connection
        is available from the pool.

        If the connection returned is ``None`` then creates a new connection.
        Because we use a last-in first-out queue, the existing connections
        (having been returned to the pool after the initial ``None`` values
        were added) will be returned before ``None`` values. This means we only
        create new connections when we need to, i.e.: the actual number of
        connections will only increase in response to demand.
        """
        # Make sure we haven't changed process.
        self._check_pid()

        # Try and get a connection from the pool. If one isn't available within
        # self.timeout then raise a ``ConnectionError``.
        try:
            connection = self.pool.get(block=True, timeout=self.timeout)
        except Empty:
            # Note that this is not caught by the redis client and will be
            # raised unless handled by application code. If you want never to
            raise ConnectionError("No connection available.")

        # If the ``connection`` is actually ``None`` then that's a cue to make
        # a new connection to add to the pool.
        if connection is None:
            connection = self.make_connection()
        try:
            # ensure this connection is connected to Redis
            connection.connect()
            # connections that the pool provides should be ready to send
            # a command. if not, the connection was either returned to the
            # pool before all data has been read or the socket has been
            # closed. either way, reconnect and verify everything is good.
            try:
                if connection.can_read():
                    raise ConnectionError("Connection has data")
            except (ConnectionError, OSError):
                connection.disconnect()
                connection.connect()
                if connection.can_read():
                    raise ConnectionError("Connection not ready")
        except BaseException:
            # release the connection back to the pool so that we don't leak it
            self.release(connection)
            raise

        return connection

    def release(self, connection):
        "Releases the connection back to the pool."
        # Make sure we haven't changed process.
        self._check_pid()
        if connection.pid != self.pid:
            # pool doesn't own this connection. do not add it back
            # to the pool. instead add a None value which is a placeholder
            # that will cause the pool to recreate the connection if
            # its needed.
            connection.disconnect()
            self.pool.put_nowait(None)
            return

        # Put the connection back into the pool.
        try:
            self.pool.put_nowait(connection)
        except Full:
            # perhaps the pool has been reset() after a fork? regardless,
            # we don't want this connection
            pass

    def disconnect(self):
        self._check_pid()
        for connection in self._connections:
            connection.disconnect()
