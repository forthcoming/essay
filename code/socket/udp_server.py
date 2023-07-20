import socket

server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # SOCK_DGRAM指定了这个Socket的类型是UDP
server_sock.bind(('127.0.0.1', 9999))  # 不需要调用listen方法,直接接收来自任何客户端数据,服务器绑定UDP端口和TCP端口可以是同一个如9999
while True:  # 接收数据
    data, addr = server_sock.recvfrom(1024)  # 返回数据和客户端的地址与端口,服务器收到数据后,直接调用sendto()就可以把数据发给客户端
    print('Received from {}:{}'.format(*addr))
    server_sock.sendto(f'Hello, {data.decode()}!'.encode(), addr)  # 多个客户端通过addr区分
