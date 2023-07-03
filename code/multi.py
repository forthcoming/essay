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
from multiprocessing.dummy import Process as Thread, Lock as ThreadLock, RLock as ThreadRLock
from threading import get_ident, local

"""
atexit
被注册的函数会在解释器正常终止时执行.atexit会按照注册顺序的逆序执行; 如果你注册了A, B 和 C, 那么在解释器终止时会依序执行C, B, A
通过该模块注册的函数, 在程序被未被Python捕获的信号杀死时并不会执行, 在检测到Python内部致命错误以及调用了os._exit()时也不会执行

concurrent(并发) & parallel(并行)
当系统只有一个CPU,则它不可能同时进行一个以上的线程,只能把CPU运行时间划分成若干个时间段
再将时间段分配给各个线程执行,在一个时间段的线程代码运行时,其它线程处于挂起状态.这种方式我们称为并发
当系统有多个CPU时,不同线程可以同时工作在不同的CPU上,这种方式我们称为并行

线程 & 进程
GIL只存在于CPython解释器中,其他解释器如Jython、IronPython、PyPy等不存在GIL的问题
每个Python进程都有自己的Python解释器和内存空间,因此GIL不会成为问题
对于CPU密集型任务通常使用多进程,进程数不是越大越好,默认进程数等于电脑核数
GIL导致线程是并发运行(即便有多个cpu,线程会在其中一个cpu来回切换),而进程是并行
标准库中所有阻塞型I/O函数都会释放GIL,time.sleep也会释放,因此尽管有GIL,线程还是能在I/O密集型应用中发挥作用
daemon=False: 父线/进程运行完,会接着等子线/进程全部都执行完后才结束
daemon=True: 父进程结束,他会杀死自己的子线/进程使其终止,但父进程被kill -9杀死时子进程不会结束,会被系统托管

进程间通信(进程间数据不共享)
共享内存如shared_memory, memoryview基于mmap实现,shared_memory基于memoryview实现
文件系统如Queue & Pipe & Manager, Queue和Manager基于Pipe实现

sys.setswitchinterval(n) # 设置解释器的线程切换间隔(以秒为单位),实际值可能更高,特别是在使用长时间运行的内部函数或方法时
在间隔结束时调度哪个线程是操作系统的决定,解释器没有自己的调度程序
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

    # with thread_lock:  # 必须加锁
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
    with代码块结束会调用executor.shutdown(wait=True),如果wait=True,则对任务进行join操作,因此主程序会等待with代码块所有任务结束
    无论wait的值是多少,整个程序都不会退出,直到所有待处理任务都执行完毕,即daemon=False
    一旦某个任务结束,会立即执行下一个任务,由pool_work总耗时6s可以验证
    如果提交的任务是一样的,就可以简化成map.假如提交的任务不一样,或者执行的过程之可能出现异常(map执行过程中发现问题会直接抛错)就要用到submit
    """
    args = [3, 2, 4]
    start_time = time.time()
    with ThreadPoolExecutor(2) as executor:
        futures = [executor.submit(pool_work, arg) for arg in args]  # concurrent.futures._base.Future,不阻塞下一行语句的执行
        time.sleep(3.5)  # 已经完成了两个任务
        # 任何在调用as_completed()之前完成的futures将首先被生成
        for future in as_completed(futures, timeout=3):  # 只要有任务完成或取消就返回,timeout秒后如果还有未完成任务抛出TimeoutError异常
            print(future.result(), futures)
    print(f"cost {time.time() - start_time} seconds")  # cost 6.006827116012573 seconds

    start_time = time.time()
    with ProcessPoolExecutor(2) as executor:  # 只创建max_worker=2个进程
        results = executor.map(pool_work, args)  # generator,不阻塞下一行语句的执行
        print(f'the results is {list(results)}')  # 都完成后按任务顺序返回
    print(f"cost {time.time() - start_time} seconds")  # cost 6.156317949295044 seconds

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
    mp.set_start_method("fork")  # 默认方式是spawn
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
    # buf = memoryview(mm)  # memoryview基于mmap实现
    mm.write(b"Hello world!")
    mm.seek(0)
    pid = os.fork()
    if pid == 0:  # In a child process
        mm[6:12] = b'python'
        print('child process: ', mm.readline(), mm.tell())
        mm.close()
        os._exit(0)  # 会停止进程,即使有异常处理也会失效
    else:  # In a parent process
        time.sleep(1)  # 让子进程先执行
        print('parent process: ', mm.tell(), mm.readline())
        mm.close()

    with mmap.mmap(fileno=-1, length=256, access=mmap.ACCESS_COPY) as mm:
        mm.write(b"Hello world!\n")  # 会移动文件指针,如果mmap使用ACCESS_READ创建,则写入会引发TypeError异常
        mm.write(b"welcome to python!\n")  # 如果剩余空间不足,则抛出ValueError

        # 不会移动文件指针,也不使用文件指针
        print(re.findall(rb'!', mm))
        mm[0] = 97
        mm[6:12] = b'python'
        print(mm[:5])

        # 会移动文件指针
        mm.seek(0)  # 指定文件指针到某个位置
        print(mm.read(13))  # 读指定字节数据
        print(mm.readline())  # 读一行数据


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


