import time
from collections import deque
from multiprocessing.dummy import Process,Condition,RLock,Lock

'''
This module is part of SQLAlchemy using RLock instead of Lock for its mutex object.
注意Condition用法
'''

__all__ = ["Empty", "Full", "Queue"]

class _Condition:   # Condition源码(稍微有精简),referer: threading.py

    def __init__(self, lock=None):
        lock = lock or RLock()
        self._lock = lock
        self.acquire = lock.acquire
        self.release = lock.release
        self._waiters = deque()
        try:
            self._is_owned = lock._is_owned # 针对递归锁Rlock(),Return True if lock is owned by current_thread.即使该线程还拥有其他锁
        except AttributeError:
            pass

    def _is_owned(self): # 针对非递归锁Lock(),应为其没有_is_owned且无法重复获取
        if self._lock.acquire(False): # 非阻塞式获取锁
            self._lock.release()
            return False
        else:
            return True
        
    def wait(self, timeout=None):
        """
        Wait until notified or until a timeout occurs.
        If the calling thread has not acquired the lock when this method is called, a RuntimeError is raised.

        This method releases the underlying lock, and then blocks until it is
        awakened by a notify() or notify_all() call for the same condition
        variable in another thread, or until the optional timeout occurs. Once
        awakened or timed out, it re-acquires the lock and returns.

        When the timeout argument is present and not None, it should be a
        floating point number specifying a timeout for the operation in seconds
        (or fractions thereof).

        When the underlying lock is an RLock, it is not released using its
        release() method, since this may not actually unlock the lock when it
        was acquired multiple times recursively. Instead, an internal interface
        of the RLock class is used, which really unlocks it even when it has
        been recursively acquired several times. Another internal interface is
        then used to restore the recursion level when the lock is reacquired.
        """
        if not self._is_owned():
            raise RuntimeError("cannot wait on un-acquired lock")
        waiter = _allocate_lock()
        waiter.acquire()
        self._waiters.append(waiter)  # 注意
        self._lock.release()
        gotit = False
        try:    # restore state no matter what (e.g., KeyboardInterrupt)
            if timeout is None:
                waiter.acquire()
                gotit = True
            else:
                if timeout > 0:
                    gotit = waiter.acquire(True, timeout)
                else:
                    gotit = waiter.acquire(False)
            return gotit
        finally:
            self._lock.acquire()
            if not gotit:
                try:
                    self._waiters.remove(waiter) # 注意
                except ValueError:
                    pass

    def notify(self, n=1):
        """
        Wake up one or more threads waiting on this condition, if any.
        If the calling thread has not acquired the lock when this method is called, a RuntimeError is raised.
        This method wakes up at most n of the threads waiting for the condition variable; it is a no-op if no threads are waiting.
        """
        if not self._is_owned():
            raise RuntimeError("cannot notify on un-acquired lock")
        all_waiters = self._waiters
        waiters_to_notify = _deque(_islice(all_waiters, n))
        if not waiters_to_notify:
            return
        for waiter in waiters_to_notify:
            waiter.release()
            try:
                all_waiters.remove(waiter)
            except ValueError:
                pass

    def notify_all(self):
        """
        Wake up all threads waiting on this condition.
        If the calling thread has not acquired the lock when this method is called, a RuntimeError is raised.
        """
        self.notify(len(self._waiters))

class Empty(Exception):
    "Exception raised by Queue.get(block=0)."
    pass

class Full(Exception):
    "Exception raised by Queue.put(block=0)."
    pass

