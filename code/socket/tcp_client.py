import socket


def tcp_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('127.0.0.1', 9999))
    print(client.recv(1024))  # 接收欢迎消息
    for data in [b'Michael', b'Tracy', b'Sarah']:
        client.send(data)
        print(client.recv(1024))
    client.send(b'exit')
    client.close()


def http_request():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # AF_INET指定使用IPv4协议,SOCK_STREAM指定使用面向流的TCP协议
    client.connect(('www.sina.com.cn', 80))  # 参数类型是tuple

    # TCP连接创建的是双向通道,双方都可以同时给对方发数据,但是谁先发谁后发,怎么协调,要根据具体的协议来决定
    # 例如HTTP协议规定客户端必须先发请求给服务器,服务器收到后才发数据给客户端

    client.send(b'GET / HTTP/1.1\r\nHost: www.sina.com.cn\r\nConnection: close\r\n\r\n')

    buffer = []
    while True:  # 接收数据
        d = client.recv(512)  # 一次最多接收指定的字节数
        if d:
            buffer.append(d)
        else:
            break

    client.close()  # 关闭连接
    data = b''.join(buffer)
    header, html = data.split(b'\r\n\r\n', 1)
    print(header.decode())
    print(html.decode())


if __name__ == "__main__":
    tcp_client()
