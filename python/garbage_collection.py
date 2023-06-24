# -*- coding: utf-8 -*-
import gc
import objgraph
import os
import sys
import time
import weakref
from multiprocessing import Process

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
对象被销毁(引用计数为0)时如果自定义了__del__,会执行__del__函数,然后销毁对象
内存泄漏仅仅存在于某个进程中,无法进程间传递(即gc.get_objects仅仅统计所在进程的对象),会随着进程的结束而释放内存
'''


class Gc:
    def __init__(self):
        self.data = list(range(10000))
        self.next = None


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
    print(sys.getrefcount(a))   # 3, 返回的计数通常比预期高1,因为它包含引用作为getrefcount参数
    print(sys.getrefcount(_a))  # 3
    print(sys.getrefcount(c))   # 2
    print(weakref.getweakrefs(a), weakref.getweakrefcount(a))  # [<weakref at 0x10dace660; to 'OBJ' at 0x10d8862d0>] 1
    del a, _a
    print(c())  # None,建议使用前先判断是否为None


class MyBigFatObject:
    pass


def computate_something(idx, _cache={}):
    _cache[idx] = {'foo': MyBigFatObject()}  # a very explicit and easy-to-find "leak" but oh well
    x = MyBigFatObject()  # this one doesn't leak


def func_to_leak():
    a = Gc()
    b = Gc()
    a.next = b
    b.next = a
    # a.next = weakref.ref(b)
    # b.next = weakref.ref(a)
    # print(sys.getrefcount(b))      # 结果是3,针对的是变量本身,调用getrefcount也会增加一个临时引用
    # print(objgraph.count('OBJ'))   # gc.get_objects针对的类型


def main0():
    for idx in range(40):
        time.sleep(1)
        func_to_leak()
        if idx == 20:
            print(gc.collect())  # 手动执行垃圾回收,返回不可达(unreachable objects)对象的数目,循环引用需要垃圾回收,无法通过引用计数法消除
        print(os.getpid(), objgraph.count('OBJ'), gc.get_count())


def main1():
    processes = [Process(target=main0) for _ in range(4)]
    for process in processes:
        process.start()
    for idx in range(100):
        print(objgraph.count('OBJ'))
        time.sleep(.5)


def main2():
    objgraph.show_growth(
        limit=3)  # We take a snapshot of all the objects counts that are alive before we call our function
    for idx in range(10):
        computate_something(idx)
        objgraph.show_growth()


if __name__ == '__main__':
    # main0()
    # main1()
    # main2()
    test_ref()
