import ctypes
import datetime
import mmap
import multiprocessing as mp
import os
import random
import re
import signal
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from multiprocessing import shared_memory
from multiprocessing.dummy import Lock as ThreadLock, RLock as ThreadRLock
from threading import get_ident, local, Barrier, BrokenBarrierError, BoundedSemaphore, Thread, Condition
from types import SimpleNamespace

"""
atexit
被注册的函数会在解释器正常终止时执行.atexit会按照注册顺序的逆序执行; 如果你注册了A, B 和 C, 那么在解释器终止时会依序执行C, B, A
通过该模块注册的函数, 在程序被未被Python捕获的信号杀死时并不会执行, 在检测到Python内部致命错误以及调用了os._exit()时也不会执行

concurrent(并发) & parallel(并行)
当系统只有一个CPU,则它不可能同时进行一个以上的线程,只能把CPU运行时间划分成若干个时间段
再将时间段分配给各个线程执行,在一个时间段的线程代码运行时,其它线程处于挂起状态.这种方式我们称为并发
当系统有多个CPU时,不同线程可以同时工作在不同的CPU上,这种方式我们称为并行

线程 & 进程
GIL存在于CPython,PyPy解释器中,其他解释器如Jython、IronPython不存在GIL的问题
每个Python进程都有自己的Python解释器和内存空间,因此GIL不会成为问题
对于CPU密集型任务通常使用多进程,进程数不是越大越好,默认进程数等于电脑核数
GIL导致线程是并发运行(即便有多个cpu,线程会在其中一个cpu来回切换),而进程是并行
标准库中所有阻塞型I/O函数都会释放GIL,time.sleep也会释放,因此尽管有GIL,线程还是能在I/O密集型应用中发挥作用
daemon=False: 父线/进程运行完,会接着等子线/进程全部都执行完后才结束
daemon=True: 父进程结束,他会杀死自己的子线/进程使其终止,但父进程被kill -9杀死时子进程不会结束,会被系统托管

进程间通信(进程间数据不共享)
共享内存如shared_memory,mmap
文件系统如Queue & Pipe & Manager, Queue和Manager基于Pipe实现
信号如signal

sys.setswitchinterval(n) # 设置解释器的线程切换间隔(以秒为单位),实际值可能更高,特别是在使用长时间运行的内部函数或方法时
在间隔结束时调度哪个线程是操作系统的决定,解释器没有自己的调度程序
memoryview让你可以直接访问对象的底层内存,而不需要复制数据,可以作用于任何实现了buffer protocol的对象,如bytes,bytearray,array.array等
"""


def run_subroutine(subroutines):
    for subroutine in subroutines:
        # print(subroutine.is_alive())  # False
        subroutine.start()
        # print(subroutine.is_alive())  # True
        # subroutine.terminate()  # 仅用于进程
    for subroutine in subroutines:
        subroutine.join()


def pool_work(second):
    time.sleep(second)
    print(f'I have sleep {second} seconds, ident:{get_ident()}, pid:{os.getpid()}\n')
    return second


def pool_compute(item, thread_lock, set_counter, dict_counter):
    # 1 / (int(time.time()) & 1)  # 线程池中出现错误,程序不会报错,需要手动捕捉异常

    time.sleep(random.uniform(0, .01))
    with thread_lock:  # 必须加锁
        if item in dict_counter:
            time.sleep(random.uniform(0, .01))
            dict_counter[item] += 1
        else:
            time.sleep(random.uniform(0, .01))
            dict_counter[item] = 1

    # with thread_lock:  # 必须加锁(思想类似redis分布式锁)
    #     while True:
    #         if item in set_counter:
    #             time.sleep(.001)
    #         else:
    #             time.sleep(random.uniform(0, .01))
    #             set_counter.add(item)
    #             break
    # if item in dict_counter:
    #     time.sleep(random.uniform(0, .01))
    #     dict_counter[item] += 1
    # else:
    #     time.sleep(random.uniform(0, .01))
    #     dict_counter[item] = 1
    # set_counter.remove(item)