class Queue:

    def __init__(self, maxsize=0, use_lifo=False):
        """
        refer: https://github.com/sqlalchemy/sqlalchemy/blob/master/lib/sqlalchemy/util/queue.py
        If `maxsize` is <= 0, the queue size is infinite.
        If `use_lifo` is True, this Queue acts like a Stack (LIFO).
        注意:
        self.not_empty和self.not_full内部使用的是同一把锁,都是self.mutex,因此self.not_empty.acquire()和self.not_full.acquire()互斥,但他们拥有不同的_waiters
        目的就是把因put挂起的线程和因get挂起的线程区分开
        """
        self.maxsize = maxsize
        self.queue = deque()
        self.mutex = RLock()
        self.not_empty = Condition(self.mutex) # Notify not_empty whenever an item is added to the queue; a thread waiting to get is notified then.
        self.not_full = Condition(self.mutex)  # Notify not_full whenever an item is removed from the queue; a thread waiting to put is notified then.
        self.use_lifo = use_lifo               # If this queue uses LIFO or FIFO

    def _empty(self):
        return not self.queue

    def _full(self):
        return self.maxsize > 0 and len(self.queue) == self.maxsize

    def qsize(self): # Return the approximate size of the queue (not reliable!).
        with self.mutex:
            return len(self.queue)
        
    def empty(self): # Return True if the queue is empty, False otherwise (not reliable!).
        with self.mutex:
            return self._empty()  # not self.queue

    def full(self): # Return True if the queue is full, False otherwise (not reliable!).
        with self.mutex:
            return self._full()  # self.maxsize > 0 and len(self.queue) == self.maxsize

    def put(self, item, block=True, timeout=None):
        """
        Put an item into the queue.
        If optional args `block` is True and `timeout` is None (the default), block if necessary until a free slot is available.
        If `timeout` is a positive number, it blocks at most `timeout` seconds and raises the ``Full`` exception if no free slot was available within that time.
        Otherwise (`block` is false), put an item on the queue if a free slot is immediately available, else raise the ``Full`` exception(`timeout` is ignored in that case).
        """
        with self.mutex:  # 即使里面抛出异常,也会执行release释放锁
            if not block:
                if self._full():
                    raise Full
            elif timeout is None:
                while self._full():
                    self.not_full.wait()
            else:
                if timeout < 0:
                    raise ValueError("'timeout' must be a positive number")
                end_time = time.time() + timeout
                while self._full():
                    remaining = end_time - time.time()
                    if remaining <= .0:
                        raise Full
                    self.not_full.wait(remaining)
                    # wait([timeout]): 线程挂起,直到收到notify通知或者超时(可选,浮点数,单位秒)才会被唤醒继续运行
                    # wait必须在已获得锁前提下才能调用,会释放锁,直至该线程被notify()、notify_all()或者超时线程唤醒又重新获得锁
            self.queue.append(item)
            self.not_empty.notify()
            # notify和notify_all并不会释放锁,需要线程本身来释放(wait或者release),但必须在已获得锁前提下才能调用
            # this means that the thread or threads awakened will not return from their wait() call immediately, but only when the thread that called notify() or notify_all() finally relinquishes ownership of the lock.

    def get(self, block=True, timeout=None):
        """
        Remove and return an item from the queue.
        If optional args `block` is True and `timeout` is None (the default), block if necessary until an item is available.
        If `timeout` is a positive number, it blocks at most `timeout` seconds and raises the ``Empty`` exception if no item was available within that time.
        Otherwise (`block` is false), return an item if one is immediately available, else raise the ``Empty`` exception (`timeout` is ignored in that case).
        """
        with self.mutex:
            if not block:
                if self._empty():
                    raise Empty
            elif timeout is None:
                while self._empty():
                    self.not_empty.wait()
            else:
                if timeout < 0:
                    raise ValueError("'timeout' must be a positive number")
                end_time = time.time() + timeout
                while self._empty():
                    remaining = end_time - time.time()
                    if remaining <= .0:
                        raise Empty
                    self.not_empty.wait(remaining)
            item = self.queue.pop() if self.use_lifo else self.queue.popleft()
            self.not_full.notify()
            return item

