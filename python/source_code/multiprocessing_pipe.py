import io
import os
import pickle
import selectors
import socket
import struct
import time


# 仅包含unix代码实现部分,参考python3.11的multiprocessing.Pipe

class Connection:
    def __init__(self, handle, readable=True, writable=True):
        assert readable or writable, "at least one of `readable` and `writable` must be True"
        self._handle = handle.__index__()  # file_no,与socket句柄关联,如果是None表示已经关闭了,小与0则非法
        self._readable = readable
        self._writable = writable

    def _send(self, buf):
        remaining = len(buf)
        while True:
            n = os.write(self._handle, buf)  # file descriptor (Unix only),windows用的是socket
            remaining -= n
            if remaining == 0:
                break
            buf = buf[n:]

    def _send_bytes(self, buf):
        n = len(buf)
        if n > 0x7fffffff:
            pre_header = struct.pack("!i", -1)
            header = struct.pack("!Q", n)
            self._send(pre_header)
            self._send(header)
            self._send(buf)
        else:
            header = struct.pack("!i", n)
            # Issue #20540: concatenate before sending, to avoid delays due to Nagle's algorithm on a TCP socket.
            # Also note we want to avoid sending a 0-length buffer separately,
            # to avoid "broken pipe" errors if the other end closed the pipe.
            self._send(header + buf)

    def send_bytes(self, buf, offset=0, size=None):
        assert self._handle is not None and self._writable
        m = memoryview(buf)
        if m.itemsize > 1:
            m = m.cast('B')
        n = m.nbytes
        if size is None:
            size = n - offset
        assert 0 <= offset <= n
        assert 0 <= size <= n - offset
        self._send_bytes(m[offset:offset + size])  # Send the bytes data from a bytes-like object

    def send(self, obj):
        assert self._handle is not None and self._writable
        self._send_bytes(pickle.dumps(obj))  # Send a picklable object

    def _recv(self, size):
        buf = io.BytesIO()
        handle = self._handle  # why??
        remaining = size
        while remaining > 0:
            chunk = os.read(handle, remaining)
            n = len(chunk)
            if n == 0:
                if remaining == size:
                    raise EOFError
                else:
                    raise OSError("got end of file during message")
            buf.write(chunk)
            remaining -= n
        return buf

    def _recv_bytes(self, maxsize=None):
        buf = self._recv(4)
        size, = struct.unpack("!i", buf.getvalue())
        if size == -1:
            buf = self._recv(8)
            size, = struct.unpack("!Q", buf.getvalue())
        if maxsize is not None and size > maxsize:
            return None
        return self._recv(size)

    def recv_bytes(self, max_length=None):
        assert self._handle is not None and self._readable
        assert max_length >= 0
        buf = self._recv_bytes(max_length)  # Receive bytes data as a bytes object.
        assert buf is not None, "bad message length"
        return buf.getvalue()

    def recv(self):
        assert self._handle is not None and self._readable
        buf = self._recv_bytes()
        return pickle.loads(buf.getbuffer())

    def recv_bytes_into(self, buf, offset=0):
        # Receive bytes data into a writeable bytes-like object.Return the number of bytes read.
        assert self._handle is not None and self._readable
        with memoryview(buf) as m:
            item_size = m.itemsize  # 获取任意缓冲区的字节大小
            bytesize = item_size * len(m)
            result = self._recv_bytes()
            size = result.tell()
            assert 0 <= offset <= bytesize and bytesize >= offset + size
            result.seek(0)
            result.readinto(m[offset // item_size:(offset + size) // item_size])
            return size

    def poll(self, timeout=.0):  # Whether there is any input available to be read
        """
        poll/select优点是不需要任何额外的文件描述符,与epoll/kqueue相反(而且它们需要单个系统调用)
        Wait till an object in object_list is ready/readable.Returns them which are ready/readable.
        """
        assert self._handle is not None and self._readable
        with selectors.PollSelector() as selector:  # 也可以是selectors.SelectSelector
            for obj in [self]:
                selector.register(obj, selectors.EVENT_READ)
            if timeout is not None:
                deadline = time.monotonic() + timeout
            while True:
                ready = selector.select(timeout)
                if ready:
                    r = [key.fileobj for (key, events) in ready]
                    return bool(r)
                else:
                    if timeout is not None:
                        timeout = deadline - time.monotonic()
                        if timeout < 0:
                            return bool(ready)

    def __del__(self):
        if self._handle is not None:
            os.close(self._handle)

    def close(self):  # Close the connection
        if self._handle is not None:
            try:
                os.close(self._handle)
            finally:
                self._handle = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()


def Pipe(duplex=True):
    if duplex:
        s1, s2 = socket.socketpair()
        """
        socketpair相当于下面三句,是UDS
        a, b = _socket.socketpair(AF_UNIX, SOCK_STREAM, 0)
        a = socket.socket(AF_UNIX, SOCK_STREAM, 0, a.detach())
        b = socket.socket(AF_UNIX, SOCK_STREAM, 0, b.detach())
        """
        s1.setblocking(True)
        s2.setblocking(True)
        c1 = Connection(s1.detach())
        c2 = Connection(s2.detach())
    else:
        fd1, fd2 = os.pipe()
        c1 = Connection(fd1, writable=False)
        c2 = Connection(fd2, readable=False)
    return c1, c2
