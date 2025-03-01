import re
import time
from collections import deque
from collections.abc import Iterable
from inspect import getgeneratorstate
from multiprocessing import Process, Value


# 记录一些不是那么重要的用例

def run_subroutine(subroutines):
    for subroutine in subroutines:
        subroutine.start()
    for subroutine in subroutines:
        subroutine.join()


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


def test_shared_value(share):
    with share.get_lock():
        time.sleep(.001)
        share.value -= 1  # 涉及读写的操作不是原子操作


def shared_value_tutorial():
    """
    multiprocessing.Value(typecode_or_type, *args, lock=True)
    返回从共享内存分配的ctypes对象, 可以通过Value的value属性来访问对象本身
    typecode_or_type确定返回对象的类型是ctypes类型或数组模块使用的单字符类型代码
    如果lock为True(默认值), 则创建一个新的递归锁对象来同步对该值的访问
    如果lock为False, 那么对返回对象的访问将不会自动受到锁的保护, 因此它不一定是“进程安全的”

    multiprocessing.Array(typecode_or_type, size_or_initializer, *, lock=True)
    返回从共享内存分配的ctypes数组,typecode_or_type和锁部分跟Value一样
    如果size_or_initializer是一个整数,那么它决定了数组的长度,并且数组最初将被清零,否则是一个用于初始化数组的序列,其长度决定了数组长度
    """
    shared_value = Value('i', 100)  # 在不需要锁的情况下可以Value('i',100,lock=False)
    processes = [Process(target=test_shared_value, args=(shared_value,)) for _ in range(100)]
    run_subroutine(processes)
    print(shared_value, shared_value.value)  # <Synchronized wrapper for c_int(0)> 0


if __name__ == '__main__':
    test_yield_from()
