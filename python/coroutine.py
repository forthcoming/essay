# 预激活协程的装饰器
def coroutine(func):  
    def primer(*args,**kwargs):
        gen=func(*args,**kwargs)
        next(gen)
        return gen
    return primer
    
#################################################################################################################################
    
# next等价于send(None),生成器一开始只能send(None)
from inspect import getgeneratorstate
def gen(a):
    print(f'start a={a}')
    b=yield a
    print(f'received b={b}')
    c=yield a+b
    print(f'received c={c}')

coro=gen(14)

print(getgeneratorstate(coro))  # GEN_CREATED

print(next(coro))
'''
start a=14
14
'''

print(getgeneratorstate(coro))  # GEN_SUSPENDED,该状态会出现很多次

print(coro.send(28))
'''
received b=28
42
'''

try:
    coro.send(99)   # received c=99
except StopIteration:
    pass
    
print(getgeneratorstate(coro))  # GEN_CLOSED

#################################################################################################################################

# yield from(后面接任意可迭代对象,类似与await,可用于简化for循环中的yield表达式,自动捕获迭代器异常,得到返回值)
from collections import namedtuple
Result=namedtuple('Result','count,average')

# 子生成器
def averager():
    total=.0
    average=count=0
    while True:
        term=yield
        if term is None:
            break
        total+=term
        count+=1
        average=total/count
    return Result(count,average)

# 委派生成器
def grouper(results,key):
    while True:
        results[key]=yield from averager()

# 客户端代码（调用方）
def main(data):
    results={}
    for key,values in data.items():
        group=grouper(results,key)  #仅生成<class 'generator'>,其他什么也不做,每次迭代会新建一个averager实例和grouper实例
        next(group)  #程序执行到term=yield的yield那里
        for value in values:
            group.send(value)
        group.send(None)  # 重要
    print(results)

if __name__=='__main__':
    data={
        'girl':[1,3,2,4],
        'boy':[4,4,3],
    }
    main(data)   #{'girl': Result(count=4, average=2.5), 'boy': Result(count=3, average=3.6666666666666665)}

#################################################################################################################################

def gen():
    yield from 'AB'
    yield from range(3)

from collections import Iterable
def flatten(items,ignore_types=(str,bytes)):
    for x in items:
        if isinstance(x,Iterable) and not isinstance(x,ignore_types):
            yield from flatten(x)
            # for y in flatten(x):
            #     yield y
        else:
            yield x

for x in flatten([2,[3,[5,6,'avatar'],7],8]):
    print(x)
    
#################################################################################################################################

# await sleep
import asyncio
async def find(num,div_by):
    print(f'start {num} {div_by}')
    located=[]
    for i in range(num):
        if i % div_by == 0:
            located.append(i)
        if i % 50000==0:  
            await asyncio.sleep(0) # 更耗时,但实现了并行
    print(f'end {num} {div_by}')
    return located

tasks=[find(508000,34113),find(100052,3210),find(500,3)]
loop=asyncio.get_event_loop()
results=loop.run_until_complete(asyncio.gather(*tasks))  # find返回的结果保存在results
loop.close()
'''
start 100052 3210
start 500 3
start 508000 34113
end 500 3
end 100052 3210
end 508000 34113
'''

#################################################################################################################################

耗时的操作一般是一些IO操作,例如网络请求,文件读取等
我们使用asyncio.sleep函数来模拟IO操作
协程是运行在单线程中的并发,目的是让这些IO操作异步化
asyncio实现并发,就需要多个协程来完成任务,每当有任务阻塞的时候就await,然后其他协程继续工作
创建多个协程的列表,然后将这些协程注册到事件循环中
通常在Python中我们进行并发编程一般都是使用多线程或者多进程来实现的
对于计算型任务由于GIL的存在我们通常使用多进程来实现
而对与IO型任务我们可以通过线程调度来让线程在执行IO任务时让出GIL,从而实现表面上的并发
其实对于IO型任务我们还有一种选择就是协程，协程是运行在单线程当中的"并发"
协程相比多线程一大优势就是省去了多线程之间的切换开销,获得了更大的运行效率
Python中的asyncio也是基于协程来进行实现的