def pool_executor_tutorial():
    """
    ThreadPoolExecutor 和 ProcessPoolExecutor的函数以及行为均一致,唯一不同的是线程和进程区别
    with代码块结束会自动调用executor.shutdown(wait=True),wait=True则对任务进行join操作,因此主程序会等待with代码块所有任务结束
    无论wait的值是多少,整个程序都不会退出,直到所有待处理任务都执行完毕,即daemon=False
    一旦某个任务结束,会立即执行下一个任务,由pool_work总耗时6s可以验证
    如果提交的任务是一样的,就可以简化成map.假如提交的任务不一样,或者执行的过程之可能出现异常(map执行过程中发现问题会直接抛错)就要用到submit
    """
    args = [3, 2, 4]  # 可以是无限任务如生成器或者阻塞式的redis队列,但只要有任务就会被取出来,且会阻塞后一句的执行,建议直接起多进程
    start_time = time.monotonic()
    with ThreadPoolExecutor(2) as executor:
        futures = [executor.submit(pool_work, arg) for arg in args]  # concurrent.futures._base.Future,不阻塞下一行语句的执行
        time.sleep(3.5)  # 已经完成了两个任务
        # 任何在调用as_completed()之前完成的futures将首先被生成
        for future in as_completed(futures, timeout=3):  # 只要有任务完成或取消就返回,timeout秒后如果还有未完成任务抛出TimeoutError异常
            print(future.result(), futures)
    print(f"cost {time.monotonic() - start_time} seconds")  # cost 6.006827116012573 seconds

    start_time = time.monotonic()
    with ProcessPoolExecutor(2) as executor:  # 只创建max_worker=2个进程
        results = executor.map(pool_work, args)  # generator,不阻塞下一行语句的执行
        print(f'the results is {list(results)}')  # 都完成后按任务顺序返回
    print(f"cost {time.monotonic() - start_time} seconds")  # cost 6.156317949295044 seconds

    thread_lock = ThreadLock()
    tasks = [1, 2, 3, 2, 1, 5, 3, 4, 4, 6, 1, 5, 2, 7, 1, 10, 4, 6, 3, 5, 32, 4, 7, 2, 7, 3, 1, 9, 5, 2] * 100
    dict_counter = {}
    set_counter = set()
    with ThreadPoolExecutor(10) as executor:
        futures = [executor.submit(pool_compute, task, thread_lock, set_counter, dict_counter) for task in tasks]
        for future in as_completed(futures):
            print(future)
        # results = executor.map(pool_compute, tasks, [thread_lock] * 3000, [set_counter] * 3000, [dict_counter] * 3000)
        # for result in results:
        #     print(result)
    assert len(tasks) == sum(dict_counter.values())


def interprocess_communication(new_shared):
    new_shared.buf[:5] = b'howdy'
    new_shared.close()


def shared_memory_tutorial():
    """
    作为一种跨进程共享数据的方式,共享内存块的寿命可能超过创建它的原始进程,一个共享内存块可能同时被多个进程使用
    当一个进程不再访问这个共享内存块的时候应该调用close方法; 当一个共享内存块不被任何进程使用时应该调用unlink方法以执行必要的清理
    create指定创建一个新的共享内存块(True)还是连接到已存在的共享内存块(False)
    """
    shared = shared_memory.SharedMemory(create=True, size=10)  # 实际分配内存为4096整倍数
    print(type(shared.buf), shared.size, shared.name)  # <class 'memoryview'> 4096 psm_a7ecc55d
    shared.buf[:4] = bytearray([97, 98, 99, 100])
    shared.buf[4:6] = b"AB"
    print(bytes(shared.buf[:6]), bytearray(shared.buf[:6]))  # b"abcdAB" bytearray(b"abcdAB")

    new_shared = shared_memory.SharedMemory(shared.name)  # Attach to an existing shared memory block
    mp.set_start_method("fork")
    """
    Register callables to be called when forking a new process.
    before: A callable to be called in the parent before the fork().
    after_in_child: A callable to be called in the child after fork().
    after_in_parent: A callable to be called in the parent after fork().
    before callbacks are called in reverse order.after_in_child and after_in_parent callbacks are called in order
    """
    os.register_at_fork(after_in_child=lambda: print(os.getpid()))  # fork方式有效
    process = mp.Process(target=interprocess_communication, args=(new_shared,))
    run_subroutine([process])

    print(shared.buf[:6].tobytes(), shared.buf[:6].tolist())  # b"howdyB" [104, 111, 119, 100, 121, 66]
    shared.close()  # Close each SharedMemory instance
    shared.unlink()  # Call unlink only once to release the shared memory


