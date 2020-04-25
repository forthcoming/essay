from threading import Lock
from collections import deque

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
        rc = self._block.acquire(blocking, timeout)
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
