import selectors
import socket
from concurrent.futures import ThreadPoolExecutor

"""
计算机硬件主要包含CPU,网卡,内存,磁盘等,内核(系统应用)可以通过驱动操作硬件,用户应用没法直接操作硬件
为了安全系统把寻址空间划分为内核空间和用户空间即不同区域的内存,内存地址的每一个值代表一个字节
linux为了提高效率,会在用户空间和内核空间加入缓冲区
写数据时,把用户缓冲区数据拷贝到内核缓冲区,然后写入设备;读数据时,从设备读取数据到内核缓冲区,然后再拷贝到用户缓冲区
LinuxIO模型分为阻塞IO,非阻塞IO,IO多路复用,信号驱动IO,异步IO,这五种IO模型主要是针对数据等待与拷贝做的不同优化
阻塞、非阻塞、IO复用、信号驱动都是同步IO模型,虽然数据加载到内核缓冲区过程中可能阻塞/不阻塞,但发起操作的系统调用(如read)过程中是被阻塞,需要等待数据拷贝回用户缓冲区
只有异步IO模型才是异步,因为发起异步类的系统调用(如aio_read)后直接返回,直到内核缓冲区中的数据准备好并复制到用户缓冲区后,再通知用户
阻塞IO:读取数据时等待数据到来和把数据从内核空间拷贝到用户空间
非阻塞IO:指数据还未到达网卡,或到达网卡但还没拷贝到内核缓冲区,这个阶段读取数据是非阻塞,数据就绪时依然会阻塞等待数据从内核空间拷贝到用户空间
IO多路复用:分为select,poll,epoll,kqueue等实现
select缺点: 需要将整个fd_set从用户空间拷贝到内核空间,select结束再拷贝回用户空间,且fd_set监听的fd数量不能超过1024
typedef long int __fd_mask;
typedef struct{
    __fd_mask fds_bits[__FD_SETSIZE / __NFDBITS]; // long型数组,长度为1024/32=32,共1024个比特位,每一位代表一个fd,1就绪,0为就绪
    // ...
} fd_set;
int select(  // select函数用于监听多个fd集合
    int nfds,  // 要监听的fd_set的最大fd+1
    fd_set *readfds,  // 监听读事件的fd
    fd_set *writefds,  // 监听写事件的fd
    fd_set *exceptfds,   // 监听异常事件的fd
    struct timeval *timeout // select超时时间,null永不超时,0不阻塞等待,大于0固定等待时间
);  // 有fd准备就绪时,会把fd_set中未就绪的fd比特位置为0,返回就绪的fd个数

poll:与select没有本质区别,也需要将整个pollfd从用户空间拷贝到内核空间,poll结束再拷贝回用户空间,只不过监听的fd数量理论上没有限制了 
#define POLLIN    // 可读事件
#define POLLOUT   // 可写事件
#define POLLERR   // 错误事件
#define POLLNVAL  // fd未打开事件
struct pollfd{
    int fd;   // 监听的fd
    short int events;   // 监听的事件类型,读、写、异常
    short int revents;  // 实际发生的事件类型
}
int poll(
    struct pollfd *fds,  // pollfd数组,可自定义大小
    nfds_t nfds,  // 数组元素个数
    int timeout  // 超时时间
)  // 有fd准备就绪时返回就绪fd数量

epoll:
struct eventpoll{
    struct rb_root rbr; // 一颗红黑树,记录要监听的fd
    struct list_head rdlist;  // 一个链表,记录就绪的fd
    // ...
}
int epoll_create(int size);  // 在内核创建eventpoll结构体,返回对应的句柄epfd
int epoll_ctl( // 将一个fd添加到epoll红黑树中,并设置ep_poll_callback,触发时把对应的fd加入到rdlist这个就绪列表中
    int epfd,   // epoll实例的句柄
    int op,   // 要执行的操作,包括ADD,MOD,DEL
    int fd,   // 要监听的fd
    struct epoll_event *event  // 监听的事件类型,包括读、写、异常等
)
LevelTriggered: 简称LT,默认模式,当fd就绪时,会重复通知多次, 直至数据处理完成
EdgeTriggered: 简称ET,当fd就绪时,只会通知一次, 不管数据是否处理完成
int epoll_wait(  // 检测rdlist列表是否为空,不为空则返回就绪的fd数量
    int epfd,  // epoll实例的句柄
    struct epoll_event *events,  // 空event数组,用于接收就绪的fd
    int maxevents,  // events数组最大长度
    int timeout  // 超时时间,-1永不超时,0不阻塞,大于0固定等待时间
)

异步IO:https://docs.python.org/zh-cn/3.11/library/asyncio-stream.html
在复制内核缓冲区数据到用户缓冲区中时需要CPU参与,这意味着不受阻的socket server会和异步调用函数争用CPU,如果并发量较大,CPU争用情况就越严重

粘包问题是指多个消息被粘在一起,半包问题是指一个消息被拆分成多个部分,解决方案:
1. 定长消息 2. 消息头中包含消息的长度信息 3. 指定结束符如\n

TCP和UDP是两种常用的传输层协议,用于网络数据传输
TCP是面向连接的协议,数据传输前必须先建立连接,提供可靠的数据顺序传输,如网页浏览、文件传输和电子邮件
UDP是无连接的协议,数据传输前不需要建立连接,数据传输不保证顺序和可靠性,使得UDP比TCP更加轻量级和快速
对于某些实时性和速度要求高、同时能容忍少量数据丢失的应用,如实时视频和音频通话、在线游戏等
TCP是全双工,三次握手和四次挥手既可以由客户端发起,也可以由服务端发起

SYN(synchronization): 请求建立连接,三次握手中用到
FIN(finish): 请求关闭连接,对应端口仍处于开放状态,可以接收后续数据,四次挥手中用到
ACK(acknowledgment): 确认接受,三次握手和四次分手中用到

三次握手
1. client首先发送SYN报文和随机产生一个值seq=X给server,此时client进入SYN_SENT状态,等待server端确认
2. server收到client发过来的SYN包后知道client请求建立连接,将产生一个SYN+ACK=X+1包和随机产生的seq=Y发送给client以确认连接请求,此时server进入SYN_RCVD状态
3. client收到server的SYN+ACK包,向server发送确认包ACK=Y+1,此包发送完毕,client和server进入ESTABLISHED(TCP连接成功)状态
第三次握手就是让server确认client可用,避免无效等待,应为第二次握手可能是因为网络延迟某个已关闭的client发出

四次挥手:
1. client发出FIN包请求关闭连接,进入FIN_WAIT_1状态
2. server收到FIN包,发送ACK包,进入CLOSE_WAIT状态,client收到ACK包后进入FIN_WAIT_2状态,此时server还可以发送未发送数据,client还可以接收数据
3. server发送完数据后,发送一个FIN包,进入LAST_ACK状态
4. client收到FIN包后,发送ACK包,进入TIME_WAIT状态,超时等待(一般为1min)结束后关闭连接,server收到ACK包后进入CLOSED状态,关闭连接
TIME_WAIT是为了保证server能收到ACK包,如果没收到,server会重发送FIN包,处于TIME_WAIT的的client收到FIN包后再次发送ACK包并刷新TIME_WAIT时间
大量TIME_WAIT会占用内存和端口资源,HTTP使用短连接或HTTP长连接数量达到上限会出现这种情况,可通过调整等待时间,SO_REUSEADDR端口复用,短连接改长连接等方式解决
握手其实是四个阶段,只不过第2,3阶段合并成2阶段,挥手2阶段后服务端可能还会发送数据,所以不能合并

TCP如何保证安全有效传输?
1. 三次握手+四次挥手
2. 发送报文包含[序列号,长度,数据内容],服务端收到数据后回复确认ACK=序列号+长度=下一个包起始序列号
3. 当报文发出后在一定时间内未收到接收方确认,发送方就会进行重传,当接收方收到重复数据(通过序列号)时就将其丢掉,重新发送ACK
4. 每个报文段都会添加一个头部校验和(参见checksum),发送方和接收方验证校验和是否相同,以检测数据在传输过程中是否损坏或者被篡改,校验不过会进行重传
"""