def shared_mmap_tutorial():
    """
    fileno=-1表示映射匿名内存,也可以是具体的文件句柄,如fileno=open('xxx').fileno(),读写权限要与mmap保持一致
    length表示最大可操作字节数
    向ACCESS_WRITE内存映射赋值会影响内存和底层的文件,向ACCESS_COPY内存映射赋值会影响内存,但不会更新底层的文件
    flags=MAP_PRIVATE创建私有写时复制映射,进程间数据不同步,MAP_SHARED创建一个与映射文件相同区域的所有其他进程共享的映射,默认共享
    共享的仅仅是内存,文件指针等属性不共享
    """
    mm = mmap.mmap(fileno=-1, length=13, flags=mmap.MAP_SHARED)
    mm.write(b"Hello world!")
    mm.seek(0)
    pid = os.fork()
    if pid == 0:  # In a child process
        mm[6:12] = b'python'
        print('child process: ', mm.readline(), mm.tell())  # child process:  b'Hello python\x00' 13
        mm.close()
        os._exit(0)  # 会停止进程,即使有异常处理也会失效
    else:  # In a parent process
        time.sleep(1)  # 让子进程先执行
        print('parent process: ', mm.tell(), mm.readline())  # parent process:  0 b'Hello python\x00'
        mm.close()

    with mmap.mmap(fileno=-1, length=256, access=mmap.ACCESS_COPY) as mm:
        mm.write(b"Hello world!\n")  # 会移动文件指针,如果mmap使用ACCESS_READ创建,则写入会引发TypeError异常
        mm.write(b"welcome to python!\n")  # 如果剩余空间不足,则抛出ValueError

        # 不会移动文件指针,也不使用文件指针
        print(re.findall(rb'!', mm))  # [b'!', b'!']
        mm[0] = 97
        mm[6:12] = b'python'
        print(mm[:5])  # b"aello"

        # 会移动文件指针
        mm.seek(0)  # 指定文件指针到某个位置
        print(mm.read(13))  # 读指定字节数据 , b"aello python\n"
        print(mm.readline())  # 读一行数据 , b"welcome to python!\n"


def shared_value_simulation_tutorial():  # 模拟multiprocessing.Value
    mm = mmap.mmap(fileno=-1, length=8)
    obj = ctypes.c_int.from_buffer(mm, 2)  # buf大小不能小于c_int大小,返回一个共享源对象缓冲区的ctypes实例
    # obj = ctypes.c_int(12)  # 此obj无法在进程间共享
    ctypes.memset(ctypes.addressof(obj), 97, ctypes.sizeof(obj))  # 与标准C库函数相同,非必须,一般用于未给定初始值情况下的初始化工作
    obj.value = 2 ** 31 - 1  # 最大数
    print('in parent', mm[:], obj.value)  # in parent b'\x00\x00\xff\xff\xff\x7f\x00\x00' 2147483647 可以验证小端模式
    if 0 == os.fork():
        obj.value = 13
        print('in son', obj.value)  # in son 13
    else:
        time.sleep(1)
        print('in parent', obj.value)  # in parent 13


def test_shared_manager(shared_dict, shared_list, process_rlock):
    time.sleep(.001)
    with process_rlock:
        shared_dict['a'] += 1
        shared_list.append(os.getpid())


def test_shared_manager_namespace(namespace):
    namespace_list_ = namespace.list_  # 通用方法,针对可变对象
    namespace_list_[0] -= 1
    namespace_list_.append(2)
    namespace_list_ += [4]
    namespace.list_ = namespace_list_

    namespace_dict_ = namespace.dict_
    namespace_dict_['c'] = 'c'
    namespace_dict_['a']['b'] = 'ab'
    namespace.dict_ = namespace_dict_

    namespace.int_ += 2  # 针对不可变对象直接操作
    namespace.string_ += "i"