class DeriveRelationship:
    """
    进程之间的派生拥有父子关系
    线程之间的派生是对等关系,都隶属于主进程的子线程
    线程进程交互派生时,进程隶属于上个进程的子进程,线程隶属于上个进程的子线程
    """

    @staticmethod
    def main():
        print('in main', os.getpid(), os.getppid())
        program = Thread(target=DeriveRelationship.kid1)  # daemon=False且无法更改,想自定义请用threading.Thread
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
    该方法阻塞主程序直到子进程终止,但不会阻塞其他子程序的运行,如果timeout是正数,则最多阻塞timeout秒,一个进程可以多次join
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
    begin = end = time.time()
    for process in processes:
        process.join()
        print('子进程阻塞耗时:', time.time() - end)
        end = time.time()
    print('总耗时:', end - begin)
    '''
    OUTPUT:
    子进程阻塞耗时: 5
    子进程阻塞耗时: 0
    子进程阻塞耗时: 2
    总耗时: 7
    '''


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
    with mp.Manager() as manager:
        process_rlock = mp.RLock()  # 必须从外部传入子程序
        shared_dict = manager.dict({'a': 0})
        shared_list = manager.list()
        processes = [mp.Process(target=test_shared_manager, args=(shared_dict, shared_list, process_rlock)) for _ in
                     range(10)]
        run_subroutine(processes)
        print(shared_dict)  # {'a': 10}
        print(shared_list)  # [16016, 19356, 18492, 17892, 13048, 19212, 1844, 14400, 7344, 1008]

        shared_dict_list = manager.list([manager.dict() for _ in range(2)])
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


def test_lock(lock, salary):
    time.sleep(.05)
    with lock:
        with lock:
            time.sleep(.05)
            salary[0] += 1


def rlock_tutorial():
    """
    线程Lock的获取与释放可以在不同线程中完成,进程Lock的获取与释放可以在不同进程或线程中完成,嵌套Lock会导致死锁,但可以顺序出现多次
    线程RLock的获取与释放必须在同一个线程中完成,进程RLock的获取与释放必须在同一个进程或线程中完成,RLock可以嵌套,也可以顺序
    Semaphore是信号量锁,用来控制线/进程的并发数量,with semaphore启动
    """
    salary = [0]
    thread_rlock = ThreadRLock()
    threads = [Thread(target=test_lock, args=(thread_rlock, salary)) for _ in range(100)]  # ok
    # thread_lock = ThreadLock()
    # threads = [Thread(target=test_rlock, args=(thread_lock, salary)) for _ in range(100)]  # deadlock
    run_subroutine(threads)
    assert salary[0] == 100


class ThreadLocal:
    def __init__(self):
        self.id = local()  # 保证同一个实例在不同线程中拥有不同的token值,redis分布式锁利用该性质达到线程安全
        self.token = type('dummy', (), {})  # 注意此用法,很好类似达到namespace效果
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
    """
    子进程可通过fork或者spawn方式生成,spawn底层用了pickle将父进程数据序列化后传到子进程
    子进程是从fork后面那个指令开始执行,在父进程中fork返回新创建子进程的进程ID,子进程返回0
    kill(跟linux一致),pid>0: 向进程号pid的进程发送信号,可以验证kill杀死父进程,子进程会不会结束;pid=0: 向当前进程所在的进程组发送信号
    父进程里使用wait,相当于join,这个函数会让父进程阻塞,直到任意一个子进程执行完成,回收该子进程的内核进程资源
    每个进程都属于一个进程组,通过getpgid(0)获取,getpgid(pid)获取进程ID是pid所在组的组ID,默认为父进程id,父进程,子进程以及子子进程都属于这个进程组

    孤儿进程: 父进程退出而它的子进程还在运行,则子进程将成为孤儿进程
    僵尸进程: 使用fork创建子进程,如果子进程退出,父进程还在运行,并且没有调用wait/waitpid回收资源,则子进程成为僵死进程,Linux中用defunct标记
    如果主进程开了多个子进程,当某个子进程出错,并不影响其他子进程和主进程的运行,但其自身会变为僵尸进程
    multiprocessing不会产生孤儿进程,需要用os.fork模拟产生,可以产生僵尸进程
    僵尸进程将会导致资源浪费,而孤儿进程并不会有什么危害,将被init进程(进程号为1)所收养,成为该子进程的父进程,并对它们完成状态收集工作
    kill -9不能杀掉僵尸进程,可以先找到僵尸进程的父进程(ps -ef | grep defunct),将父进程杀掉,子进程就自动消失,通过top能查看当前僵尸进程个数

    所有信号都由操作系统来发,应用程序通过signal()捕捉,SIGKILL和SIGSTOP信号除外
    当子进程退出的时候,内核都会给父进程一个SIGCHLD信号,终端上按下ctrl+c会产生SIGINT信号
    如果父进程不关心子进程什么时候结束,可以用signal(SIGCHLD,SIG_IGN)通知内核,当子进程结束后内核会回收,默认采用SIG_DFL,代表不理会该信号
    """
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
        task.join()  # 阻塞主程序,每完成一次任务执行一次task_done,直到所有任务完成


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
    shared_pipe_tutorial()
    # shared_manager_tutorial()
    # shared_mmap_tutorial()
    # shared_value_simulation_tutorial()
    # pool_executor_tutorial()
    # DeriveRelationship.main()
    # join_tutorial()
    # rlock_tutorial()
    # ThreadLocal.thread_local_tutorial()
    # fork_tutorial()
    # QueueTutorial.scheduler()
