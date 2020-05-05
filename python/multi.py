# ProcessPoolExecutor & ThreadPoolExecutor
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from threading import Lock,get_ident
import math,urllib.request,time,random,os

'''
ThreadPoolExecutor & ProcessPoolExecutor在提交任务的时候有两种方式,submit和map:
相同点:
1·都不阻塞程序,通过遍历结果集可以达到阻塞的效果
2·一旦某个子程序结束,会立即执行下一个任务,由work总耗时6s可以验证
3·主程序会等待子程序执行完才退出,相当与daemon=False
不同点:
1·map可以保证按顺序输出,submit按照谁先完成谁先输出
2·如果你要提交的任务是一样的,就可以简化成map.假如提交的任务不一样,或者执行的过程之可能出现异常（使用map执行过程中发现问题会直接抛出错误）就要用到submit()

shutdown(wait=True)
If wait is True then this method will not return until all the pending futures are done executing and the resources associated with the executor have been freed.
If wait is False then this method will return immediately and the resources associated with the executor will be freed when all pending futures are done executing.
Regardless of the value of wait, the entire Python program will not exit until all pending futures are done executing.
'''

urls = [
    'http://www.foxnews.com/',
    'http://www.cnn.com/',
    'http://europe.wsj.com/',
    'http://www.bbc.co.uk/',
    'http://some-made-up-domain.com/'
]

primes = [112272535095293, 112582705942171, 112272535095293, 115280095190773, 1099726899285419]

task = [1, 2, 3, 2, 1, 5, 3, 4, 4, 6, 1, 5, 2, 7, 1, 10, 4, 6, 3, 5, 32, 4, 7, 2, 7, 3, 1, 9, 5, 2] * 10
result = {}
mutex = Lock()
_result = set()

def load_url(url, timeout):
    with urllib.request.urlopen(url, timeout=timeout) as conn:
        return conn.read()

def is_prime(n):
    if n % 2 == 0:
        return False
    sqrt_n = int(math.floor(math.sqrt(n)))
    for i in range(3, sqrt_n + 1, 2):
        if n % i == 0:
            return False
    return True

def work(second):
    time.sleep(second)
    print(f'I have sleep {second} seconds, ident:{get_ident()}, PID:{os.getpid()}\n') # 可以看出只创建了max_workers个线程/进程
    return second

def consumer(item, mutex, _result):
    # 1/(int(time.time())&1)  # 线程池中出现错误,程序不会报错,需要手动捕捉异常

    time.sleep(random.uniform(0,.01))
    with mutex:
        if item in result:
            time.sleep(.01)
            result[item]+=1
        else:
            time.sleep(.01)
            result[item]=1

    # with mutex:
    #     while True:
    #         if item in _result:
    #             time.sleep(.001)
    #         else:
    #             time.sleep(random.uniform(0, .01))
    #             _result.add(item)
    #             break
    # if item in result:
    #     time.sleep(random.uniform(0, .01))
    #     result[item] += 1
    # else:
    #     time.sleep(random.uniform(0, .01))
    #     result[item] = 1
    # _result.remove(item)

    # error
    # time.sleep(random.uniform(0,.01))
    # if item in result:
    #     time.sleep(random.uniform(0,.01))
    #     result[item]+=1
    # else:
    #     time.sleep(random.uniform(0,.01))
    #     result[item]=1

if __name__ == '__main__':
    # with ThreadPoolExecutor(max_workers=2) as executor:   # with代码块结束会调用executor.shutdown(),其中包含对线程的join操作
    #     futures = {executor.submit(load_url, url, 30): url for url in urls}  # 非阻塞
    #     '''
    #     阻塞,只要有线程结束(finished or were cancelled)就返回,直至所有线程结束(仅在获取线程返回值时才需要调用)
    #     Any futures given by fs that are duplicated will be returned once.
    #     Any futures that completed before as_completed() is called will be yielded first. The returned iterator raises a concurrent.futures.
    #     timeout不会影响线程的执行,只有40s之后返回的线程,在取其返回值时会抛出concurrent.futures._base.TimeoutError异常
    #     '''
    #     for future in as_completed(futures,timeout=40): # 阻塞
    #         print(futures)
    #         url = futures[future]
    #         try:
    #             data = future.result()
    #         except Exception as exc:
    #             print('%r generated an exception: %s' % (url, exc))
    #         else:
    #             print('%r page is %d bytes' % (url, len(data)))

    # with ProcessPoolExecutor(2) as executor:
    #     for number, result in zip(primes, executor.map(is_prime,primes)): # map本身非阻塞,遍历会使其阻塞
    #         print('{} is prime: {}'.format(number, result))

    # with ProcessPoolExecutor(2) as executor:
    #     for result in executor.map(work,[3,2,4]):
    #         print('the result is {}'.format(result))

    with ThreadPoolExecutor(6) as executor:
        for item in task:
            executor.submit(consumer, item, mutex, _result)
    print(len(task), sum(result.values()))

