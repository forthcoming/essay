import os
import random
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from multiprocessing import shared_memory, Value, Process, Manager, RLock as ProcessRLock
from multiprocessing.dummy import Process as Thread, Lock as ThreadLock, RLock as ThreadRLock
from threading import get_ident

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
如果主进程开了多个子进程,而子进程出错,并不影响其他子进程和主进程的运行,但其自身会变为僵尸进程
应为主进程没有join操作给其收尸,在Linux中用"defunct"标记该进程,通过top也能查看当前的僵尸进程个数

进程间通信
进程间数据不共享,但共享同一套文件系统,所以访问同一文件或终端可以实现进程间通信,但效率低(文件是硬盘上的数据)且需要自己加锁处理
常见方式是共享内存(Value & Array & shared_memory & Manager),队列(Queue)

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
    process = Process(target=interprocess_communication, args=(new_shared,))
    run_subroutine([process])

    print(shared.buf[:6].tobytes(), shared.buf[:6].tolist())  # b"howdyB" [104, 111, 119, 100, 121, 66]
    shared.close()  # Close each SharedMemory instance
    shared.unlink()  # Call unlink only once to release the shared memory


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
        time.sleep(100)
        # in main 15944 13085
        # in kid1 15944 13085
        # in kid2 15948 15944
        # in kid3 15948 15944
        # in kid3 15950 15948

    @staticmethod
    def kid1():
        print('in kid1', os.getpid(), os.getppid())
        program = Process(target=DeriveRelationship.kid2)
        run_subroutine([program])
        time.sleep(100)

    @staticmethod
    def kid2():
        print('in kid2', os.getpid(), os.getppid())
        programs = [Thread(target=DeriveRelationship.kid3), Process(target=DeriveRelationship.kid3)]
        run_subroutine(programs)
        time.sleep(100)

    @staticmethod
    def kid3():
        print('in kid3', os.getpid(), os.getppid())
        time.sleep(100)