class BlockingIO:  # 阻塞IO
    def __init__(self, ip='127.0.0.1', port=9999):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # AF_INET指使用IPv4协议,SOCK_STREAM指使用TCP协议
        # SO_REUSEADDR标志告诉内核将处于TIME_WAIT状态的本地套接字重新使用,而不必等到固有的超时到期
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind((ip, port))  # 监听端口,0.0.0.0表示绑定到所有的网络地址
        self.server_sock.listen(5)  # 调用listen()方法开始监听端口,传入的参数指定等待连接的最大数量

    @staticmethod
    def tcp_link(client_sock, addr):  # 这是个长连接,服务端一般可以通过接收的数据某个字段判断
        print('Accept new connection from {}:{}...'.format(*addr))
        client_sock.sendall(b'Welcome!')  # 必须是byte类型
        while True:  # 新建一个与客户端关联的socket,再接收和发送数据
            """
            浏览器可以通过http://127.0.0.1:9999/hello方式访问服务器,接收到的数据大致如下(与RESP2.0一样以\r\n作为一行结束标志)
            b'''GET /hello HTTP/1.1\r\nHost: localhost:9999\r\nConnection: keep-alive\r\nCache-Control: max-age=0\r\n
            Upgrade-Insecure-Requests: 1\r\nUser-Agent: Mozilla/5.0\r\nAccept: text/html\r\n
            Accept-Encoding: gzip, deflate, br\r\nAccept-Language: zh-CN,zh;q=0.9\r\n\r\n'''
            """
            data = client_sock.recv(1024)
            if data:
                # time.sleep(1.8)  # 测试客户端socket超时
                client_sock.sendall(f'Hello, {data.decode()}'.encode())  # 如果需要发送多种类型的数据,可考虑用struct.pack
            else:
                client_sock.close()
                print('Connection from {}:{} closed.'.format(*addr))
                break

    def start(self):
        # 每个阻塞fd用线程处理,也可以只用一个线程循环遍历所有的非阻塞fd,模拟IO多路复用,但应为不断执行系统调用(空间切换)效率慢
        with ThreadPoolExecutor(10) as executor:
            while True:
                client_sock, addr = self.server_sock.accept()  # 等待并返回一个客户端的连接
                executor.submit(self.__class__.tcp_link, client_sock, addr)


