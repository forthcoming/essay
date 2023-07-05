import os
import socket
import threading
from queue import Empty, Full, LifoQueue
from time import time

from redis.connection import PythonParser
from redis.exceptions import ChildDeadlockedError


# 仅包含unix代码实现部分,参考 https://github.com/redis/redis-py/blob/master/redis/connection.py


class Connection:
    def __init__(self, socket_timeout=None, socket_connect_timeout=None, socket_read_size=65536,
                 health_check_interval=0, host="localhost", port=6379, socket_keepalive=False,
                 socket_keepalive_options=None, socket_type=0):
        self.pid = os.getpid()
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self._sock = None
        self.host = host
        self.port = int(port)
        self.socket_keepalive = socket_keepalive
        self.socket_keepalive_options = socket_keepalive_options or {}
        self.socket_type = socket_type
        self.health_check_interval = health_check_interval
        self.next_health_check = 0
        self._socket_read_size = socket_read_size
        self._parser = PythonParser(socket_read_size=self._socket_read_size)

    def read_response(self, disable_decoding=False, *, disconnect_on_error: bool = True):
        """Read the response from a previously sent command"""
        try:
            response = self._parser.read_response(disable_decoding=disable_decoding)
        except socket.timeout:
            if disconnect_on_error:
                self.disconnect()
            raise TimeoutError("Timeout")
        except BaseException:
            # Also by default close in case of BaseException.  A lot of code
            # relies on this behaviour when doing Command/Response pairs.See #1128.
            if disconnect_on_error:
                self.disconnect()
            raise
        if self.health_check_interval:  # 每次执行完命令,都会更新next_health_check,interval时间内不会再触发check_health
            self.next_health_check = time() + self.health_check_interval
        return response

    def send_command(self, *args, **kwargs):
        command = args  # 把args中的命令打包(省略打包过程)
        if not self._sock:
            self.connect()
        if kwargs.get("check_health", True):  # guard against health check recursion
            self.check_health()
        try:
            for item in command:  # Send an already packed command to the Redis server
                self._sock.sendall(item)
        except socket.timeout:
            self.disconnect()
            raise TimeoutError("Timeout writing to socket")
        except BaseException:
            # BaseExceptions can be raised when a socket send operation is not
            # finished, e.g. due to a timeout.  Ideally, a caller could then re-try
            # to send un-sent data. However, the send_packed_command() API
            # does not support it so there is no point in keeping the connection open.
            self.disconnect()
            raise

    def can_read(self, timeout=0):  # Poll the socket to see if there's data that can be read.
        sock = self._sock
        if not sock:
            self.connect()
        return self._parser.can_read(timeout)

    @staticmethod
    def str_if_bytes(value: str | bytes) -> str:
        return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value

    def check_health(self):
        if self.health_check_interval and time() > self.next_health_check:
            # Check the health of the connection with a PING/PONG,没有socket连接的话会先建立连接(此处check_health=False防止无穷调用)
            self.send_command("PING", check_health=False)
            if Connection.str_if_bytes(self.read_response()) != "PONG":
                raise ConnectionError("Bad response from PING health check")

    def connect(self):  # Create a TCP socket connection to the Redis server
        if self._sock:
            return
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
                sock.settimeout(self.socket_connect_timeout)  # 连接redis资源时的超时时间
                sock.connect(socket_address)  # connect
                sock.settimeout(self.socket_timeout)  # 命令执行的超时时间,可通过rds.eval("while(true) do local a=1; end",0)验证
            except OSError as _:
                if sock is not None:
                    sock.close()
        self._sock = sock
        self.on_connect()

    def on_connect(self):
        self._parser.on_connect(self)
        # Initialize the connection, authenticate and select a database
        # if username or password:
        #     # avoid checking health here -- PING will fail if we try to check the health prior to the AUTH
        #     self.send_command("AUTH", *auth_args, check_health=False)
        # if client_name:
        #     self.send_command("CLIENT", "SETNAME", client_name)
        # if db:
        #     self.send_command("SELECT", db)

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
        self._parser.on_disconnect()
        if self._sock:
            conn_sock, self._sock = self._sock, None  # why??
            if os.getpid() == self.pid:
                conn_sock.shutdown(socket.SHUT_RDWR)
            conn_sock.close()

    def __del__(self):
        self.disconnect()