###########################################################################################################################

Pipe
# The Pipe() function returns a pair of connection objects connected by a pipe which by default is duplex (two-way).
# Each connection object has send() and recv() methods (among others). Note that data in a pipe may become corrupted if two processes (or threads) try to read from or write to the same end of the pipe at the same time.
# Of course there is no risk of corruption from processes using different ends of the pipe at the same time.

import time
from multiprocessing import Process, Pipe

def f(conn):
    time.sleep(3)
    conn.send([42, None, 'hello'])
    conn.close()

if __name__ == '__main__':
    parent_conn, child_conn = Pipe(False)  # parent_conn只读,child_conn只写
    # parent_conn, child_conn = Pipe(True)  # parent_conn和child_conn可以读写,默认为True
    p = Process(target=f, args=(child_conn,))
    p.start()
    '''
    返回值bool类型,whether there is any data available to be read.
    If timeout is not specified then it will return immediately.
    If timeout is a number then this specifies the maximum time in seconds to block.
    If timeout is None then an infinite timeout is used.
    '''
    parent_conn.poll(timeout=1)
    print(parent_conn.recv())    # [42, None, 'hello'], Blocks until there is something to receive.
    p.join()

###########################################################################################################################
    
进程中的变量传递(可变对象x从A进程传给B进程时,即使id没变,但仍然是一个全新的对象y,y在刚进B的那一刻值与x相同,此后便再无关联,子进程结束时其test被销毁)
from multiprocessing import Process 
import time,os
class A:
    a=0
    b=[]
    def __init__(self):
        self.c=1
        self.d=[]
test=A()

print(test.a,test.b,test.c,test.d,id(test.a),id(test.b),id(test.c),id(test.d))

def main():
    print('in main',os.getpid(),os.getppid())
    test.a=11
    test.b.append(22)
    test.c=33
    test.d.append(44)
    program=Process(target=kid,args=(test,))
    program.start()
    program.join()
    print('in main',test.a,test.b,test.c,test.d,id(test.a),id(test.b),id(test.c),id(test.d))
    
def kid(test):
    print('in kid',os.getpid(),os.getppid())
    test.a=55
    test.b.append(66)
    test.c=77
    test.d.append(88)
    print('in kid',test.a,test.b,test.c,test.d,id(test.a),id(test.b),id(test.c),id(test.d))
    time.sleep(2)

main()
print(test.a,test.b,test.c,test.d,id(test.a),id(test.b),id(test.c),id(test.d))

output:
0 [] 1 [] 4355075824 4359193136 4355075856 4359193776
in main 2929 1121
in kid 2930 2929
in kid 55 [22, 66] 77 [44, 88] 4355077584 4359193136 4355078288 4359193776
in main 11 [22] 33 [44] 4355076176 4359193136 4355076880 4359193776
11 [22] 33 [44] 4355076176 4359193136 4355076880 4359193776

###########################################################################################################################

concurrent:
当有多个线程在操作时,如果系统只有一个CPU,则它根本不可能真正同时进行一个以上的线程,它只能把CPU运行时间划分成若干个时间段
再将时间段分配给各个线程执行,在一个时间段的线程代码运行时,其它线程处于挂起状态.这种方式我们称之为并发(Concurrent)
parallel:
当系统有一个以上CPU时,则线程的操作有可能非并发.当一个CPU执行一个线程时,另一个CPU可以执行另一个线程,两个线程互不抢占CPU资源,可以同时进行
这种方式我们称之为并行(Parallel),并行需要两个或两个以上的线程跑在不同的处理器上,并发可以跑在一个处理器上通过时间片进行切换