def shared_manager_tutorial():
    """
    服务器进程管理器比使用共享内存对象更灵活,因为它可以支持任意对象类型,单个管理器可以由网络上不同计算机上的进程共享,但比使用共享内存慢
    如果您有manager.list()对象,则对托管列表本身的任何更改都会传播到所有其他进程,但如果该列表中有一个列表,则对内部列表的任何更改都不会传播
    """
    with mp.Manager() as manager:  # 启动一个服务器进程(子进程)
        lock = mp.RLock()  # 必须从外部传入子程序
        shared_dict = manager.dict({'a': 0})
        shared_list = manager.list()
        processes = [mp.Process(target=test_shared_manager, args=(shared_dict, shared_list, lock)) for _ in range(10)]
        run_subroutine(processes)
        print(shared_dict)  # {'a': 10}
        print(shared_list)  # [16016, 19356, 18492, 17892, 13048, 19212, 1844, 14400, 7344, 1008]

        shared_dict_list = manager.list([manager.dict() for _ in range(2)])  # 如果在子进程中使用manager.dict()会失败
        # shared_dict_list = manager.list([{} for _ in range(2)]) # 此种方式用法错误
        first_inner = shared_dict_list[0]
        first_inner['a'] = 1
        first_inner['b'] = 2
        shared_dict_list[1]['c'] = 3
        shared_dict_list[1]['d'] = 4
        print(*shared_dict_list)  # {'a': 1, 'b': 2} {'c': 3, 'd': 4}

        namespace = manager.Namespace()
        namespace.list_ = [1]
        namespace.int_ = 1
        namespace.string_ = "h"
        namespace.dict_ = {'a': {'b': 1}}
        print(namespace)  # Namespace(dict_={'a': {'b': 1}}, int_=1, list_=[1], string_='h')
        process = mp.Process(target=test_shared_manager_namespace, args=(namespace,))
        run_subroutine([process])
        print(namespace)  # Namespace(dict_={'a': {'b': 'ab'}, 'c': 'c'}, int_=3, list_=[0, 2, 4], string_='hi')


class DeriveRelationship:
    """
    进程之间的派生拥有父子关系
    线程之间的派生是对等关系,都隶属于主进程的子线程
    线程进程交互派生时,进程隶属于上个进程的子进程,线程隶属于上个进程的子线程
    """

    @staticmethod
    def main():
        print('in main', os.getpid(), os.getppid())
        program = Thread(target=DeriveRelationship.kid1)
        run_subroutine([program])
        time.sleep(5)
        # in main 15944 13085
        # in kid1 15944 13085
        # in kid2 15948 15944
        # in kid3 15948 15944
        # in kid3 15950 15948

    @staticmethod
    def kid1():
        print('in kid1', os.getpid(), os.getppid())
        program = mp.Process(target=DeriveRelationship.kid2)
        run_subroutine([program])
        time.sleep(5)

    @staticmethod
    def kid2():
        print('in kid2', os.getpid(), os.getppid())
        programs = [Thread(target=DeriveRelationship.kid3), mp.Process(target=DeriveRelationship.kid3)]
        run_subroutine(programs)
        time.sleep(5)

    @staticmethod
    def kid3():
        print('in kid3', os.getpid(), os.getppid())
        time.sleep(5)


def join_tutorial():
    """
    该方法阻塞主程序直到子进程终止(不阻塞子进程运行),如果timeout是正数,则最多阻塞timeout秒,一个进程可以多次join
    join会调用系统的os.waitpid()方法回收子进程资源,防止产生僵尸进程,但如果超过timeout后父进程被唤醒,子进程在这之后结束,仍可能产生僵尸进程
    如果timeout未指定,则主进程总的等待时间T = max(t1,t2,...,tn)
    如果timeout大于0,T1 = min(timeout,max(t1,0)),...,Tn = min(timeout,max(tn-Tn-1,0)),则主进程总的等待时间T = sum(T1+T2,...+Tn)
    """
    processes = [
        mp.Process(target=time.sleep, args=(5,)),
        mp.Process(target=time.sleep, args=(3,)),
        mp.Process(target=time.sleep, args=(7,)),
    ]
    for process in processes:
        process.start()
    begin = end = time.monotonic()
    for process in processes:
        process.join()
        print('子进程阻塞耗时:', time.monotonic() - end)
        end = time.monotonic()
    print('总耗时:', end - begin)
    '''
    OUTPUT:
    子进程阻塞耗时: 5
    子进程阻塞耗时: 0
    子进程阻塞耗时: 2
    总耗时: 7
    '''


def test_rlock(lock, salary):
    time.sleep(.05)
    with lock:
        with lock:
            time.sleep(.05)
            salary[0] += 1


def test_barrier(status, barrier):
    try:
        time.sleep(random.random())
        barrier.wait(2)  # 如果2秒内没有达到障碍线程数量,会进入断开状态,引发BrokenBarrierError错误
        print(status, datetime.datetime.now())
    except BrokenBarrierError:
        print(f"等待超时,status:{status}")


