from threading import Lock
from collections import deque
from itertools import islice

# 代码来自threading.py,略有改动

class _RLock:
    """
    A reentrant lock must be released by the thread that acquired it. Once a thread has acquired a reentrant lock,
    the same thread may acquire it again without blocking; the thread must release it once for each time it has acquired it.
    """

    def __init__(self):
        self._block = Lock()
        self._owner = None     # get_ident返回的线程id
        self._count = 0        # 上锁次数

    def __repr__(self):
        return "<%s %s.%s object owner=%r count=%d at %s>" % (
            "locked" if self._block.locked() else "unlocked",
            self.__class__.__module__,
            self.__class__.__qualname__,
            self._owner,
            self._count,
            hex(id(self))
        )

    def acquire(self, blocking=True, timeout=-1):
        """
        When invoked without arguments:
        if this thread already owns the lock, increment the recursion level by one, and return immediately.
        Otherwise,if another thread owns the lock, block until the lock is unlocked.
        Once the lock is unlocked (not owned by any thread), then grab ownership, set the recursion level to one, and return.
        If more than one thread is blocked waiting until the lock is unlocked, only one at a time will be able to grab ownership of the lock.
        """
        me = get_ident()
        if self._owner == me:
            self._count += 1
            return 1
        rc = self._block.acquire(blocking, timeout)  # 锁等待超时返回False并向下执行(不会抛出异常)
        if rc:
            self._owner = me
            self._count = 1
        return rc

    __enter__ = acquire

    def release(self):
        """
        If after the decrement it is zero, reset the lock to unlocked, and if any other threads are blocked waiting for the lock to become unlocked, allow exactly one of them to proceed.
        If after the decrement the recursion level is still nonzero, the lock remains locked and owned by the calling thread.
        Only call this method when the calling thread owns the lock. A RuntimeError is raised if this method is called when the lock is unlocked.
        """
        if self._owner != get_ident():
            raise RuntimeError("cannot release un-acquired lock")
        self._count -= 1
        if not count:
            self._owner = None
            self._block.release()

    def __exit__(self, t, v, tb):
        self.release()

    def _acquire_restore(self, state):     # Internal methods used by condition variables
        self._block.acquire()
        self._count, self._owner = state

    def _release_save(self):                # Internal methods used by condition variables
        if self._count == 0:
            raise RuntimeError("cannot release un-acquired lock")
        count = self._count
        self._count = 0
        owner = self._owner
        self._owner = None
        self._block.release()
        return count, owner

    def _is_owned(self):  # 线程是否拥有该锁
        return self._owner == get_ident()


class Condition:
    """
    A condition variable allows one or more threads to wait until they are notified by another thread.
    If the lock argument is given and not None, it must be a Lock or RLock object, and it is used as the underlying lock.
    Otherwise, a new RLock object is created and used as the underlying lock.
    """

    def __init__(self, lock=None):
        if lock is None:
            lock = RLock()
        self._lock = lock
        self.acquire = lock.acquire
        self.release = lock.release
        self._release_save = lock._release_save
        self._acquire_restore = lock._acquire_restore
        self._is_owned = lock._is_owned
        self._waiters = deque()

    def __enter__(self):
        return self._lock.__enter__()

    def __exit__(self, *args):
        return self._lock.__exit__(*args)

    def __repr__(self):
        return "<Condition(%s, %d)>" % (self._lock, len(self._waiters))

    def wait(self, timeout=None):  # wait等待超时返回False(不会抛出异常),线程被唤醒
        """
        Wait until notified or until a timeout occurs.
        If the calling thread has not acquired the lock when this method is called, a RuntimeError is raised.
        This method releases the underlying lock, and then blocks until it is awakened by a notify() call for the same condition variable in another thread, or until the optional timeout occurs.
        Once awakened or timed out, it re-acquires the lock and returns.
        When the timeout argument is present and not None, it should be a floating point number specifying a timeout for the operation in seconds (or fractions thereof).
        When the underlying lock is an RLock, it is not released using its release() method, since this may not actually unlock the lock when it was acquired multiple times recursively.
        Instead, an internal interface of the RLock class is used, which really unlocks it even when it has been recursively acquired several times. Another internal interface is then used to restore the recursion level when the lock is reacquired.
        """
        if not self._is_owned():
            raise RuntimeError("self.not_empty wait on un-acquired lock")
        waiter = Lock()
        waiter.acquire()
        self._waiters.append(waiter)
        saved_state = self._release_save()  # 释放self._lock锁
        gotit = False
        try:    # 再次上锁挂起线程,等待notify通知后释放锁
            if timeout is None:
                gotit = waiter.acquire()
            else:
                if timeout > 0:
                    gotit = waiter.acquire(True, timeout)
                else:
                    gotit = waiter.acquire(False)
            return gotit
        finally:  # wait超时或者notify通知
            self._acquire_restore(saved_state)
            if not gotit:
                try:
                    self._waiters.remove(waiter)
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
        for waiter in deque(islice(all_waiters, n)):
            waiter.release()
            try:
                all_waiters.remove(waiter)
            except ValueError:
                pass

    def notify_all(self):
        self.notify(len(self._waiters))
