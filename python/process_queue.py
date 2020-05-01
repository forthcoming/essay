__all__ = ['Queue', 'SimpleQueue', 'JoinableQueue']

import sys, os, threading, collections, time, weakref, errno, traceback, _multiprocessing
from queue import Empty, Full
from multiprocessing import Queue,connection
from multiprocessing.reduction import ForkingPickler
from multiprocessing.context import assert_spawning
from multiprocessing.util import debug, info, Finalize, register_after_fork, is_exiting


class Queue:
    
    def __init__(self, maxsize=0, *, ctx):
        if maxsize <= 0:
            maxsize = _multiprocessing.SemLock.SEM_VALUE_MAX
        self._maxsize = maxsize
        self._reader, self._writer = connection.Pipe(duplex=False)
        self._rlock = ctx.Lock()
        self._wlock = None if sys.platform == 'win32' else ctx.Lock()
        self._opid = os.getpid()
        self._sem = ctx.BoundedSemaphore(maxsize)
        self._ignore_epipe = False          # For use by concurrent.futures
        self._after_fork()
        if sys.platform != 'win32':
            register_after_fork(self, Queue._after_fork)

    def _after_fork(self):   # Queue被传到其他进程之后调用,
        debug('Queue._after_fork()')
        self._notempty = threading.Condition(threading.Lock())
        self._buffer = collections.deque()
        self._thread = None     # 同步数据的线程
        self._jointhread = None
        self._joincancelled = False
        self._closed = False
        self._close = None
        self._send_bytes = self._writer.send_bytes  # _send_bytes,_recv_bytes,_poll为什么需要重新赋值
        self._recv_bytes = self._reader.recv_bytes
        self._poll = self._reader.poll

    def qsize(self):   # Raises NotImplementedError on Mac OSX because of broken sem_getvalue()
        return self._maxsize - self._sem._semlock._get_value()

    def empty(self):
        return not self._poll()

    def full(self):
        return self._sem._semlock._is_zero()

    def _start_thread(self):   # Start thread which transfers data from buffer to pipe
        self._buffer.clear()
        self._thread = threading.Thread(
            target=Queue._feed,
            args=(self._buffer, self._notempty, self._send_bytes,self._wlock, self._writer.close, self._ignore_epipe, self._sem),
            name='QueueFeederThread',
            daemon=True,
        )
        self._thread.start()
        if not self._joincancelled:
            self._jointhread = Finalize(self._thread, Queue._finalize_join,[weakref.ref(self._thread)],exitpriority=-5)
        self._close = Finalize(self, Queue._finalize_close,[self._buffer, self._notempty],exitpriority=10)    # Send sentinel to the thread queue object when garbage collected

    @staticmethod
    def _feed(buffer, notempty, send_bytes, writelock, close, ignore_epipe, queue_sem):
        while True:
            try:
                with notempty:
                    if not buffer:
                        notempty.wait()
                try:
                    while True:
                        obj = buffer.popleft()
                        if obj is _sentinel:
                            debug('feeder thread got sentinel -- exiting')
                            close()
                            return
                        obj = ForkingPickler.dumps(obj)
                        if sys.platform == 'win32':
                            send_bytes(obj)
                        else:
                            with writelock:
                                send_bytes(obj)
                except IndexError:  # 当buffer为空时popleft会抛出异常
                    pass
            except Exception as e:
                if ignore_epipe and getattr(e, 'errno', 0) == errno.EPIPE:
                    return
                # Since this runs in a daemon thread the resources it uses may be become unusable while the process is cleaning up.
                # We ignore errors which happen after the process has started to cleanup.
                if is_exiting():
                    info('error in queue thread: %s', e)
                    return
                else:
                    # Since the object has not been sent in the queue, we need to decrease the size of the queue.
                    # The error acts as if the object had been silently removed from the queue and this step is necessary to have a properly working queue.
                    queue_sem.release()
                    traceback.print_exc()

    def put(self, obj, block=True, timeout=None):
        assert not self._closed, "Queue {0!r} has been closed".format(self)
        if not self._sem.acquire(block, timeout):
            raise Full
        with self._notempty:
            if self._thread is None:
                self._start_thread()
            self._buffer.append(obj)
            self._notempty.notify()

    def get(self, block=True, timeout=None):
        if block and timeout is None:
            with self._rlock:
                res = self._recv_bytes()
            self._sem.release()
        else:
            if block:
                deadline = time.monotonic() + timeout
            if not self._rlock.acquire(block, timeout):
                raise Empty
            try:
                if block:
                    timeout = deadline - time.monotonic()  # 减掉获取进程锁_rlock耗时
                    if not self._poll(timeout):
                        raise Empty
                elif not self._poll():
                    raise Empty
                res = self._recv_bytes()
                self._sem.release()
            finally:
                self._rlock.release()
        return ForkingPickler.loads(res)

    def close(self):
        self._closed = True
        try:
            self._reader.close()
        finally:
            close = self._close
            if close:
                self._close = None
                close()

    def __getstate__(self):
        context.assert_spawning(self)
        return self._ignore_epipe, self._maxsize, self._reader, self._writer,self._rlock, self._wlock, self._sem, self._opid

    def __setstate__(self, state):
        self._ignore_epipe, self._maxsize, self._reader, self._writer,self._rlock, self._wlock, self._sem, self._opid = state
        self._after_fork()

    def join_thread(self):
        debug('Queue.join_thread()')
        assert self._closed, "Queue {0!r} not closed".format(self)
        if self._jointhread:
            self._jointhread()

    def cancel_join_thread(self):
        debug('Queue.cancel_join_thread()')
        self._joincancelled = True
        try:
            self._jointhread.cancel()
        except AttributeError:
            pass

    @staticmethod
    def _finalize_join(twr):
        debug('joining queue thread')
        thread = twr()
        if thread is not None:
            thread.join()
            debug('... queue thread joined')
        else:
            debug('... queue thread already dead')

    @staticmethod
    def _finalize_close(buffer, notempty):
        debug('telling queue thread to quit')
        with notempty:
            buffer.append(_sentinel)
            notempty.notify()
     