class IOMultiplexing:  # IO多路复用
    def __init__(self, ip="127.0.0.1", port=9999):
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind((ip, port))
        server_sock.listen(5)
        server_sock.setblocking(False)  # 创建一个非阻塞的TCP套接字
        # 选择最佳实现, epoll|kqueue|devpoll > poll > select, macOS下为kqueue,Linux下为epoll
        self.selector = selectors.DefaultSelector()  # 相当于epoll_create
        # 相当于epoll_ctl的EPOLL_CTL_ADD模式,让accept关联server
        self.selector.register(server_sock, selectors.EVENT_READ, self.accept)  # 此处的EVENT_READ和EVENT_WRITE什么区别

    def start(self):
        while True:
            ready = self.selector.select()  # 相当于epoll_wait,等待已注册文件对象准备就绪或超时到期
            for selector_key, events in ready:  # events就是register时指定的EVENT_READ或EVENT_WRITE
                callback = selector_key.data
                callback(selector_key.fileobj)  # 调用相应的回调函数处理事件

    def accept(self, server_sock):  # 回调函数,用于处理新连接的客户端套接字
        client_sock, addr = server_sock.accept()
        print(f"Accepted connection from {addr}")
        client_sock.setblocking(False)
        client_sock.sendall(b'Welcome!')
        self.selector.register(client_sock, selectors.EVENT_READ, self.read)

    def read(self, client_sock):  # 回调函数,用于处理客户端套接字的写事件
        data = client_sock.recv(1024)
        if data:
            print(f"Received data from {client_sock.getpeername()}")
            client_sock.sendall(f'Hello, {data.decode()}'.encode())  # 回显数据给客户端
        else:  # client断开连接时会执行
            print("connection closed")
            self.selector.unregister(client_sock)  # 取消selector上的注册,相当于epoll_ctl的EPOLL_CTL_DEL模式
            client_sock.close()


def checksum(data):
    length = len(data)
    if length & 1:
        data += b'\x00'  # Pad with zero if the length is odd,填充字节只是为了计算校验和,不用传送
    total = 0
    for i in range(0, length, 2):
        total += data[i] << 8 | data[i + 1]
        if total > 0xFFFF:
            total = (total & 0xFFFF) + 1
    return ~total & 0xFFFF


if __name__ == "__main__":
    # blocking_io = BlockingIO()
    # blocking_io.start()

    # io_multiplexing = IOMultiplexing()
    # io_multiplexing.start()

    tcp_header_and_data = b'\x45\x00\x00\x28\x00\x00\x40\x00\x40\x06\x00\x00\xc0\xa8\x01\x01\xc0\xa8\x01\x02\x14'
    print("Calculated Checksum:", checksum(tcp_header_and_data))
