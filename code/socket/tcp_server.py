import selectors
import socket
from concurrent.futures import ThreadPoolExecutor


class BlockingIO:  # 阻塞IO
    def __init__(self, ip='127.0.0.1', port=9999):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # AF_INET指使用IPv4协议,SOCK_STREAM指使用面向流的TCP协议
        self.server_sock.bind((ip, port))  # 监听端口,0.0.0.0表示绑定到所有的网络地址
        self.server_sock.listen(5)  # 调用listen()方法开始监听端口,传入的参数指定等待连接的最大数量

    def __del__(self):
        self.server_sock.close()

    @staticmethod
    def tcp_link(client_sock, addr):
        print('Accept new connection from {}:{}...'.format(*addr))
        client_sock.send(b'Welcome!')  # 必须是byte类型
        while True:
            data = client_sock.recv(1024)
            if data:
                client_sock.send(f'Hello, {data.decode()}'.encode())  # 如何需要发送多种类型的数据,可考虑用struct.pack struct.unpack
            else:
                client_sock.close()
                print('Connection from {}:{} closed.'.format(*addr))
                break

    def start(self):
        with ThreadPoolExecutor(10) as executor:  # 每个连接用线程处理,否则在处理连接过程中无法接受其他客户端连接
            while True:
                client_sock, addr = self.server_sock.accept()  # 等待并返回一个客户端的连接
                executor.submit(BlockingIO.tcp_link, client_sock, addr)


class IOMultiplexing:  # IO多路复用
    def __init__(self, ip="127.0.0.1", port=9999):
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind((ip, port))
        server_sock.listen(5)
        server_sock.setblocking(False)  # 创建一个非阻塞的TCP套接字
        # 选择最佳实现, epoll|kqueue|devpoll > poll > select, macOS下为kqueue,Linux下为epoll
        self.selector = selectors.DefaultSelector()  # 相当于epoll_create
        # 相当于epoll_ctl的EPOLL_CTL_ADD,让accept关联server
        self.selector.register(server_sock, selectors.EVENT_READ, self.accept)

    def accept(self, server_sock, mask):  # 回调函数,用于处理新连接的客户端套接字
        client_sock, addr = server_sock.accept()
        print(f"Accepted connection from {addr}")
        client_sock.setblocking(False)
        client_sock.send(b'Welcome!')
        self.selector.register(client_sock, selectors.EVENT_READ, self.read)

    def read(self, client_sock, mask):  # 回调函数,用于处理客户端套接字的写事件
        data = client_sock.recv(1024)
        if data:
            print(f"Received data from {client_sock.getpeername()}")
            client_sock.send(f'Hello, {data.decode()}'.encode())  # 回显数据给客户端
        else:  # client断开连接时会执行
            print("connection closed")
            self.selector.unregister(client_sock)  # 取消selector上的注册,相当于epoll_ctl的EPOLL_CTL_DEL
            client_sock.close()

    def start(self):
        while True:
            events = self.selector.select()  # 相当于epoll_wait,等待I/O事件发生
            for key, mask in events:  # mask就是register时指定的EVENT_READ或EVENT_WRITE
                callback = key.data
                callback(key.fileobj, mask)  # 调用相应的回调函数处理事件


if __name__ == "__main__":
    blocking_io = BlockingIO()
    blocking_io.start()

    # io_multiplexing = IOMultiplexing()
    # io_multiplexing.start()
