import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 9999))

print(client.recv(1024))  # 接收欢迎消息
for data in [b'Michael', b'Tracy', b'Sarah']:
    client.send(data)
    print(client.recv(1024))
client.send(b'exit')
client.close()
