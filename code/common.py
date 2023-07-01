import re
import time
from collections import deque
from collections.abc import Iterable
from inspect import getgeneratorstate
from multiprocessing import Process, Pipe


def test_generator_state():
    # send: Resumes the generator and "sends" a value that becomes the result of the current yield-expression
    # next: next等价于send(None),生成器一开始只能send(None)
    def gen(a):
        print(f'start a={a}')
        b = yield a
        print(f'received b={b}')
        getgeneratorstate(coro)  # GEN_RUNNING
        c = yield a + b
        print(f'received c={c}')

    coro = gen(14)

    print(getgeneratorstate(coro))  # GEN_CREATED
    print(next(coro))
    # start a=14
    # 14

    print(getgeneratorstate(coro))  # GEN_SUSPENDED,该状态会出现很多次
    print(coro.send(28))
    # received b=28
    # 42

    try:
        coro.send(99)  # received c=99
    except StopIteration:
        pass
    print(getgeneratorstate(coro))  # GEN_CLOSED


def test_yield_from():
    # yield from(后面接任意可迭代对象,类似与await,可用于简化for循环中的yield表达式,自动捕获迭代器异常,得到返回值)
    # 子生成器
    def averager():
        total = .0
        average = count = 0
        while True:
            term = yield
            if term is None:
                break
            total += term
            count += 1
            average = total / count
        return count, average

    # 委派生成器
    def grouper(results, key):
        while True:
            results[key] = yield from averager()

    # 客户端代码（调用方）
    def main(data):
        results = {}
        for key, values in data.items():
            group = grouper(results, key)  # 仅生成<class 'generator'>,其他什么也不做,每次迭代会新建一个averager实例和grouper实例
            next(group)  # 程序执行到term=yield的yield那里
            for value in values:
                group.send(value)
            group.send(None)  # 重要
        print(results)

    data = {
        'girl': [1, 3, 2, 4],
        'boy': [4, 4, 3],
    }
    main(data)  # # {'girl': (count=4, average=2.5), 'boy': (count=3, average=3.6666666666666665)}


def test_flatten():
    def flatten(items, ignore_types=(str, bytes)):
        for x in items:
            if isinstance(x, Iterable) and not isinstance(x, ignore_types):
                yield from flatten(x)
                # for y in flatten(x):
                #     yield y
            else:
                yield x

    for x in flatten([2, [3, [5, 6, 'avatar'], 7], 8]):
        print(x)


def dec2bin(string, precision=10):  # dec2bin('19.625') => 10011.101
    result = deque()
    integer, decimal = re.match(r'(\d*)(\.?\d*)', string).groups()
    integer, decimal = int(integer or 0), float(decimal or 0)
    while integer:
        result.appendleft(str(integer & 1))
        integer >>= 1
    if decimal:
        result.append('.')
    while precision and decimal:
        decimal *= 2
        if decimal >= 1:
            result.append('1')
            decimal -= 1
        else:
            result.append('0')
        precision -= 1
    return ''.join(result)


def test_win32():
    import win32api
    import win32con
    x, y = 120, 240
    win32api.SetCursorPos((x, y))  # 鼠标定位,不同的屏幕分辨率请用百分比换算
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)  # 鼠标左键按下
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)  # 鼠标左键弹起


def test_pipe(conn):
    time.sleep(3)
    conn.send([42, None, 'hello'])
    conn.close()


def pipe_tutorial():
    """
    returns a pair of connection objects connected by a pipe which by default is duplex (two-way).
    Each connection object has send() and recv() methods (among others). Note that data in a pipe may become corrupted
    if two processes (or threads) try to read from or write to the same end of the pipe at the same time.
    Of course there is no risk of corruption from processes using different ends of the pipe at the same time.
    """
    parent_conn, child_conn = Pipe(False)  # parent_conn只读,child_conn只写
    # parent_conn, child_conn = Pipe(True)  # parent_conn和child_conn可以读写,默认为True
    p = Process(target=test_pipe, args=(child_conn,))
    p.start()
    '''
    返回值bool类型,whether there is any data available to be read.
    If timeout is not specified then it will return immediately.
    If timeout is a number then this specifies the maximum time in seconds to block.
    If timeout is None then an infinite timeout is used.
    '''
    parent_conn.poll(timeout=1)
    print(parent_conn.recv())  # [42, None, 'hello'], Blocks until there is something to receive.
    p.join()


if __name__ == '__main__':
    # test_yield_from()
    pipe_tutorial()