def test_semaphore(timeout, semaphore):
    with semaphore:
        time.sleep(timeout)
        print('working in {}'.format(timeout))


class TestCondition:
    product = 15

    @staticmethod
    def producer(con):
        while True:
            with con:  # 获取锁
                if TestCondition.product >= 15:
                    con.wait()  # 先释放con,内部新建一个锁并阻塞,等wait超时或接收到notify时取消阻塞,然后重新尝试获取con
                else:
                    TestCondition.product += 5
                    con.notify()  # 处理完成发出通知告诉consumer
                time.sleep(2)

    @staticmethod
    def consumer(con):
        while True:
            with con:
                if TestCondition.product <= 10:
                    con.wait()
                else:
                    TestCondition.product -= 1
                    con.notify()
                time.sleep(1)


def lock_tutorial():
    """
    线程Lock的获取与释放可以在不同线程中完成,进程Lock的获取与释放可以在不同进程或线程中完成,嵌套Lock会导致死锁,但可以顺序出现多次
    线程/进程RLock的获取与释放必须在同一个线程/进程中完成(跟Lock一样,在A线/进程上锁后,没法在B线/进程上锁),RLock可以嵌套,也可以顺序
    Barrier每个任务按规定的分组数进行任务执行,如果没有达到规定的分组数,则需要一直阻塞等待满足规定的分数组(屏障点)才会继续执行任务
    BoundedSemaphore用于控制线/进程并发量(类似线程池),计数器 = release调用次数 - acquire调用次数 + 初始值(默认1)
    当计数器为负时acquire会阻塞,会对release做检测(Semaphore不会检测),如果计数器大于初始值则会引发ValueError,初始值为1的信号量等效为非重入锁
    Queue,Barrier和BoundedSemaphore都是在满足某些条件下执行线程,内部都是基于Condition实现
    注意: 线程锁没法在spawn产生的进程间传递(pickle没法序列化)
    """
    salary = [0]
    thread_rlock = ThreadRLock()
    threads = [Thread(target=test_rlock, args=(thread_rlock, salary)) for _ in range(100)]  # ok
    # thread_lock = ThreadLock()
    # threads = [Thread(target=test_rlock, args=(thread_lock, salary)) for _ in range(100)]  # deadlock
    run_subroutine(threads)
    assert salary[0] == 100

    condition = Condition()
    threads = [Thread(target=TestCondition.producer, args=(condition,)) for _ in range(2)]
    threads += [Thread(target=TestCondition.consumer, args=(condition,)) for _ in range(3)]
    run_subroutine(threads)

    barrier = Barrier(3, action=lambda: print('开始执行任务'))  # 设置3个障碍对象
    threads = [Thread(target=test_barrier, args=(i, barrier)) for i in range(8)]
    run_subroutine(threads)

    semaphore = BoundedSemaphore(2)
    t1 = time.monotonic()
    threads = [Thread(target=test_semaphore, args=(idx, semaphore)) for idx in range(5)]
    run_subroutine(threads)
    print(time.monotonic() - t1)  # 6


class ThreadLocal:
    def __init__(self):
        self.id = local()  # 保证同一个实例在不同线程中拥有不同的token值,redis分布式锁利用该性质达到线程安全
        self.token = SimpleNamespace()  # 相当于type('dummy', (), {})
        self.id.value = self.token.value = 0

    def show(self, timeout):
        self.id.value = random.random()
        self.token.value = os.urandom(16)
        time.sleep(timeout)
        print(self.id.value, self.token.value)

    @staticmethod
    def thread_local_tutorial():
        thread_local = ThreadLocal()
        print(thread_local.id.value, thread_local.token.value)
        threads = [Thread(target=ThreadLocal.show, args=(thread_local, i)) for i in range(1, 4)]
        run_subroutine(threads)
        print(thread_local.id.value, thread_local.token.value)
        """
        0                   0
        0.17592252714228607 b'K\xb3\x1b\n\xb4\xa9\xec\xbbR\x1e0\xdf#o\xddC'
        0.06397156707740081 b'K\xb3\x1b\n\xb4\xa9\xec\xbbR\x1e0\xdf#o\xddC'
        0.23054671171870256 b'K\xb3\x1b\n\xb4\xa9\xec\xbbR\x1e0\xdf#o\xddC'
        0                   b'K\xb3\x1b\n\xb4\xa9\xec\xbbR\x1e0\xdf#o\xddC'
        """
        thread_local = ThreadLocal()
        print(thread_local.id.value, thread_local.token.value)
        threads = [Thread(target=ThreadLocal.show, args=(thread_local, 0)) for _ in range(3)]
        run_subroutine(threads)
        print(thread_local.id.value, thread_local.token.value)
        """
        0                  0
        0.8147597177195579 b'\x8c\xe8\xa1\xfc\x1a\x9b\xf5:R\xf4#|w\xb0;}'
        0.2977537192745075 b"|\xa5\x01'}\xd2\xb8\xdb\xdfdf\x18a\xaeF\xc2"
        0.3604843239415484 b'_\x7fD=\x88w\x01\xb0\x92\xf1\xb4\x8d\xda\xb8@\xbc'
        0                  b'_\x7fD=\x88w\x01\xb0\x92\xf1\xb4\x8d\xda\xb8@\xbc'
        """