# from .base import Pool
# from .. import util
# class QueuePool(Pool):  # sqlalchemy连接池源码(稍微有精简),refer: impl.py
#     def __init__(self, creator, pool_size=5, max_overflow=10, timeout=30, use_lifo=False, **kw):
#         """
#         pool_size:
#         Note that the pool begins with no connections; once this number of connections is requested, that number of connections will remain.
#         pool_size can be set to 0 to indicate no size limit; to disable pooling, use a NullPool instead.
#
#         max_overflow:
#         When the number of checked-out connections reaches the size set in pool_size,additional connections will be returned up to this limit.
#         When those additional connections are returned to the pool,they are disconnected and discarded.
#         the total number of simultaneous connections the pool will allow is pool_size + max_overflow,and the total number of "sleeping" connections the pool will allow is pool_size.
#         max_overflow can be set to -1 to indicate no overflow limit;
#
#         kw:
#         Other keyword arguments including Pool.recycle,Pool.echo,Pool.reset_on_return and others are passed to the class Pool constructor.
#         """
#         Pool.__init__(self, creator, **kw)
#         self._pool = Queue(pool_size, use_lifo=use_lifo)
#         self._overflow = -pool_size  # 注意
#         self._max_overflow = max_overflow
#         self._timeout = timeout
#         self._overflow_lock = Lock()
#
#     def _do_return_conn(self, conn): # 释放连接调用(连接资源归还至连接池不会被调用)
#         try:
#             self._pool.put(conn, False)
#         except Full:
#             try:
#                 conn.close()
#             finally:
#                 self._dec_overflow()  # 注意
#
#     def _do_get(self):  # 获取连接调用
#         use_overflow = self._max_overflow > -1
#
#         try:
#             wait = use_overflow and self._overflow >= self._max_overflow  # 如果使用max_overflow并且连接数已达上限
#             return self._pool.get(wait, self._timeout)  # 获取连接池中的连接将被阻塞
#         except Empty:
#             # don't do things inside of "except Empty", because when we say we timed out or can't connect and raise,
#             # Python 3 tells people the real error is queue.Empty which it isn't.
#             pass
#         if use_overflow and self._overflow >= self._max_overflow:
#             if not wait:
#                 return self._do_get()
#             else:
#                 raise TimeoutError(
#                     "QueuePool limit of overflow {} reached, connection timed out, timeout {}".format(self.overflow(),
#                                                                                                       self._timeout))
#
#         if self._inc_overflow():
#             try:
#                 return self._create_connection()
#             except:
#                 with util.safe_reraise():
#                     self._dec_overflow()
#         else:
#             return self._do_get()
#
#     def _inc_overflow(self):
#         if self._max_overflow == -1:
#             self._overflow += 1
#             return True
#         with self._overflow_lock:
#             if self._overflow < self._max_overflow:
#                 self._overflow += 1
#                 return True
#             else:
#                 return False
#
#     def _dec_overflow(self):
#         if self._max_overflow == -1:
#             self._overflow -= 1
#             return True
#         with self._overflow_lock:
#             self._overflow -= 1
#             return True
#
#     def recreate(self):
#         self.logger.info("Pool recreating")
#         return self.__class__(self._creator, pool_size=self._pool.maxsize, max_overflow=self._max_overflow,
#             timeout=self._timeout, recycle=self._recycle, echo=self.echo, logging_name=self._orig_logging_name,
#             use_threadlocal=self._use_threadlocal, reset_on_return=self._reset_on_return, _dispatch=self.dispatch,
#             dialect=self._dialect, )
#
#     def dispose(self):
#         while True:
#             try:
#                 conn = self._pool.get(False)
#                 conn.close()
#             except Empty:
#                 break
#
#         self._overflow = 0 - self.size()
#         self.logger.info("Pool disposed. %s", self.status())
#
#     def status(self):
#         return "Pool size: {}  Connections in pool: {} Current Overflow: {} Current Checked out connections: {}".format(
#             self.size(), self.checkedin(), self.overflow(), self.checkedout())
#
#     def size(self):
#         return self._pool.maxsize     # 连接池大小
#
#     def checkedin(self):
#         return self._pool.qsize()    # 连接池中的连接数
#
#     def overflow(self):
#         return self._overflow
#
#     def checkedout(self):
#         return self._overflow + self._pool.maxsize - self._pool.qsize() # 现有已申请连接总数-池子中的连接数
    
    
if __name__=='__main__':
    queue = Queue(4)
    threadings = [Process(target=queue.get, args=()), Process(target=queue.put, args=(5,))]
    for thread in threadings:
        thread.start()
    for thread in threadings:
        thread.join()