#################################################################################################################################

import asyncio,time
async def do_some_work(x):
    print('Waiting: ', x)
    await asyncio.sleep(x)  #在sleep的时候使用await让出控制权,即当遇到阻塞调用的函数的时使用await方法将协程的控制权让出,以便loop调用其他的协程
    return 'Done after {}s'.format(x)

start=time.time()
coroutine=[do_some_work(2),do_some_work(3),do_some_work(4),do_some_work(5),]
loop = asyncio.get_event_loop()
tasks=loop.run_until_complete(asyncio.gather(*coroutine))
for task in tasks:
    print(task)
print(time.time()-start) #总耗时5s,5s的阻塞时间，足够前面3个协程执行完毕。如果是同步顺序的任务，那么至少需要14s。

start=time.time()
tasks=loop.run_until_complete(asyncio.gather(do_some_work(3),do_some_work(6)))
for task in tasks:
    print(task)
print(time.time()-start)  #总耗时6s

#################################################################################################################################

import asyncio
async def do_some_work(x):
    print('Waiting: ', x)
    return 'values'
def callback(future):
    print('Callback: ', future.result())
loop = asyncio.get_event_loop()   #<_WindowsSelectorEventLoop running=False closed=False debug=False>

coroutine = do_some_work(2)  #协程不能直接运行,需要把协程加入到事件循环(loop),由后者在适当的时候调用协程
print(coroutine)             #<coroutine object do_some_work at 0x00000211B0286150>
result=loop.run_until_complete(coroutine)  #将协程注册到事件循环,并启动事件循环,当传入一个协程,其内部会自动封装成task
print(result)                #values

coroutine = do_some_work(2)
task = loop.create_task(coroutine) 
print(task)    #<Task pending coro=<do_some_work() running at C:\Users\root\Desktop\111.py:84>>
loop.run_until_complete(task)
print(task,task.result())  #<Task finished coro=<do_some_work() done, defined at C:\Users\root\Desktop\111.py:84> result='values'> values

coroutine = do_some_work(2)
task = loop.create_task(coroutine)
task.add_done_callback(callback)  #coroutine执行结束时候会调用回调函数,并通过参数future获取协程执行的结果.task和回调里的future是同一个对象
loop.run_until_complete(task)

#################################################################################################################################

对于IO密集型: 协程>多线程>多进程>单进程
import requests,asyncio,aiohttp,time
from concurrent.futures import ThreadPoolExecutor,ProcessPoolExecutor

async def fetch_async():
    async with aiohttp.request('GET', 'http://www.baidu.com') as r:
        return await r.text()
async def main():
    futures=[loop.run_in_executor(None, requests.get, 'http://www.baidu.com') for i in range(100)]
    response=[await future for future in futures]
    print(response)

if __name__ == '__main__':
    task = main()
    print(asyncio.iscoroutinefunction(main))  # True
       print(asyncio.iscoroutine(task))          # True  
    # start=time.time()
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main())
    # loop.close()
    # print(time.time()-start)

    # start=time.time()
    # event_loop = asyncio.get_event_loop()
    # results = event_loop.run_until_complete(asyncio.gather(*([fetch_async()]*100)))  #asyncio.gather可以按顺序搜集异步任务执行的结果
    # print(len(results))
    # print(time.time()-start)   #0.04

    # start=time.time()
    # with ThreadPoolExecutor() as executor:
       #  for response in executor.map(requests.get, ['http://www.baidu.com']*100)
       #      print(status.status_code)
    # print(time.time()-start)   #0.27

    start=time.time()
    with ProcessPoolExecutor() as executor:   #1.18
        for response in executor.map(requests.get, ['http://www.baidu.com']*100)
            print(status.status_code)
    print(time.time()-start)
