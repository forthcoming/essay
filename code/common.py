from collections.abc import Iterable
from inspect import getgeneratorstate


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
    def gen():
        yield from 'AB'
        yield from range(3)

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


if __name__ == '__main__':
    test_yield_from()
