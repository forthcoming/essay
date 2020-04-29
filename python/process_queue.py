import sys
from queue import Empty, Full
from multiprocessing import Queue,connection
from multiprocessing.reduction import ForkingPickler
from multiprocessing.context import assert_spawning


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
        self._reader, self._writer = connection.Pipe(duplex=False)  # multiprocessing.Pipe()
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
        return _ForkingPickler.loads(res)

    def put(self, obj):
        obj = _ForkingPickler.dumps(obj)
        if self._wlock is None:
            self._writer.send_bytes(obj)  # writes to a message oriented win32 pipe are atomic
        else:
            with self._wlock:
                self._writer.send_bytes(obj)
                
      