def join_tutorial():
    """
    该方法阻塞主程序直到子进程终止,但不会阻塞其他子程序的运行,如果timeout是正数,则最多阻塞timeout秒,一个进程可以多次join
    join会调用系统的os.waitpid()方法来获取子进程的退出信息,消除子进程,防止产生僵尸进程,但如果超过timeout后父进程被唤醒,子进程在这之后结束,仍可能产生僵尸进程
    如果timeout未指定,则主进程总的等待时间T = max(t1,t2,...,tn)
    如果timeout大于0,T1 = min(timeout,max(t1,0)),...,Tn = min(timeout,max(tn-Tn-1,0)),则主进程总的等待时间T = sum(T1+T2,...+Tn)
    """
    processes = [
        Process(target=time.sleep, args=(5,)),
        Process(target=time.sleep, args=(3,)),
        Process(target=time.sleep, args=(7,)),
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
    with Manager() as manager:
        process_rlock = ProcessRLock()  # 必须从外部传入子程序
        shared_dict = manager.dict({'a': 0})
        shared_list = manager.list()
        processes = [Process(target=test_shared_manager, args=(shared_dict, shared_list, process_rlock)) for _ in
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
        process = Process(target=test_shared_manager_namespace, args=(namespace,))
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


if __name__ == "__main__":
    # shared_memory_tutorial()
    # shared_value_tutorial()
    # shared_manager_tutorial()
    pool_executor_tutorial()
    # DeriveRelationship.main()
    # join_tutorial()
    # rlock_tutorial()

# def test0():
#     mm = mmap.mmap(fileno=-1, length=256,
#                    access=mmap.ACCESS_COPY)  # fileno=-1 means map anonymous memory,length不能小于所写内容总字节数
#     mm.write(
#         b"Hello world!\n")  # 会移动文件指针,If the mmap was created with ACCESS_READ, then writing to it will raise a TypeError exception.
#     mm.write(b"welcome to python!\n")  # 如果剩余空间不足,则抛出ValueError

#     # 不会移动文件指针,也不使用文件指针
#     print(re.findall(rb'!', mm))
#     mm[0] = 97
#     mm[6:12] = b'python'
#     print(mm[:5])

#     # 会移动文件指针
#     mm.seek(0)  # 指定文件指针到某个位置
#     print(mm.read(13))  # 读指定字节数据
#     print(mm.readline())  # 读一行数据
#     mm.close()  # Subsequent calls to other methods of the object will result in a ValueError exception being raised. This will not close the open file.


# def test1():
#     with open("hello.txt", "wb") as f:
#         f.write(b"Hello Python!\n")

#     with open("hello.txt", "r+b") as f:  # 读写权限要与mmap保持一致
#         with mmap.mmap(f.fileno(), 0,
#                        access=mmap.ACCESS_COPY) as mm:  # 向ACCESS_WRITE内存映射赋值会影响内存和底层的文件,向ACCESS_COPY内存映射赋值会影响内存,但不会更新底层的文件
#             print(mm.readline())  # prints b"Hello Python!\n"
#             print(mm[:5])  # prints b"Hello"
#             mm[6:] = b" world!\n"
#             mm.seek(0)
#             print(mm.readline())  # prints b"Hello  world!\n"


# def test2():
#     """
#     create an anonymous map and exchange data between the parent and child processes
#     MAP_PRIVATE creates a private copy-on-write mapping, so changes to the contents of the mmap object will be private to this process(A进程更改的数据不会同步到B进程);
#     MAP_SHARED creates a mapping that's shared with all other processes mapping the same areas of the file. The default value is MAP_SHARED(A进程更改的数据会同步到B进程).
#     在MAP_SHARED情况下各个进程的mm对象独立,意味着close,文件指针等不相互影响,仅共享数据

#     length申请的是虚拟内存VIRT(注意length要大点,应为本身会预申请一定大小的虚拟内存)
#     如果flags=mmap.MAP_PRIVATE,write占用的是驻留内存RES; 如果flags=mmap.MAP_SHARED,write占用的是共享内存SHR,但由于RES包含SHR,所以RES也会相应增大
#     """
#     mm = mmap.mmap(-1, length=13, flags=mmap.MAP_SHARED)
#     mm.write(b"Hello world!")
#     mm.seek(0)
#     pid = os.fork()

#     if pid == 0:  # In a child process
#         mm[6:12] = b'python'
#         print('child process: ', mm.readline())
#         print('child process: ', mm.tell())
#         mm.close()
#         os._exit(0)   # 会停止进程,即使有异常处理也会失效
#     else:  # In a parent process
#         time.sleep(1)  # 让子进程先执行
#         print('parent process: ', mm.tell())
#         print('parent process: ', mm.readline())
#         mm.close()


# def test3():  # 进程间通信(模拟multiprocessing.Value)
#     mm = mmap.mmap(fileno=-1, length=8)
#     buf = memoryview(mm)
#     obj = ctypes.c_int.from_buffer(buf)  # buf大小不能小于c_int大小,正确使用方式是跟c_int一般大
#     # obj=ctypes.c_int(12)  # 此obj无法在进程间共享
#     ctypes.memset(ctypes.addressof(obj), 97, ctypes.sizeof(obj))  # 非必须,一般用于未给定初始值情况下的初始化工作
#     obj.value = 2 ** 31 - 1  # 最大数
#     print(mm[:], buf.tobytes(), obj.value)
#     mm.write(b"Hello\n")  # 会影响到obj的值,应为操作的是同一块内存
#     print(mm[:], buf.tobytes(), obj.value)

#     print('in parent', obj.value)
#     if 0 == os.fork():
#         obj.value = 13
#         print('in son', obj.value)
#     else:
#         time.sleep(1)
#         print('in parent', obj.value)


# if __name__ == '__main__':
#     test2()

# ##################################################################################################################################

# # thread local
# from multiprocessing.dummy import Process
# from os import urandom


# class ThreadLocal:
#     def __init__(self):
#         # self.token=local()  # 保证同一个实例在不同线程中拥有不同的token值,redis分布式锁利用该性质达到线程安全
#         self.token = type('dummy', (), {})

#     def show(self, timeout):
#         self.token.value = urandom(16)
#         time.sleep(timeout)
#         print(self.token.value)


# thread_local = ThreadLocal()

# processes = [Process(target=lambda thread_local, timeout: thread_local.show(timeout), args=(thread_local, idx)) for idx
#              in range(1, 4)]
# for process in processes:
#     process.start()
# for process in processes:
#     process.join()

# ##################################################################################################################################

# import threading


# def plyer_display():
#     print('初始化通过完成,音视频同步完成,可以开始播放....')


# barrier = threading.Barrier(3, action=plyer_display, timeout=None)  # 设置3个障碍对象


# def player_init(status):
#     print(status)
#     try:
#         barrier.wait(2)  # 如果2秒内没有达到障碍线程数量,会进入断开状态,引发BrokenBarrierError错误
#     except Exception as e:  # BrokenBarrierError错误
#         print("等待超时了... ")
#     else:
#         print("xxxooooxxxxxooooxxxoooo")


# if __name__ == '__main__':

#     status_list = ["init ready", "video ready", "audio ready"]
#     thread_list = []
#     for i in range(0, 3):
#         t = threading.Thread(target=player_init, args=(status_list[i],))
#         t.start()
#         thread_list.append(t)
#     for t in thread_list:
#         t.join()
# '''
# output:
# init ready
# video ready
# audio ready
# 初始化通过完成,音视频同步完成,可以开始播放....
# xxxooooxxxxxooooxxxoooo
# xxxooooxxxxxooooxxxoooo
# xxxooooxxxxxooooxxxoooo
# '''

# ctypes.memset(dst, c, count)
# Same as the standard C memset library function: fills the memory block at address dst with count bytes of value c. dst must be an integer specifying an address, or a ctypes instance.

# from_buffer(source[, offset])
# This method returns a ctypes instance that shares the buffer of the source object. The source object must support the writeable buffer interface.
# The optional offset parameter specifies an offset into the source buffer in bytes; the default is zero. If the source buffer is not large enough a ValueError is raised.
