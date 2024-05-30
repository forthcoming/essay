import asyncio
import time
import aiohttp
import uvloop

"""
协程是运行在单线程中的并发,目的是让这些IO操作异步化,相比多线程一大优势是省去了多线程之间的切换开销,但没法利用CPU多核资源
如果一个对象可以在await语句中使用,那么它就是可等待对象,三种主要类型为 协程,任务,Future
await后面一般接耗时IO操作,事件循环遇到await后会挂起当前程序执行,去执行别的程序,直到await挂起的程序IO操作结束,拿到结果后继续执行
Future是一种特殊的低层级可等待对象,表示一个异步操作的最终结果
对于IO密集型: 协程>多线程>多进程>单线程
asyncio内部创建一个新的event loop,task交还控制权给event loop情况是task执行完或者task遇到await,一个线程只能有一个事件循环
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
    print(await asyncio.gather(*coroutines))  # say返回值集合,与coroutine顺序一致,入参也可以是tasks,如果是coroutines会隐式转换成tasks
    print(f"main finished at {time.strftime('%X')}")


async def run_say_by_task():  # 并发运行多个协程
    print(f"main started at {time.strftime('%X')}")
    coroutines = [say(3, 'world'), say(4, 'say'), say(2, 'hello')]
    # task对象, create_task将coroutine变为task,并注册到event loop,非阻塞
    tasks = [asyncio.create_task(c, name=f'task-{idx}') for idx, c in enumerate(coroutines)]
    for task in tasks:  # 如果主程序可以保证在task都完成后退出如await asyncio.sleep(10)且不需要task返回值,该步可省略,asyncio.gather类似
        print('over:', await task)  # 按tasks顺序返回say的返回值
    # done, pending = await asyncio.wait(tasks)  # 也可以不遍历,但没法保证返回的顺序
    # print('pending:', pending, 'done:', done)
    print(f"main finished at {time.strftime('%X')}")


async def fetch():
    async with aiohttp.request('GET', 'http://www.baidu.com') as r:
        return await r.text()


async def run_fetch():
    results = await asyncio.gather(*([fetch()] * 100))
    print(len(results))


if __name__ == "__main__":
    # uvloop.run(run_say_by_coroutine())  # uvloop.run和asyncio.run都是阻塞,前者性能更高
    asyncio.run(run_say_by_task())
    # asyncio.run(run_fetch())
