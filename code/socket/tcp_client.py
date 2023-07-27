import socket


def start_client():
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 套接字对象可以处于阻塞、非阻塞或超时模式之一,默认阻塞模式
    client_sock.settimeout(1)
    client_sock.connect(('127.0.0.1', 9999))  # 参数类型是tuple
    client_sock.settimeout(2)
    print(client_sock.recv(1024))  # 接收欢迎消息
    for data in [b'Michael', b'Tracy', b'Sarah']:
        client_sock.sendall(data)  # send不保证一次发送所有数据,需要用户判断并不断尝试
        print(client_sock.recv(1024))  # 一次最多接收指定的字节数

    with client_sock.makefile('rw') as f:
        for data in ['Michael', 'Tracy', 'Sarah']:
            f.write(data + '\n')
            f.flush()  # 发送数据
            print(f.readline(), end='')  # readline遇到\n才会返回,read(n)会读完n个字节后返回


def http_request():
    # TCP连接创建的是双向通道,双方都可以同时给对方发数据,但是谁先发谁后发,怎么协调,要根据具体的协议来决定
    # 例如HTTP协议规定客户端必须先发请求给服务器,服务器收到后才发数据给客户端
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('www.sina.com.cn', 80))
    client.sendall(b'GET / HTTP/1.1\r\nHost: www.sina.com.cn\r\nConnection: close\r\n\r\n')
    buffer = []
    while True:  # 接收数据
        d = client.recv(512)
        if d:
            buffer.append(d)
        else:
            break

    client.close()
    data = b''.join(buffer)
    header, html = data.split(b'\r\n\r\n', 1)
    print(header.decode())
    print(html.decode())


if __name__ == "__main__":
    # start_client()
    http_request()