线程 & 进程
由于GIL锁的缘故,线程实际上是并发运行(即便有多个cpu,线程会在其中一个cpu来回切换,只占用一个cpu资源),而进程才是真正的并行(同时执行多个任务,占用多个cpu资源)
sys.getswitchinterval() # current thread switch interval
sys.setswitchinterval(n)
'''
The parameter must represent the desired switching delay in seconds A typical value is 0.005 (5 milliseconds).
Set the interpreter’s thread switch interval (in seconds). 
This floating-point value determines the ideal duration of the “timeslices” allocated to concurrently running Python threads. 
Please note that the actual value can be higher, especially if long-running internal functions or methods are used. 
Also, which thread becomes scheduled at the end of the interval is the operating system’s decision. The interpreter doesn’t have its own scheduler.
'''
子线程可以访问程序的全局变量并且改变变量本身,子线程也可以改变进程变量本身,前提是需要以参数形式传递给子线程
子进程or子进程中的子线程可以访问程序的全局变量,但是该变量的一份拷贝,并不能修改他,只不过值是一样而已
对于CPU密集型,python的多线程表现不如单线程好,但多进程效率更高,进程数不是越大越好,默认进程数等于电脑核数
技巧:如果一个任务拿不准是CPU密集还是I/O密集型(宜用多线程),且没有其它不能选择多进程方式的因素,都统一直接上多进程模式

###########################################################################################################################

# 进程之间的派生拥有父子关系
# 线程之间的派生是对等关系,都隶属于主进程的子线程
# 线程进程交互派生时,进程隶属于上个进程的子进程,线程隶属于上个进程的子线程
from multiprocessing.dummy import Process as Thread
from multiprocessing import Process 
import time,os

def start(programs):
    for program in programs:
        program.start()
    for program in programs:
        program.join()

def main():
    print('in main',os.getpid(),os.getppid())
    programs=[Thread(target=kid1)]
    start(programs)
    time.sleep(100)
    
def kid1():
    print('in kid1',os.getpid(),os.getppid())
    programs=[Process(target=kid2)]
    start(programs)
    time.sleep(100)

def kid2():
    print('in kid2',os.getpid(),os.getppid())
    programs=[Thread(target=kid3),Process(target=kid3)]
    start(programs)
    time.sleep(100)

def kid3():
    print('in kid3',os.getpid(),os.getppid())
    time.sleep(100)

main()
# in main 15944 13085
# in kid1 15944 13085
# in kid2 15948 15944
# in kid3 15948 15944
# in kid3 15950 15948

###########################################################################################################################

'''
如果主进程开了多个子进程,而子进程出错,并不影响其他子进程和主进程的运行,但其自身会变为僵尸进程（例如imghash.py）,应为主进程没有join操作给其收尸
在Linux中用"defunct"标记该进程,通过top也能查看当前的僵尸进程个数.
'''
from multiprocessing import Process
import time,os
def test(num):
    print('start test({})'.format(num))
    time.sleep(num)
    print('PPID:{} PID:{}'.format(os.getppid(),os.getpid()))  #PPID:7872 PID:10496

if __name__=='__main__':
    p = Process(target=time.sleep, name='python',args=(1000,))
    print(p,p.is_alive(),p.pid,p.name)         #<Process(python, initial)> False None python
    p.start()
    print(p, p.is_alive(),p.pid,p.name)        #<Process(python, started)> True 10732 python
    p.terminate()                              #终止
    time.sleep(0.1)                            #必须要停一下
    print(p,p.is_alive(),p.pid,p.name)         #<Process(python, stopped[SIGTERM])> False 10732 python

    p = Process(target=test, name='test',args=(4,))
    p.daemon=True  
    # daemon=True:  父进程結束,子进程/线程也將終止(When a process exits, it attempts to terminate all of its daemonic child processes.)
    # daemon=False: 父进程运行完,会接着等子进程/线程全部都执行完后才结束(注意线程也有daemon概念)
    print('PPID:{} PID:{}'.format(os.getppid(),os.getpid()))  #PPID:8092 PID:7872
    p.start() #异步执行子进程
    print('Process has start.')
    p.join()               
    print('Process end.')  # 执行到这里父进程将结束
    
###########################################################################################################################

# lock
from multiprocessing.dummy import Process,Lock
from threading import get_ident
mutex=Lock()  

def loop(n):
    global deposit
    for i in range(100000):
        deposit += n # 存
        deposit -= n # 取

def loop_lock(n):
    global deposit
    print(get_ident())
    # Return a non-zero integer that uniquely identifies the current thread amongst other threads that exist simultaneously.
    # This may be used to identify per-thread resources.A thread's identity may be reused for another thread after it exits.
    for i in range(100000):
        with mutex:  # 加锁会使速度变慢,注意这里不能写作with Lock(),mutex必须共享
            deposit += n # 存
            deposit -= n # 取

for i in range(10):
    deposit = 0 
    # threadings=[Process(target=loop, args=(5,)),Process(target=loop, args=(8,))]  # 最终可能是0,5,8,-5,-8
    threadings=[Process(target=loop_lock, args=(5,)),Process(target=loop_lock, args=(8,))]
    for thread in threadings:
        thread.start()
    for thread in threadings:
        thread.join()
    print(deposit)
