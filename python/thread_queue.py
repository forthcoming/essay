import threading
from collections import deque
from heapq import heappush, heappop
from time import monotonic as time


__all__ = ['Empty', 'Full', 'Queue', 'PriorityQueue', 'LifoQueue', 'SimpleQueue']

class Empty(Exception):   # Exception raised by Queue.get(block=0)/get_nowait().
    pass

class Full(Exception):    # Exception raised by Queue.put(block=0)/put_nowait().
    pass

class Queue:

    def __init__(self, maxsize=0):
        self.maxsize = maxsize
        self._init(maxsize)

        # mutex must be held whenever the queue is mutating.  All methods that acquire mutex must release it before returning.
        # mutex is shared between the three conditions, so acquiring and releasing the conditions also acquires and releases mutex.
        self.mutex = threading.Lock()
        # Notify not_empty whenever an item is added to the queue; a thread waiting to get is notified then.
        self.not_empty = threading.Condition(self.mutex)
        # Notify not_full whenever an item is removed from the queue; a thread waiting to put is notified then.
        self.not_full = threading.Condition(self.mutex)
        # Notify all_tasks_done whenever the number of unfinished tasks drops to zero; thread waiting to join() is notified to resume
        self.all_tasks_done = threading.Condition(self.mutex)
        self.unfinished_tasks = 0

    def _init(self, maxsize):   # Override these methods to implement other queue organizations
        self.queue = deque()

    def _qsize(self):
        return len(self.queue)

    def _put(self, item):
        self.queue.append(item)

    def _get(self):
        return self.queue.popleft()

    def qsize(self):  # Return the approximate size of the queue (not reliable!).
        with self.mutex:
            return self._qsize()

    def put(self, item, block=True, timeout=None):
        '''
        If optional args 'block' is true and 'timeout' is None (the default), block if necessary until a free slot is available.
        If 'timeout' is a non-negative number, it blocks at most 'timeout' seconds and raises the Full exception if no free slot was available within that time.
        Otherwise ('block' is false), put an item on the queue if a free slot is immediately available, else raise the Full exception ('timeout' is ignored in that case).
        '''
        with self.not_full:
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
                    endtime = time() + timeout
                    while self._qsize() >= self.maxsize:
                        remaining = endtime - time()
                        if remaining <= 0.0:
                            raise Full
                        self.not_full.wait(remaining)
            self._put(item)
            self.unfinished_tasks += 1
            self.not_empty.notify()

    def get(self, block=True, timeout=None):
        '''
        If optional args 'block' is true and 'timeout' is None (the default),block if necessary until an item is available.
        If 'timeout' is a non-negative number, it blocks at most 'timeout' seconds and raises the Empty exception if no item was available within that time.
        Otherwise ('block' is false), return an item if one is immediately available, else raise the Empty exception ('timeout' is ignored in that case).
        '''
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
                endtime = time() + timeout
                while not self._qsize():
                    remaining = endtime - time()
                    if remaining <= 0.0:
                        raise Empty
                    self.not_empty.wait(remaining)
            item = self._get()
            self.not_full.notify()
            return item

    def task_done(self):   # 要放到任务执行完的最后一步调用,标记本次任务结束
        '''
        Indicate that a formerly enqueued task is complete.
        Used by Queue consumer threads.  For each get() used to fetch a task, a subsequent call to task_done() tells the queue that the processing on the task is complete.
        If a join() is currently blocking, it will resume when all items have been processed (meaning that a task_done() call was received for every item that had been put() into the queue).
        Raises a ValueError if called more times than there were items placed in the queue.
        '''
        with self.all_tasks_done:
            self.unfinished_tasks -= 1
            if self.unfinished_tasks == 0:
                self.all_tasks_done.notify_all()
            elif self.unfinished_tasks < 0:
                raise ValueError('task_done() called too many times')

    def join(self):  # 使用前要保证所有生产者都已完成生产任务(可通过线程join达到目的)
        '''
        Blocks until all items in the Queue have been gotten and processed.
        The count of unfinished tasks goes up whenever an item is added to the queue.
        The count goes down whenever a consumer thread calls task_done() to indicate the item was retrieved and all work on it is complete.
        When the count of unfinished tasks drops to zero, join() unblocks.
        '''
        with self.all_tasks_done:
            while self.unfinished_tasks:
                self.all_tasks_done.wait()

                
class LifoQueue(Queue):

    def _init(self, maxsize):
        self.queue = []

    def _get(self):
        return self.queue.pop()


class PriorityQueue(Queue):

    def _init(self, maxsize):
        self.queue = []

    def _put(self, item):
        heappush(self.queue, item)

    def _get(self):
        return heappop(self.queue)
