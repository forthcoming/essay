from threading import Lock
from collections import deque
from itertools import islice
from time import monotonic

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

        
class Semaphore:
    """
    信号量的主要用途是控制线程并发量(类似线程池),初始值为1的信号量为互斥量,其实就是线程锁
    信号量用的是非重入锁,但信号量本身可重入
    Semaphores manage a counter representing the number of release() calls minus the number of acquire() calls, plus an initial value.
    The acquire() method blocks if necessary until it can return without making the counter negative. If not given, value defaults to 1.
    
    ######################## 死锁试例 ########################
    semaphore = Semaphore(2)
    def work(idx): 
        with semaphore:
            time.sleep(.1)
            with semaphore:
                print('working in {}'.format(idx))
    def work_v1(idx):
        with semaphore:
            with semaphore:
                with semaphore:
                    print('working in {}'.format(idx))
    threads = [Thread(target=work,args=(idx,)) for idx in range(5)]  # or work_v1
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    """

    def __init__(self, value=1):
        if value < 0:
            raise ValueError("semaphore initial value must be >= 0")
        self._cond = Condition(Lock())
        self._value = value

    def acquire(self, blocking=True, timeout=None):
        """
        Acquire a semaphore, decrementing the internal counter by one.
        When invoked without arguments: if the internal counter is larger than zero on entry, decrement it by one and return immediately.
        If it is zero on entry, block, waiting until some other thread has called release() to make it larger than zero.
        This is done with proper interlocking so that if multiple acquire() calls are blocked,release() will wake exactly one of them up.
        The implementation may pick one at random, so the order in which blocked threads are awakened should not be relied on. There is no return value in this case.
        When invoked with blocking set to true, do the same thing as when called without arguments, and return true.
        When invoked with blocking set to false, do not block. If a call without an argument would block, return false immediately;otherwise, do the same thing as when called without arguments, and return true.
        When invoked with a timeout other than None, it will block for at most timeout seconds.If acquire does not complete successfully in that interval, return false.  Return true otherwise.
        """
        if not blocking and timeout is not None:
            raise ValueError("can't specify timeout for non-blocking acquire")
        rc = False
        endtime = None
        with self._cond:
            while self._value == 0:
                if not blocking:
                    break
                if timeout is not None:
                    if endtime is None:
                        endtime = monotonic() + timeout  # monotonic单调时间,它指的是系统启动以后流逝的时间,不区分线程进程,按调用顺序递增
                    else:
                        timeout = endtime - monotonic()
                        if timeout <= 0:
                            break
                self._cond.wait(timeout)
            else:
                self._value -= 1
                rc = True
        return rc

    __enter__ = acquire

    def release(self):
        """
        Release a semaphore, incrementing the internal counter by one.
        When the counter is zero on entry and another thread is waiting for it to become larger than zero again, wake up that thread.
        """
        with self._cond:
            self._value += 1
            self._cond.notify()

    def __exit__(self, t, v, tb):
        self.release()

        
class BoundedSemaphore(Semaphore):  # 建议使用BoundedSemaphore代替Semaphore,应为他会对release做检测,减小程序bug
    """
    A bounded semaphore checks to make sure its current value doesn't exceed its initial value. If it does, ValueError is raised.
    If the semaphore is released too many times it's a sign of a bug. If not given, value defaults to 1.
    Like regular semaphores, bounded semaphores manage a counter representing the number of release() calls minus the number of acquire() calls, plus an initial value.
    The acquire() method blocks if necessary until it can return without making the counter negative. If not given, value defaults to 1.
    """

    def __init__(self, value=1):
        super().__init__(value)
        self._initial_value = value

    def release(self):
        """
        When the counter is zero on entry and another thread is waiting for it to become larger than zero again, wake up that thread.
        If the number of releases exceeds the number of acquires, raise a ValueError.
        """
        with self._cond:
            if self._value >= self._initial_value:
                raise ValueError("Semaphore released too many times")
            self._value += 1
            self._cond.notify()
            

class Event:
    """
    Events manage a flag that can be set to true with the set() method and reset to false with the clear() method.
    The wait() method blocks until the flag is true.  The flag is initially false.
    """

    def __init__(self):
        self._cond = Condition(Lock())
        self._flag = False

    def _reset_internal_locks(self):
        self._cond.__init__(Lock())     # private!  called by Thread._reset_internal_locks by _after_fork()

    def is_set(self):  # Return true if and only if the internal flag is true.
        return self._flag

    def set(self):   # All threads waiting for it to become true are awakened. Threads that call wait() once the flag is true will not block at all.
        with self._cond:
            self._flag = True
            self._cond.notify_all()

    def clear(self):  # Subsequently, threads calling wait() will block until set() is called to set the internal flag to true again.
        with self._cond:
            self._flag = False

    def wait(self, timeout=None):
        """
        Block until the internal flag is true.
        If the internal flag is true on entry, return immediately. Otherwise,block until another thread calls set() to set the flag to true, or until the optional timeout occurs.
        When the timeout argument is present and not None, it should be a floating point number specifying a timeout for the operation in seconds(or fractions thereof).
        This method returns the internal flag on exit, so it will always return True except if a timeout is given and the operation times out.
        """
        with self._cond:
            signaled = self._flag
            if not signaled:
                signaled = self._cond.wait(timeout)
            return signaled
        
        