def fork_tutorial():
    # 当使用multiprocessing启动子进程时,Linux默认使用fork,macOS和Windows默认使用spawn
    # 在主进程创建了多个子进程的情况下，若某个子进程异常退出，一般不会影响其他子进程或主进程的正常运行
    # fork
    # 在父进程中调用fork(),内核会复制出一个几乎完全相同的子进程,子进程继承父进程的所有内存空间、文件描述符等资源(套接字、管道等)
    # 物理内存页采用写时复制: 读操作直接访问同一物理页,写操作时才会拷贝出一份给修改者,保证父子进程互不影响
    # fork()返回值: 父进程中返回子进程的PID,子进程中返回0
    # 子进程从fork()调用之后的那行指令开始执行
    # 父进程中已创建的锁（Lock、Semaphore等）也会被继承,但如果父进程在fork前某个锁已经被线程持有,就可能导致子进程中该锁永远无法释放,造成死锁
    # spawn
    # 1. 启动一个全新的Python解释器进程(等同于从命令行运行python)
    # 2. 新的解释器会将创建子进程的那个.py文件当作标准模块通过import加载一次,模块的所有语句都会执行——包括变量定义、函数/类声明
    # 3. 父进程将需要给子进程的目标函数target和它的args/kwargs,通过pickle序列化后发送给子进程,子进程在加载完主模块后,会反序列化这些对象,并调用target(*args, **kwargs)
    # spawn方式创建子进程时必须放在if __name__ == "__main__"下面, 防止无限递归创建子进程
    # 相比fork,spawn保证子进程从干净环境开始,避免继承不必要的状态（例如在多线程程序里避免锁状态被继承）,性能开销大于fork,且传输的数据需要支持pickle序列化
    # fork是一种内核级别的瞬时复制,需要系统支持; spawn则是跨平台的子进程创建方式,几乎所有语言都至少支持某种形式的spawn
    # import multiprocessing as mp
    # def son_process():
    #     print(a)
    #
    # if __name__ == "__main__":  # 只有作为主程序运行时才执行的代码
    #     a = 1
    #     # mp.set_start_method('spawn') # Error
    #     mp.set_start_method('fork')  # OK
    #     p = mp.Process(target=son_process)
    #     p.start()
    #     p.join()
    #
    # 父进程调用wait()或join(): 会阻塞父进程,直到某个子进程退出,随后回收该子进程的内核资源,避免产生僵尸进程(join内部会调用wait)
    # 进程组: 每个进程都有一个所属的进程组,默认组ID等于其父进程的PID,父进程,子进程以及子子进程都属于这个进程组
    # getpgid(0) 获取当前进程所在进程组ID
    # getpgid(pid) 获取指定进程pid所在的进程组ID
    # kill(pid, sig): 向进程或进程组发送信号,跟linux的命令行为一致
    # pid > 0 向指定PID的进程发送信号(可以验证kill杀死父进程,子进程会不会结束)
    # pid == 0 向调用进程所在的整个进程组发送信号
    #
    # 信号由操作系统或用户程序通过函数(如kill或raise)发送,用于通知进程发生了某些事件
    # 大多数信号可以通过signal()函数进行捕捉和处理,但SIGKILL和SIGSTOP例外,它们不能被捕捉、阻塞或忽略，操作系统会强制执行它们的行为
    # SIGINT：通常由终端按 Ctrl+C 触发
    # SIGCHLD：当子进程退出时,内核自动向父进程发送
    # signal(SIGCHLD, handler)控制子进程结束后的资源回收行为; signal(SIGCHLD,SIG_IGN)忽略SIGCHLD信号,内核会自动回收子进程,不会产生僵尸进程
    #
    # 孤儿进程: 父进程先于子进程退出,子进程将成为孤儿进程,被系统PID=1的init进程收养,并由其完成回收工作,一般不会造成危害
    # 僵尸进程(Zombie/Defunct): 子进程已经退出,但父进程尚未调用wait()来回收其资源,此时子进程成为僵尸进程,仅占用极少量内核资源,Linux中用defunct标记
    # 无法用kill -9直接杀死僵尸进程,需先终止其父进程(ps -ef | grep defunct),或者让父进程调用wait(),通过top能查看当前僵尸进程个数
    signal.signal(signal.SIGCHLD, lambda sv, frame: print(f"sv:{sv}, time:{datetime.datetime.now()},frame:{frame}"))
    signal.signal(signal.SIGINT, signal.SIG_IGN)  # protect process from KeyboardInterrupt signals
    if os.fork() == 0:
        time.sleep(1)
        print(f"in child process, time: {datetime.datetime.now()}")
        exit(1)
        print("此处不会被输出")
    else:
        os.wait()
        print("子进程结束,开始执行父进程")
        time.sleep(3)

    # os.fork()
    # os.fork() and os.fork() or os.fork()
    # os.fork()
    # print("+")  # 总共有20个进程,1个主进程+19个子进程

    # for i in range(3):
    #     os.fork()
    #     print(f"pid:{os.getpid()} ppid:{os.getppid()} pgid:{os.getpgid(0)}")  # 2+4+8=14 outputs


