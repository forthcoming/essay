import asyncio
import time

import aiohttp

"""
协程是运行在单线程中的并发,目的是让这些IO操作异步化,相比多线程一大优势是省去了多线程之间的切换开销
如果一个对象可以在await语句中使用,那么它就是可等待对象,三种主要类型为 协程,任务,Future
Future是一种特殊的低层级可等待对象,表示一个异步操作的最终结果
对于IO密集型: 协程>多线程>多进程>单线程
"""


async def say_after(delay, what):
    print(f"say_after started at {time.strftime('%X')}")
    await asyncio.sleep(delay)
    print(what)
    print(f"say_after finished at {time.strftime('%X')}")
    return delay


async def run_say_after():
    coroutines = [say_after(3, 'world'), say_after(1, 'hello')]
    print(f"main started at {time.strftime('%X')}")
    print(await asyncio.gather(*coroutines))  # say_after返回值集合,与coroutine顺序一致,入参也可以是tasks,如果是coroutines会隐式转换成tasks
    print(f"main finished at {time.strftime('%X')}")
    # task交还控制权给event loop情况是task执行完或者task遇到await
    # tasks = [asyncio.create_task(c) for c in coroutines]  # task对象, create_task将coroutine变为task,并注册到event loop
    # for task in tasks:
    #     print(await task)  # say_after返回值


async def find(num, div_by):
    print(f"start find({num}, {div_by})")
    located = []
    for i in range(num):
        if i % div_by == 0:
            located.append(i)
        if i % 50000 == 0:
            await asyncio.sleep(0)  # 模拟IO操作,每当有任务阻塞的时候就await
    print(f"end find({num}, {div_by})")
    return located


def run_find():
    coroutines = [find(508000, 34113), find(100052, 3210), find(500, 3)]  # coroutine objects,前提是函数被async修饰,类似于生成器初始化
    print(asyncio.iscoroutinefunction(find))  # True
    print(asyncio.iscoroutine(coroutines[0]))  # True
    event_loop = asyncio.get_event_loop()
    results = event_loop.run_until_complete(asyncio.gather(*coroutines))  # find返回的结果保存在results
    print(results)


async def fetch():
    async with aiohttp.request('GET', 'http://www.baidu.com') as r:
        return await r.text()


def run_fetch():
    event_loop = asyncio.get_event_loop()
    results = event_loop.run_until_complete(asyncio.gather(*([fetch()] * 100)))
    print(len(results))
    event_loop.close()


if __name__ == "__main__":
    run_find()
    """
    start find(508000, 34113)
    start find(100052, 3210)
    start find(500, 3)
    end find(500, 3)
    end find(100052, 3210)
    end find(508000, 34113)
    """
    run_fetch()
    asyncio.run(run_say_after())  # 内部创建一个新的event loop,并将传入的coroutine转换为task
    """
    main started at 21:25:27
    say_after started at 21:25:27
    say_after started at 21:25:27
    hello
    say_after finished at 21:25:28
    world
    say_after finished at 21:25:30
    [3, 1]
    main finished at 21:25:30
    """