class BrokenBarrierError(RuntimeError):
    pass

class Barrier:
    """
    We maintain two main states, 'filling' and 'draining' enabling the barrier to be cyclic.  Threads are not allowed into it until it has fully drained since the previous cycle.  
    In addition, a 'resetting' state exists which is similar to 'draining' except that threads leave with a BrokenBarrierError,and a 'broken' state in which all threads get the exception.
    Useful for synchronizing a fixed number of threads at known synchronization points.
    Threads block on 'wait()' and are simultaneously awoken once they have all made that call.
    多线程Barrier会设置一个线程障碍数量parties,如果等待的线程数量没有达到障碍数量parties,所有线程会处于阻塞状态,当等待的线程到达了这个数量就会唤醒所有的等待线程
    """

    def __init__(self, parties, action=None, timeout=None):
        """
        'action' is a callable which, when supplied, will be called by one of the threads after they have all entered the barrier and just prior to releasing them all.
        If a 'timeout' is provided, it is used as the default for all subsequent 'wait()' calls.
        """
        self._cond = Condition(Lock())
        self._action = action
        self._timeout = timeout
        self._parties = parties  # the number of threads required to trip the barrier.
        self._state = 0          # 0 filling, 1, draining, -1 resetting, -2 broken
        self._count = 0          # the number of threads currently waiting at the barrier.

    @property
    def parties(self):
        return self._parties

    @property
    def n_waiting(self):
        if self._state == 0:   # We don't need synchronization here since this is an ephemeral result anyway.  It returns the correct value in the steady state.
            return self._count
        return 0

    @property
    def broken(self):  # Return True if the barrier is in a broken state.
        return self._state == -2

    def _enter(self):      # Block until the barrier is ready for us, or raise an exception if it is broken.
        while self._state in (-1, 1):  # It is draining or resetting, wait until done
            self._cond.wait()
        if self._state < 0:            # see if the barrier is in a broken state
            raise BrokenBarrierError
        assert self._state == 0

    def _release(self):
        try:
            if self._action:      # Optionally run the 'action' and release the threads waiting in the barrier.
                self._action()
            self._state = 1       # enter draining state
            self._cond.notify_all()
        except:
            self._break()         # an exception during the _action handler.  Break and reraise
            raise

    def _break(self):  # An internal error was detected.  The barrier is set to a broken state all parties awakened.
        self._state = -2
        self._cond.notify_all()

    def abort(self):  # Useful in case of error.  Any currently waiting threads and threads attempting to 'wait()' will have BrokenBarrierError raised.
        with self._cond:
            self._break()

    def wait(self, timeout=None):
        """
        如果等待超时,障碍将进入断开状态,如果在线程等待期间障碍断开或重置,此方法会引发BrokenBarrierError错误
        When the specified number of threads have started waiting, they are all simultaneously awoken.
        If an 'action' was provided for the barrier, one of the threads will have executed that callback prior to returning.
        Returns an individual index number from 0 to 'parties-1'.
        """
        if timeout is None:
            timeout = self._timeout
        with self._cond:
            self._enter() # Block while the barrier drains.
            index = self._count
            self._count += 1
            try:
                if index + 1 == self._parties:
                    self._release()
                else:
                    self._wait(timeout)       # We wait until someone releases us
                return index
            finally:
                self._count -= 1
                self._exit()     # Wake up any threads waiting for barrier to drain.

    def _wait(self, timeout):    # Wait in the barrier until we are released.  Raise an exception if the barrier is reset or broken.
        if not self._cond.wait_for(lambda : self._state != 0, timeout):
            #timed out.  Break the barrier
            self._break()
            raise BrokenBarrierError
        if self._state < 0:
            raise BrokenBarrierError
        assert self._state == 1

    def _exit(self):      # If we are the last thread to exit the barrier, signal any threads waiting for the barrier to drain.
        if self._count == 0:
            if self._state in (-1, 1):
                self._state = 0
                self._cond.notify_all()

    def reset(self):    # Any threads currently waiting will get the BrokenBarrier exception raised.
        with self._cond:
            if self._count > 0:
                if self._state in (0,-2):
                    self._state = -1
            else:
                self._state = 0
            self._cond.notify_all()
