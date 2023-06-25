import gc
import os
import sys
import time
import weakref
from multiprocessing import Process

import objgraph

'''
引用计数+1情况
对象被创建,例如a=23
对象被引用,例如b=a
对象作为参数传入到一个函数中,例如func(a)
对象作为一个元素存储在容器中,例如list1=[a]

引用计数-1情况
对象的别名被显式销毁,例如del a
对象的别名被赋予新的对象,例如a=24
对象离开它的作用域.例如func函数执行完毕时,func函数中的局部变量(全局变量不会)
对象所在的容器被销毁,或从容器中删除对象

atexit
被注册的函数会在解释器正常终止时执行.atexit会按照注册顺序的逆序执行; 如果你注册了A, B 和 C, 那么在解释器终止时会依序执行C, B, A.
通过该模块注册的函数, 在程序被未被Python捕获的信号杀死时并不会执行, 在检测到Python内部致命错误以及调用了os._exit()时也不会执行.

循环引用例子:
arr = [1]
arr.append(arr)
x=[]
y=[]
x.append(y)
y.append(x)
只有容器对象才会产生循环引用,比如列表、字典、用户自定义类的对象、元组等,而像数字,字符串这类简单类型不会出现循环引用

垃圾回收包含引用计数,标记清除(可解决循环引用)和分代回收
gc.disable()仅仅关闭垃圾回收功能,对象仍可能会因为引用计数为0而被销毁
gc.get_threshold()返回(700,10,10),当分配对象的个数达到700时,进行一次0代回收; 当进行10次0代回收后触发一次1代回收; 当进行10次1代回收后触发一次2代回收
gc.get_count()Return a three-tuple of the current collection counts,与get_threshold返回值相对应
gc.collect()手动执行垃圾回收,返回不可达(unreachable objects)对象的数目,循环引用无法通过引用计数法消除
gc.get_objects()Returns a list of all objects tracked by the collector, 不包括返回的列表
对象被销毁(引用计数为0)时如果自定义了__del__,会执行__del__函数,然后销毁对象
内存泄漏仅仅存在于某个进程中,无法进程间传递(即gc.get_objects仅仅统计所在进程的对象),会随着进程的结束而释放内存
'''


class Gc:
    def __init__(self):
        self.data = list(range(10000))
        self.next = None


def circular_reference_to_leak():
    a = Gc()
    b = Gc()
    a.next = b  # a.next = weakref.ref(b),解决循环引用嗯题
    b.next = a  # b.next = weakref.ref(a),解决循环引用嗯题


def default_parameter_to_leak(idx, _cache={}):
    _cache[idx] = {Gc()}  # a very explicit and easy-to-find "leak" but oh well
    _ = Gc()  # this one doesn't leak
    print("in default_parameter_to_leak", objgraph.count('Gc'))


def generator_to_leak():
    cnt = 0
    _ = [Gc() for _ in range(10)]
    while True:
        yield cnt
        cnt += 1


def test_ref():
    """
    弱引用不增加引用计数,当对像的引用只剩弱引用时, garbage collection可以销毁对象并将其内存重用于其他内容
    弱引用的主要用途是实现保存大对象的高速缓存或映射, 并希望大对象仅仅因为它出现在高速缓存或映射中而保持存活;还能解决循环引用
    WeakKeyDictionary 弱引用键的映射类, 当不再有对键的强引用时字典中的条目将被丢弃
    WeakValueDictionary 弱引用值的映射类, 当不再存在对该值的强引用时, 字典中的条目将被丢弃
    WeakSet 保持对其元素弱引用的集合类, 当不再有对某个元素的强引用时元素将被丢弃
    """
    a = Gc()
    c = weakref.ref(a)
    _a = c()  # 相当与给a增加了一个引用计数,一般不建议这么使用
    print(a, _a, c)
    print(sys.getrefcount(a))  # 3, 返回的计数通常比预期高1,因为它包含引用作为getrefcount参数
    print(sys.getrefcount(_a))  # 3
    print(sys.getrefcount(c))  # 2
    print(weakref.getweakrefs(a), weakref.getweakrefcount(a))  # [<weakref at 0x10dace660; to 'Gc' at 0x10d8862d0>] 1
    del a, _a
    print(c())  # None,建议使用前先判断是否为None