'''
线程Lock的获取与释放可以在不同线程中完成,进程Lock的获取与释放可以在不同进程或线程中完成
线程RLock的获取与释放必须在同一个线程中完成,进程RLock的获取与释放必须在同一个进程或线程中完成
'''

###########################################################################################################################

# RLock(普通的锁里面不能再出现锁,但可以顺序出现多次)

from multiprocessing.dummy import Process,RLock,Lock,active_children
import time

salary = 0
rlock = RLock()
lock = Lock()

def run(mutex):
    print('start run')
    time.sleep(.5)
    with mutex:  # 此处只能用递归锁,否则后面的with mutex会拿不到锁
        print('in first lock')
        with mutex:
            print('in second lock')
            global salary
            salary +=1

def run_v1(mutex):
    print('start run')
    time.sleep(.5)
    with mutex:
        print('in first lock')
    with mutex:
        print('in second lock')
        global salary
        salary +=1
        
for i in range(10):
    # t = Process(target=run,args=(rlock,))   # ok
    # t = Process(target=run,args=(lock,))      # error
    # t = Process(target=run_v1,args=(rlock,))  # ok
    t = Process(target=run_v1,args=(lock,))   # ok
    t.start()

while active_children():
    print("当前线程：",active_children())
    time.sleep(1)
else:
    print(salary,'over')

###########################################################################################################################

semaphore manages an atomic counter representing the number of release() calls minus the number of acquire() calls, plus an initial value.
The acquire() method blocks if necessary until it can return without making the counter negative.
A bounded semaphore checks to make sure its current value doesn’t exceed its initial value. If it does, ValueError is raised.
In most situations semaphores are used to guard resources with limited capacity, for example, a database server.
If the semaphore is released too many times it’s a sign of a bug. If not given, value defaults to 1.
Once spawned, worker threads call the semaphore’s acquire and release methods when they need to connect to the server
The use of a bounded semaphore reduces the chance that a programming error which causes the semaphore to be released more than it’s acquired will go undetected.


###########################################################################################################################

join([timeout])
# If the optional argument timeout is None (the default), the method blocks until the process whose join() method is called terminates.
# If timeout is a positive number, it blocks at most timeout seconds. Note that the method returns None if its process terminates or if the method times out. Check the process’s exitcode to determine if it terminated.
# A process can be joined many times.
# 主程序一遇到join就会阻塞,直到join的子进程执行完毕,但不会阻塞所有子程序的运行
# join会调用系统的os.waitpid()方法来获取子进程的退出信息,消除子进程,防止产生僵尸进程,但如果超过timeout后父进程被唤醒,子进程在这之后结束,仍可能产生僵尸进程

from multiprocessing import Process
import time

def xx(a):
    time.sleep(5)
    return a

def yy(a):
    time.sleep(3)
    return a

def zz(a):
    time.sleep(7)
    return a

if __name__=='__main__':
    threadings=[Process(target=xx, args=(5,)),Process(target=yy, args=(8,)),Process(target=zz, args=(8,))]
    begin=time.time()
    for thread in threadings:
        thread.start()
    mid=time.time()
    print(mid-begin)
    for thread in threadings:
        thread.join()
        print('子进程阻塞耗时:',time.time()-mid)
        mid=time.time()
    print('总耗时:',time.time()-begin)
'''
OUTPUT:
0.053999900817871094
子进程阻塞耗时: 5.063000202178955
子进程阻塞耗时: 0.0
子进程阻塞耗时: 2.045599937438965
总耗时: 7.162600040435791
'''

###########################################################################################################################

进程间通信(Value & Array & Manager)
进程之间数据不共享,但是共享同一套文件系统,所以访问同一个文件,或同一个打印终端,是没有问题的.
虽然可以用文件共享数据实现进程间通信,但问题是:
1.效率低(共享数据基于文件,而文件是硬盘上的数据)
2.需要自己加锁处理
因此我们最好找寻一种解决方案能够兼顾:1、效率高(多个进程共享一块内存的数据) 2、帮我们处理好锁问题
这就是mutiprocessing模块为我们提供的基于消息的IPC通信机制:队列和管道
队列和管道都是将数据存放于内存中
队列又是基于(管道+锁)实现,可以让我们从复杂的锁问题中解脱出来.
我们应该尽量避免使用共享数据,尽可能使用消息传递和队列,避免处理复杂的同步和锁问题

###########################################################################################################################

# multiprocessing.Value(typecode_or_type, *args, lock=True)

