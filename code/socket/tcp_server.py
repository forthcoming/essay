import socket
import time
from concurrent.futures import ThreadPoolExecutor


def tcp_link(sock, addr):
    print('Accept new connection from {}:{}...'.format(*addr))
    sock.send(b'Welcome!')  # 必须是byte类型
    while True:
        data = sock.recv(1024)
        time.sleep(1)
        if not data or data == b'exit':
            break
        sock.send(f'Hello, {data}!'.encode())  # 如何需要发送多种类型的数据,可考虑用struct.pack struct.unpack
    sock.close()
    print('Connection from {}:{} closed.'.format(*addr))


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # AF_INET指定使用IPv4协议,SOCK_STREAM指定使用面向流的TCP协议
    server.bind(('127.0.0.1', 9999))  # 监听端口,0.0.0.0表示绑定到所有的网络地址
    server.listen(5)  # 调用listen()方法开始监听端口,传入的参数指定等待连接的最大数量
    with ThreadPoolExecutor(10) as executor:  # 每个连接用线程处理,否则在处理连接过程中无法接受其他客户端连接
        while True:
            sock, addr = server.accept()  # 等待并返回一个客户端的连接
            executor.submit(tcp_link, sock, addr)


if __name__ == "__main__":
    main()
