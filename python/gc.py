# -*- coding: utf-8 -*-
from multiprocessing import Process
import objgraph,gc,time,sys,os,weakref


'''
引用计数+1情况
对象被创建,例如a=23
对象被引用,例如b=a
对象作为参数传入到一个函数中,例如func(a)
对象作为一个元素存储在容器中,例如list1=[a]

引用计数-1情况
对象的别名被显式销毁,例如del a
对象的别名被赋予新的对象,例如a=24
一个对象离开它的作用域.例如func函数执行完毕时,func函数中的局部变量(全局变量不会)
对象所在的容器被销毁,或从容器中删除对象

atexit
被注册的函数会在解释器正常终止时执行.atexit会按照注册顺序的逆序执行; 如果你注册了 A, B 和 C, 那么在解释器终止时会依序执行 C, B, A.
通过该模块注册的函数, 在程序被未被Python捕获的信号杀死时并不会执行, 在检测到Python内部致命错误以及调用了os._exit()时也不会执行.

内存泄漏仅仅存在于某个进程中,无法进程间传递(即gc.get_objects仅仅统计所在进程的对象),会随着进程的结束而释放内存
The del statement does not necessarily call __del__() – it simply decrements the object’s reference count, and if this reaches zero __del__() is called.
gc.disable()仅仅关闭垃圾回收功能,对象仍可能会因为引用计数为0而被销毁
当对像的引用只剩弱引用时, garbage collection可以销毁引用并将其内存重用于其他内容, 弱引用不增加引用计数
弱引用的主要用途是实现保存大对象的高速缓存或映射, 但又并希望大对象仅仅因为它出现在高速缓存或映射中而保持存活;还能避免循环引用
从Python3.4 开始, __del__() 方法不会再阻止循环引用被作为垃圾回收, 并且模块全局变量在interpreter shutdown 期间不会被强制设为None

WeakKeyDictionary
弱引用键的映射类, 当不再有对键的强引用时字典中的条目将被丢弃,这可被用来将额外数据关联到一个应用中其他部分所拥有的对象而无需在那些对象中添加属性
WeakValueDictionary
弱引用值的映射类, 当不再存在对该值的强引用时, 字典中的条目将被丢弃
WeakSet
保持对其元素弱引用的集合类, 当不再有对某个元素的强引用时元素将被丢弃
'''

class OBJ:
    def __init__(self):
        self.data = list(range(10000))
        self.next = None

class MyBigFatObject:
    pass

def computate_something(idx,_cache={}):
    _cache[idx] = {'foo':MyBigFatObject()}  # a very explicit and easy-to-find "leak" but oh well
    x = MyBigFatObject()                    # this one doesn't leak

def func_to_leak():
    a = OBJ()
    b = OBJ()
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
            print(gc.collect())   # 手动执行垃圾回收,返回不可达(unreachable objects)对象的数目,循环引用需要垃圾回收,无法通过引用计数法消除
        print(os.getpid(),objgraph.count('OBJ'),gc.get_count())

def main1():
    processes = [Process(target=main0) for _ in range(4)]
    for process in processes:
        process.start()
    for idx in range(100):
        print(objgraph.count('OBJ'))
        time.sleep(.5)

def main2():
    objgraph.show_growth(limit=3)  # We take a snapshot of all the objects counts that are alive before we call our function
    for idx in range(10):
        computate_something(idx)
        objgraph.show_growth()

def main3():
    a = OBJ()
    b = weakref.proxy(a)
    print(a,b,type(a),type(b))
    print(sys.getrefcount(a))
    print(sys.getrefcount(b))
    print(weakref.getweakrefs(a),weakref.getweakrefcount(a))
    print(b is a)  # False
    del a
    # print(b) # ReferenceError: weakly-referenced object no longer exists

    a = OBJ()
    c = weakref.ref(a)
    _c = c()
    print(c)
    print(_c is a)
    del a,_c
    print(c)

if __name__ == '__main__':
    main0()
    # main1()
    # main2()
    # main3()