class ConnectionPool:
    def __init__(self, max_connections=None, **connection_kwargs):
        assert isinstance(max_connections, int) and max_connections >= 0
        self.connection_class = Connection
        self.connection_kwargs = connection_kwargs
        self.max_connections = max_connections or 2 ** 31  # 相当于sqlalchemy的pool_size + max_overflow
        self._fork_lock = threading.Lock()
        self.reset()

    def reset(self):
        self._lock = threading.Lock()
        self._created_connections = 0
        self._available_connections = []
        self._in_use_connections = set()  # 有remove操作,用set更高效
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
        2过程在with self._fork_lock代码块内部添加sleep方便构造场景
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
            connection.connect()
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
            if connection.pid == self.pid:
                self._in_use_connections.discard(connection)
                self._available_connections.append(connection)
            else:  # 池不拥有此连接,减少计数并且不要将其添加回池
                self._created_connections -= 1
                connection.disconnect()

    def disconnect(self):  # __del__中执行
        self._check_pid()
        with self._lock:
            for connection in self._available_connections:
                connection.disconnect()
            for connection in self._in_use_connections:
                connection.disconnect()


class BlockingConnectionPool(ConnectionPool):  # 线程安全的阻塞连接池,当所有连接都在使用时,如果客户试图从池中获得连接,会被阻塞最多指定秒数,直到连接可用
    def __init__(self, max_connections=50, timeout=20, queue_class=LifoQueue, **connection_kwargs):
        self.queue_class = queue_class
        self.timeout = timeout
        # 调用父类构造函数,由于父类构造函数调用了reset,并且子类进行了重构,so子类的reset随后会被调用
        super().__init__(max_connections=max_connections, **connection_kwargs)

    def reset(self):
        # Create and fill up a thread safe queue with ``None`` values.
        self.pool = self.queue_class(self.max_connections)
        while True:
            try:
                self.pool.put(None, block=False)  # 用None将连接池填满
            except Full:
                break
        self._connections = []  # Keep a list of actual connection instances so that we can disconnect them later.
        self.pid = os.getpid()  # 必须放最后赋值

    def make_connection(self):
        connection = self.connection_class(**self.connection_kwargs)
        self._connections.append(connection)
        return connection

    def get_connection(self):
        """
        阻塞获取(最多等待self.timeout)池中连接,如果返回的连接是None则创建一个新连接
        因为我们使用后进先出队列(栈),有效连接将在None之前返回,意味着只有真正需要时才会创建新链接
        """
        self._check_pid()
        try:
            connection = self.pool.get(block=True, timeout=self.timeout)
        except Empty:
            # Note that this is not caught by the redis client and will be
            # raised unless handled by application code. If you want never to
            raise ConnectionError("No connection available.")
        if connection is None:
            connection = self.make_connection()
        try:
            connection.connect()  # ensure this connection is connected to Redis
            # connections that the pool provides should be ready to send a command. if not,
            # the connection was either returned to the pool before all data has been read or the socket has been closed
            # either way, reconnect and verify everything is good.
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
        self._check_pid()
        if connection.pid != self.pid:
            connection.disconnect()
            self.pool.put(None, block=False)  # 不要将不属于自己的连接添加回池,而是添加一个占位符None,将导致池在需要时重新创建连接
            return
        try:
            self.pool.put(connection, block=False)
        except Full:  # perhaps the pool has been reset() after a fork? regardless,we don't want this connection
            pass

    def disconnect(self):
        self._check_pid()
        for connection in self._connections:
            connection.disconnect()
