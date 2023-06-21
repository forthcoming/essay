from multiprocessing.dummy import Lock


def decorator_a(func):
    print('start in decorator_a')

    def inner_a(*args, **kwargs):
        print('start in inner_a')
        result = func(*args, **kwargs)
        print('end in inner_a')
        return result

    print('end in decorator_a')
    return inner_a


def decorator_b(func):
    print('start in decorator_b')

    def inner_b(*args, **kwargs):
        print('start in inner_b')
        result = func(*args, **kwargs)
        print('end in inner_b')
        return result

    print('end in decorator_b')
    return inner_b


@decorator_b
@decorator_a
def f(x):
    print('start in f')
    return x * 2


f(1)
'''
start in decorator_a        # 装饰时打印
end in decorator_a          # 装饰时打印
start in decorator_b        # 装饰时打印
end in decorator_b          # 装饰时打印
start in inner_b            # 调用时打印
start in inner_a            # 调用时打印
start in f                  # 调用时打印
end in inner_a              # 调用时打印
end in inner_b              # 调用时打印
'''


# 最简单的方式是实例化一个类,然后在其他地方直接导入这个类实例即可实现单例
def singleton(cls):
    _instance = None
    lock = Lock()

    def _singleton(*args, **kwargs):
        nonlocal _instance
        with lock:  # 线程安全单例模式
            if not _instance:
                _instance = cls(*args, **kwargs)
        return _instance

    return _singleton


def singleton_pool(cls):
    _instance_pool = []
    lock = Lock()

    def _singleton(*args, **kwargs):
        with lock:  # 线程安全单例池
            for _args, _kwargs, _instance in _instance_pool:
                if (_args, _kwargs) == (args, kwargs):
                    return _instance
            _instance = cls(*args, **kwargs)
            _instance_pool.append((args, kwargs, _instance))
            return _instance

    return _singleton
