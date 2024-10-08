import threading
from collections import deque
from heapq import heappush, heappop
from time import monotonic as time

# 参考python3.11的queue.py


__all__ = ['Empty', 'Full', 'Queue', 'PriorityQueue', 'LifoQueue', 'SimpleQueue']


class Empty(Exception):  # Exception raised by Queue.get(block=0)/get_nowait().
    pass


class Full(Exception):  # Exception raised by Queue.put(block=0)/put_nowait().
    pass


class Queue:

    def __init__(self, maxsize=0):
        self.maxsize = maxsize
        self._init(maxsize)
        self.mutex = threading.Lock()  # 当队列发生变化时,必须保持互斥锁,mutex在三个conditions之间共享,因此获取和释放condition也会获取和释放mutex
        # not_empty与not_full拥有不同的_waiters,目的是把因put挂起的线程和因get挂起的线程区分开
        # Notify not_empty whenever an item is added to the queue; a thread waiting to get is notified then.
        # Notify not_full whenever an item is removed from the queue; a thread waiting to put is notified then.
        self.not_empty = threading.Condition(self.mutex)
        self.not_full = threading.Condition(self.mutex)
        self.all_tasks_done = threading.Condition(self.mutex)  # 每当未完成的任务数量降至零时通知all_tasks_done,等待join()的线程被通知恢复
        self.unfinished_tasks = 0

    def qsize(self):  # Return the approximate size of the queue (not reliable!).
        with self.mutex:
            return self._qsize()

    def task_done(self):  # 要放到任务执行完的最后一步调用,标记本次任务结束
        # 由队列消费者线程使用,对于获取任务的每个get(),随后对task_done()的调用会告诉队列该任务的处理已完成
        # 如果join()当前处于阻塞状态,它将在处理完所有项目后恢复
        with self.all_tasks_done:
            unfinished = self.unfinished_tasks - 1
            if unfinished <= 0:
                if unfinished < 0:
                    raise ValueError('task_done() called too many times')
                self.all_tasks_done.notify_all()
            self.unfinished_tasks = unfinished

    def join(self):  # 使用前要保证所有生产者都已完成生产任务(可通过线程join达到目的),阻塞直到队列中的所有项目都被获取并处理(计数为0)
        # 每当将项目添加到队列中时未完成任务的计数就会增加; 每当消费者线程调用task_done()来表明该项目已被检索时,计数就会减少
        with self.all_tasks_done:
            while self.unfinished_tasks:
                self.all_tasks_done.wait()

    def put(self, item, block=True, timeout=None):
        """
        If optional args 'block' is true and 'timeout' is None (the default), block if necessary
        until a free slot is available.If 'timeout' is a non-negative number, it blocks at most 'timeout' seconds
        and raises the Full exception if no free slot was available within that time,Otherwise ('block' is false),
        put an item on the queue if a free slot is immediately available, else raise the Full exception(忽略timeout)
        """
        with self.not_full:  # 与with self.not_empty,with self.all_tasks_done,with self.mutex等价
            if self.maxsize > 0:
                if not block:
                    if self._qsize() >= self.maxsize:
                        raise Full
                elif timeout is None:
                    while self._qsize() >= self.maxsize:
                        self.not_full.wait()
                elif timeout < 0:
                    raise ValueError("'timeout' must be a non-negative number")
                else:
                    end_time = time() + timeout
                    while self._qsize() >= self.maxsize:
                        remaining = end_time - time()
                        if remaining <= 0.0:
                            raise Full
                        self.not_full.wait(remaining)
            self._put(item)
            self.unfinished_tasks += 1
            self.not_empty.notify()

    def get(self, block=True, timeout=None):  # If block = false,如果item立即可用则返回否则引发Empty异常,此时忽略timeout
        with self.not_empty:
            if not block:
                if not self._qsize():
                    raise Empty
            elif timeout is None:
                while not self._qsize():
                    self.not_empty.wait()
            elif timeout < 0:
                raise ValueError("'timeout' must be a non-negative number")
            else:
                end_time = time() + timeout
                while not self._qsize():
                    remaining = end_time - time()
                    if remaining <= 0.0:
                        raise Empty
                    self.not_empty.wait(remaining)
            item = self._get()
            self.not_full.notify()
            return item

    # Override these methods to implement other queue organizations (e.g. stack or priority queue).
    # These will only be called with appropriate locks held
    def _init(self, maxsize):
        self.queue = deque()

    def _qsize(self):
        return len(self.queue)

    # Put a new item in the queue
    def _put(self, item):
        self.queue.append(item)

    # Get an item from the queue
    def _get(self):
        return self.queue.popleft()


class PriorityQueue(Queue):

    def _init(self, maxsize):
        self.queue = []

    def _put(self, item):
        heappush(self.queue, item)

    def _get(self):
        return heappop(self.queue)


class LifoQueue(Queue):

    def _init(self, maxsize):
        self.queue = []

    def _get(self):
        return self.queue.pop()


class SimpleQueue:
    """
    缺少如任务追踪等高级功能的简单队列
    Note: This pure Python implementation is not reentrant.while this pure Python version provides fairness
    by using a threading.Semaphore which is itself fair,being based on threading.Condition,
    """

    def __init__(self):
        self._queue = deque()
        self._count = threading.Semaphore(0)

    def put(self, item):
        self._queue.append(item)
        self._count.release()

    def get(self, block=True, timeout=None):
        if timeout is not None and timeout < 0:
            raise ValueError("'timeout' must be a non-negative number")
        if not self._count.acquire(block, timeout):
            raise Empty
        return self._queue.popleft()

    def qsize(self):
        return len(self._queue)
