########################################################################################################################
# TCPServer
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
        sock.send(
            'Hello, {}!'.format(data).encode('utf-8'))  # encode成bytes类型,如何需要发送多种类型的数据,可考虑用struct.pack struct.unpack
    sock.close()
    print('Connection from {}:{} closed.'.format(*addr))


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('127.0.0.1', 9999))  # 监听端口,0.0.0.0表示绑定到所有的网络地址
server.listen(5)  # 调用listen()方法开始监听端口,传入的参数指定等待连接的最大数量

while True:  # 服务器程序通过一个永久循环来接受来自客户端的连接,accept()会等待并返回一个客户端的连接
    # 接受一个新连接:
    sock, addr = server.accept()  # 每个连接都必须创建新线程(或进程)来处理,否则单线程在处理连接的过程中,无法接受其他客户端的连接
    # 创建新线程来处理TCP连接:
    t = threading.Thread(target=tcp_link, args=(sock, addr))
    t.start()

########################################################################################################################
# TCPClient
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 9999))

print(client.recv(1024))  # 接收欢迎消息
for data in [b'Michael', b'Tracy', b'Sarah']:
    client.send(data)
    print(client.recv(1024))
client.send(b'exit')
client.close()

########################################################################################################################
# UDPServer
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # SOCK_DGRAM指定了这个Socket的类型是UDP
server.bind(('127.0.0.1', 9999))  # 不需要调用listen()方法,直接接收来自任何客户端的数据
while True:
    # 接收数据:
    data, addr = server.recvfrom(1024)  # 返回数据和客户端的地址与端口,服务器收到数据后,直接调用sendto()就可以把数据用UDP发给客户端
    print('Received from {}:{}.'.format(*addr))
    server.sendto('Hello, {}!'.format(data).encode('utf-8'), addr)

########################################################################################################################
# UDPClient
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # 不需要调用connect(),直接通过sendto()给服务器发数据
for data in [b'Michael', b'Tracy', b'Sarah']:
    client.sendto(data, ('127.0.0.1', 9999))
    print(client.recv(1024))  # 从服务器接收数据仍然调用recv()方法

client.close()
# 服务器绑定UDP端口和TCP端口互不冲突,也就是说,UDP的9999端口与TCP的9999端口可以各自绑定

########################################################################################################################
# HTTP请求
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # AF_INET指定使用IPv4协议,SOCK_STREAM指定使用面向流的TCP协议
client.connect(('www.sina.com.cn', 80))  # 参数类型是tuple

# TCP连接创建的是双向通道,双方都可以同时给对方发数据,但是谁先发谁后发,怎么协调,要根据具体的协议来决定
# 例如HTTP协议规定客户端必须先发请求给服务器,服务器收到后才发数据给客户端

client.send(b'GET / HTTP/1.1\r\nHost: www.sina.com.cn\r\nConnection: close\r\n\r\n')

# 接收数据:
buffer = []
while True:
    # 每次最多接收1k字节:
    d = client.recv(1024)  # 一次最多接收指定的字节数
    if d:
        buffer.append(d)
    else:
        break

client.close()  # 关闭连接
data = b''.join(buffer)
header, html = data.split(b'\r\n\r\n', 1)
print(header)
# 把接收的数据写入文件:
with open('sina.html', 'wb') as f:
    f.write(html)