Return a ctypes object allocated from shared memory. By default the return value is actually a synchronized wrapper for the object. 
The object itself can be accessed via the value attribute of a Value.
typecode_or_type determines the type of the returned object: it is either a ctypes type or a one character typecode of the kind used by the array module. 
*args is passed on to the constructor for the type.
If lock is True (the default) then a new recursive lock object is created to synchronize access to the value.
If lock is a Lock or RLock object then that will be used to synchronize access to the value.
If lock is False then access to the returned object will not be automatically protected by a lock, so it will not necessarily be “process-safe”.
Operations like += which involve a read and write are not atomic. 
So if, for instance, you want to atomically increment a shared value it is insufficient to just do "counter.value += 1"
Assuming the associated lock is recursive (which it is by default) you can instead do
with counter.get_lock():
    counter.value += 1
Note that lock is a keyword-only argument.

from multiprocessing import Process,Value
def work(share):
    with share.get_lock():
        share.value-=1
    
if __name__ == '__main__':
    share = Value('i',100)  # 在不需要锁的情况下可以Value('i',100,lock=False)
    processes=[Process(target=work,args=(share,)) for i in range(100)]
    for process in processes:
        process.start()
    for process in processes:
        process.join()
    print(share,share.value) # <Synchronized wrapper for c_long(0)> 0
    
###########################################################################################################################

# multiprocessing.Array(typecode_or_type, size_or_initializer, *, lock=True)

Return a ctypes array allocated from shared memory. By default the return value is actually a synchronized wrapper for the array.
typecode_or_type determines the type of the elements of the returned array: it is either a ctypes type or a one character typecode of the kind used by the array module.
If size_or_initializer is an integer, then it determines the length of the array, and the array will be initially zeroed. Otherwise,
size_or_initializer is a sequence which is used to initialize the array and whose length determines the length of the array.
If lock is True (the default) then a new lock object is created to synchronize access to the value.
If lock is a Lock or RLock object then that will be used to synchronize access to the value.
If lock is False then access to the returned object will not be automatically protected by a lock, so it will not necessarily be “process-safe”.

###########################################################################################################################

Manager
Server process managers are more flexible than using shared memory objects because they can be made to support arbitrary object types.
Also, a single manager can be shared by processes on different computers over a network. They are, however, slower than using shared memory.
manager不是进程安全,写操作需要加锁

from multiprocessing import Process, Manager
import os

def task(Dict, List):
    Dict['k'] = 'v'
    List.append(os.getpid())  # 获取子进程的PID

if __name__ == '__main__':
    with Manager() as manager:
        Dict = manager.dict({'a':1})  # 生成一个可以在多个进程之间共享的字典
        List = manager.list()

        processes=[Process(target=task, args=(Dict, List)) for i in range(10)]
        for process in processes:
            process.start()
        for process in processes:
            process.join()
        print(Dict)  # {'a': 1, 'k': 'v'}
        print(List)  # [16016, 19356, 18492, 17892, 13048, 19212, 1844, 14400, 7344, 1008]


import multiprocessing as mp
def f(ns):
    # ns.x.append(10) # 无效
    ns.x+=[10]

    # ns.y[0]+=20 # 无效
    ns_y=ns.y
    ns_y[0]+=20
    ns.y=ns_y

    ns_z=ns.z  # 通用方法
    ns_z['c']=123
    ns_z['a']['b']=321    
    ns.z=ns_z

if __name__ == '__main__':
    with mp.Manager() as manager:
        ns = manager.Namespace()
        ns.x = [10]
        ns.y = [10]
        ns.z = {'a':{'b':1}}
        print('before', ns)
        p = mp.Process(target=f, args=(ns,))
        p.start()
        p.join()
        print('after', ns)

        l_outer = manager.list([ manager.dict() for i in range(2) ])
        # l_outer = manager.list([ {} for i in range(2) ])
        d_first_inner = l_outer[0]
        d_first_inner['a'] = 1
        d_first_inner['b'] = 2
        l_outer[1]['c'] = 3
        l_outer[1]['z'] = 26
        print(l_outer[0])
        print(l_outer[1])

# Manager proxy objects are unable to propagate changes made to mutable objects inside a container.
# So in other words, if you have a manager.list() object, any changes to the managed list itself are propagated to all the other processes.
# But if you have a list inside that list, any changes to the inner list are not propagated, because the manager has no way of detecting the change.
# In order to propagate the changes, you have to modify the manager.list() object directly, as indicated by the note here.
# As you can see, when a new value is assigned directly to the managed container, it changes;
# when it is assigned to a mutable container within the managed container, it doesn't change;
# but if the mutable container is then reassigned to the managed container, it changes again.