class JoinableQueue(Queue):

    def __init__(self, maxsize=0, *, ctx):
        super().__init__(maxsize, ctx=ctx)
        self._unfinished_tasks = ctx.Semaphore(0)
        self._cond = ctx.Condition()

    def __getstate__(self):
        return Queue.__getstate__(self) + (self._cond, self._unfinished_tasks)

    def __setstate__(self, state):
        Queue.__setstate__(self, state[:-2])
        self._cond, self._unfinished_tasks = state[-2:]
        
    def put(self, obj, block=True, timeout=None):
        assert not self._closed, "Queue {0!r} is closed".format(self)
        if not self._sem.acquire(block, timeout):
            raise Full

        with self._notempty, self._cond:
            if self._thread is None:
                self._start_thread()
            self._buffer.append(obj)
            self._unfinished_tasks.release()
            self._notempty.notify()

    def task_done(self):
        with self._cond:
            if not self._unfinished_tasks.acquire(False):
                raise ValueError('task_done() called too many times')
            if self._unfinished_tasks._semlock._is_zero():
                self._cond.notify_all()

    def join(self):
        with self._cond:
            if not self._unfinished_tasks._semlock._is_zero():
                self._cond.wait()


class SimpleQueue:
    '''
    from multiprocessing import SimpleQueue
    simple_queue = SimpleQueue()
    执行multiprocessing/__init__.py把context.py中的SimpleQueue导进来,如下
    def SimpleQueue(self):
        from .queues import SimpleQueue
        return SimpleQueue(ctx=self.get_context())
    '''
    def __init__(self, *, ctx):  # *是命名关键字参数用法
        self._reader, self._writer = connection.Pipe(duplex=False)  # multiprocessing.Pipe(),说明管道也可以多进程传递,但同时读or同时写可能会出错,所以要加锁(待验证)
        self._poll = self._reader.poll
        self._rlock = ctx.Lock()                                    # multiprocessing.Lock()
        self._wlock = None if sys.platform == 'win32' else ctx.Lock()

    def __getstate__(self):
        assert_spawning(self)
        return self._reader, self._writer, self._rlock, self._wlock

    def __setstate__(self, state):
        self._reader, self._writer, self._rlock, self._wlock = state
        self._poll = self._reader.poll

    def empty(self):
        return not self._poll()

    def get(self):
        with self._rlock:
            res = self._reader.recv_bytes()
        return ForkingPickler.loads(res)

    def put(self, obj):
        obj = ForkingPickler.dumps(obj)
        if self._wlock is None:
            self._writer.send_bytes(obj)  # writes to a message oriented win32 pipe are atomic
        else:
            with self._wlock:
                self._writer.send_bytes(obj)
                
      