def test_cache():
    """
    为避免重复创建和销毁一些常见对象,会维护一个缓存池,里面包含如-5,-4,...257,字符等常见对象,用户定义的字符串,数字等不可变类型,也会被加入到缓存池
    当再有其他变量需要用到缓存池内对象时,直接指向即可,即地址不变,当变量值发生改变时才会重新创建对象
    用户定义的数组,字典等可变类型,当引用计数为0被销毁时,如果free_list未满会被加入其中,当用户再定义一个类型相同的对象时直接从free_list选地址赋值即可,即地址不变
    """
    immutable_val = "1314520."
    print(id(immutable_val))
    del immutable_val
    immutable_val1 = "1314520."
    immutable_val2 = "1314520."
    print(id(immutable_val1), id(immutable_val2))  # 4405645168 4405645168

    mutable_val = {1}
    print(id(mutable_val))  # 4368865856
    del mutable_val
    mutable_val1 = {2}
    mutable_val2 = {2}
    print(id(mutable_val1), id(mutable_val2))  # 4368865856 4366383040


def test_circular_reference():
    for idx in range(40):
        time.sleep(1)
        circular_reference_to_leak()
        if idx == 20:
            print(gc.collect())
        print(os.getpid(), objgraph.count('Gc'), gc.get_count())


def test_multiprocess_circular_reference():
    processes = [Process(target=test_circular_reference) for _ in range(3)]
    for process in processes:
        process.start()
    for idx in range(100):
        print("in main", objgraph.count('Gc'))
        time.sleep(.5)


def test_default_parameter():
    objgraph.show_growth(limit=2)  # 调用函数之前We take a snapshot of all the objects counts that are alive
    for idx in range(10):
        default_parameter_to_leak(idx)
        print("in test_default_parameter", objgraph.count('Gc'))
        objgraph.show_growth()


def test_generator():
    it = generator_to_leak()
    next(it)
    print(objgraph.count("Gc"))


class ObjGraph:
    # https://github.com/mgedmin/objgraph/blob/master/objgraph.py
    @staticmethod
    def type_stats():
        """
        Count the number of instances for each type tracked by the GC.
        Note that classes with the same name but defined in different modules will be lumped together if shortnames is True.
        The Python garbage collector does not track simple objects like int or str.
        See https://docs.python.org/3/library/gc.html#gc.is_tracked
        """
        objects = gc.get_objects()
        try:
            stats = {}
            for obj in objects:
                name = type(obj).__name__
                stats[name] = stats.get(name, 0) + 1
            return stats
        finally:
            del objects  # clear cyclic references to frame

    @staticmethod
    def show_most_common_types(limit=10):
        stats = sorted(ObjGraph.type_stats().items(), key=lambda item: item[1], reverse=True)
        if limit:
            stats = stats[:limit]
        width = max(len(name) for name, count in stats)
        for name, count in stats:
            sys.stdout.write('%-*s %i\n' % (width, name, count))

    @staticmethod
    def show_growth(limit=10, peak_stats={}):
        """
        Show the increase in peak object counts since last call.
        peak_stats, a dictionary from type names to previously seen peak object counts.
        Usually you don't need to pay attention to this argument.
        """
        gc.collect()  # 手动执行垃圾回收,避免循环引用干扰
        stats = ObjGraph.type_stats()
        deltas = {}
        for name, count in stats.items():
            old_count = peak_stats.get(name, 0)
            if count > old_count:
                deltas[name] = count - old_count
                peak_stats[name] = count
        deltas = sorted(deltas.items(), key=lambda item: item[1], reverse=True)
        if limit:
            deltas = deltas[:limit]
        result = [(name, stats[name], delta) for name, delta in deltas]
        if result:
            width = max(len(name) for name, _, _ in result)
            for name, count, delta in result:
                sys.stdout.write('%-*s%9d %+9d\n' % (width, name, count, delta))


if __name__ == '__main__':
    # test_ref()
    # test_cache()
    # test_circular_reference()
    # test_multiprocess_circular_reference()
    # test_default_parameter()
    test_generator()