class QueueTutorial:
    @staticmethod
    def producer(task, index):
        # task.qsize()  # 在Unix平台如macOS,由于sem_getvalue()没实现,可能抛NotImplementedError异常
        task.put(index)
        print("in producer")
        time.sleep(2)

    @staticmethod
    def consumer(task):
        while True:
            item = task.get()  # (block=True, timeout=None)
            time.sleep(2)
            print("in consumer", item)
            task.task_done()

    @staticmethod
    def scheduler():
        task = mp.JoinableQueue()  # 操作均为原子性,用户无需再加锁
        for _ in range(2):
            # 多进程一定要把task传递过去,这里daemon必须为True,否则主程序会一直等待consumer
            process = mp.Process(target=QueueTutorial.consumer, args=(task,), daemon=True)
            process.start()
        with ThreadPoolExecutor(3) as executor:  # 为什么不能用ProcessPoolExecutor??
            for index in range(20):
                executor.submit(QueueTutorial.producer, task, index)  # 多线程中task不用传,传了也没事
        task.join()  # 阻塞主程序,每完成一次任务执行一次task_done,直到所有任务完成,调用时必须满足所有生产者已完成生产


def test_shared_pipe(conn):
    time.sleep(3)
    conn.send([42, None, 'hello'])  # 内部用pickle序列化后再传输


def shared_pipe_tutorial():
    # 如果两个线/进程尝试同时读/写管道的同一端,管道中的数据可能会损坏,同时使用管道不同端的进程不存在损坏的风险
    # 可以不用手动调用close函数,应为在对象引用计数为0时自定义的__del__会调用close释放资源
    parent_conn, child_conn = mp.Pipe(False)  # parent_conn只读,child_conn只写,默认为True
    # parent_conn, child_conn = mp.Pipe(True)  # parent_conn和child_conn可以读写
    p = mp.Process(target=test_shared_pipe, args=(child_conn,))
    p.start()
    print(parent_conn.poll(timeout=.5))  # False,最多阻塞timeout秒,时间内收到数据返回True并停止阻塞
    print(parent_conn.recv())  # [42, None, 'hello'], Blocks until there is something to receive.
    p.join()


if __name__ == "__main__":
    # shared_memory_tutorial()
    # shared_pipe_tutorial()
    # shared_manager_tutorial()
    # shared_mmap_tutorial()
    # shared_value_simulation_tutorial()
    # pool_executor_tutorial()
    # DeriveRelationship.main()
    # join_tutorial()
    # lock_tutorial()
    ThreadLocal.thread_local_tutorial()
    # fork_tutorial()
    # QueueTutorial.scheduler()
