import asyncio
import os
import time
import aiohttp
import uvloop
import concurrent.futures
import threading

"""
协程是运行在单线程中的并发,目的是让这些IO操作异步化,相比多线程一大优势是省去了多线程之间的切换开销,但没法利用CPU多核资源
如果一个对象可以在await语句中使用,那么它就是可等待对象,三种主要类型为 协程,任务,Future
await后面一般接耗时IO操作,事件循环遇到await后会挂起当前程序执行,去执行别的程序,直到await挂起的程序IO操作结束,拿到结果后继续执行
Future是一种特殊的低层级可等待对象,表示一个异步操作的最终结果
对于IO密集型: 协程>多线程>多进程>单线程
uvloop.run和asyncio.run都是阻塞,前者性能更高,每次调用都会创建和销毁事件循环(event loop),一个线程只能有一个事件循环
task交还控制权给event loop情况是task执行完或者task遇到await
"""


async def say(delay, what):
    print(f"say_after started at {time.strftime('%X')}")
    await asyncio.sleep(delay)  # 模拟IO操作,每当有任务阻塞的时候就await
    print(what)
    print(f"say_after finished at {time.strftime('%X')}")
    return delay


async def run_say_by_coroutine():  # 并发运行多个协程
    print(f"main started at {time.strftime('%X')}")
    # coroutine objects,前提是函数被async修饰,类似于生成器初始化
    coroutines = [say(3, 'world'), say(4, 'say'), say(2, 'hello')]
    print(asyncio.iscoroutinefunction(say))  # True
    print(asyncio.iscoroutine(coroutines[0]))  # True
    # 一次性返回say返回值列表,与coroutine顺序一致,入参也可以是tasks,如果是coroutines会隐式转换成tasks
    results = await asyncio.gather(*coroutines, return_exceptions=True)  # True代表任务出错不影响其他任务执行
    for result in results:
        if isinstance(result, Exception):
            print(f'error:{result}')
        else:
            print(f'data:{result}')
    print(f"main finished at {time.strftime('%X')}")


async def run_say_by_task():  # 并发运行多个协程
    print(f"main started at {time.strftime('%X')}")
    coroutines = [say(3, 'world'), say(4, 'say'), say(2, 'hello')]
    # task对象, create_task将coroutine变为task,并注册到event loop,非阻塞
    tasks = [asyncio.create_task(c, name=f'task-{idx}') for idx, c in enumerate(coroutines)]
    for task in tasks:  # 如果主程序可以保证在task都完成后退出如await asyncio.sleep(10)且不需要task返回值,该步可省略,asyncio.gather类似
        print('over:', await task)  # 按tasks顺序返回say的返回值,返回完当前任务结果,才会继续返回下一个任务结果
    # done, pending = await asyncio.wait(tasks)  # 也可以不遍历,但没法保证返回的顺序
    # print('pending:', pending, 'done:', done)
    print(f"main finished at {time.strftime('%X')}")


########################################################################################################################
async def fetch():
    async with aiohttp.request('GET', 'http://www.baidu.com') as r:
        return await r.text()


async def run_fetch():
    results = await asyncio.gather(*([fetch()] * 100))
    print(len(results))


########################################################################################################################
async def hello(delay):
    loop = asyncio.get_running_loop()
    loop.slow_callback_duration = .5  # 默认0.1,记录执行时间超过阈值的回调或任务(阻塞事件循环),需要事件循环debug=True
    print(f"hello started at {time.strftime('%X')}")
    time.sleep(delay)  # 使用time.sleep 模拟阻塞
    print(f"hello finished at {time.strftime('%X')}")
    return delay


async def test_callback_duration():
    start_time = time.monotonic()
    for i in range(4):
        await asyncio.create_task(hello(1))
        # await hello(1)  # 理解create_task和直接await直接区别,这么调用只会有一个task,除非配合await asyncio.sleep一起使用
        # await asyncio.sleep(0)  # 将控制权还给事件循环,相当于当前事件结束
    print(f"test_callback_duration: {time.monotonic() - start_time}")


########################################################################################################################
def blocking_io(chunk_size):
    # File operations (such as logging) can block the event loop: run them in a thread pool.
    print(f'in blocking_io, pid:{os.getpid()}, thread_id:{threading.get_ident()}')
    with open('/dev/urandom', 'rb') as f:
        return f.read(chunk_size)


def cpu_bound():
    # CPU-bound operations will block the event loop: in general it is preferable to run them in a process pool.
    print(f'in cpu_bound, pid:{os.getpid()}, ppid:{os.getppid()}')
    return sum(i * i for i in range(10 ** 7))


async def main():
    print(f'in main, pid:{os.getpid()}, thread_id:{threading.get_ident()}')
    # 1. Run in the default loop's executor:
    result = await asyncio.to_thread(blocking_io, 100)
    print('default thread pool', result)

    # 2. Run in a custom process pool:
    loop = asyncio.get_running_loop()
    with concurrent.futures.ProcessPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, cpu_bound)
        print('custom process pool', result)


if __name__ == "__main__":
    # uvloop.run(run_say_by_coroutine())
    # asyncio.run(run_say_by_task())
    # asyncio.run(run_fetch())
    # uvloop.run(test_callback_duration(), debug=True)
    asyncio.run(main(), debug=True)
