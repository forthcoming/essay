import socket
import threading
import time


def tcp_link(sock, addr):
    print('Accept new connection from {}:{}...'.format(*addr))
    sock.send(b'Welcome!')  # 必须是byte类型
    while True:
        data = sock.recv(1024)
        time.sleep(1)
        if not data or data == b'exit':
            break
        sock.send(f'Hello, {data}!'.encode())  # encode成bytes类型,如何需要发送多种类型的数据,可考虑用struct.pack struct.unpack
    sock.close()
    print('Connection from {}:{} closed.'.format(*addr))


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('127.0.0.1', 9999))  # 监听端口,0.0.0.0表示绑定到所有的网络地址
    server.listen(5)  # 调用listen()方法开始监听端口,传入的参数指定等待连接的最大数量
    while True:  # 服务器程序通过一个永久循环来接受来自客户端的连接,accept()会等待并返回一个客户端的连接
        # 接受一个新连接:
        sock, addr = server.accept()  # 每个连接都必须创建新线程(或进程)来处理,否则单线程在处理连接的过程中,无法接受其他客户端的连接
        # 创建新线程来处理TCP连接:
        t = threading.Thread(target=tcp_link, args=(sock, addr))
        t.start()


if __name__ == "__main__":
    main()
