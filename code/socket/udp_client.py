import socket

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # 不需要调用connect(),直接通过sendto()给服务器发数据
for data in [b'Michael', b'Tracy', b'Sarah']:
    client.sendto(data, ('127.0.0.1', 9999))
    print(client.recv(1024))  # 从服务器接收数据仍然调用recv()方法

client.close()
