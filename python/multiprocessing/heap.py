# Module which supports allocation of memory from an mmap
import bisect, mmap,os, sys, tempfile, threading
from collections import defaultdict
from multiprocessing import util

__all__ = ['BufferWrapper']

class Arena:  # Inheritable class which wraps an mmap, and from which blocks can be allocated

    def __init__(self, size, fd=-1):
        self.size = size
        self.fd = fd
        if fd == -1:
            '''
            User-callable function to create and return a unique temporary file.  
            The return value is a pair (fd, name) where fd is the file descriptor returned by os.open, and name is the filename.
            If 'prefix' is not None, the file name will begin with that prefix,otherwise a default prefix is used.
            If 'dir' is not None, the file will be created in that directory,otherwise a default directory is used.
            If 'text' is specified and true, the file is opened in text mode.  Else (the default) the file is opened in binary mode. On some operating systems, this makes no difference.
            The file is readable and writable only by the creating user ID.The file descriptor is not inherited by children of this process.
            '''
            self.fd, name = tempfile.mkstemp(prefix=f'pym-{os.getpid()}-')
            os.unlink(name)  # 删除临时文件
            util.Finalize(self, os.close, (self.fd,))  # os.close: Close a file descriptor,这里没看懂
            os.ftruncate(self.fd, size)  # Truncate a file, specified by file descriptor, to a specific length.
        self.buffer = mmap.mmap(self.fd, self.size)

class Heap:

    _alignment = 8     # Minimum malloc() alignment
    _DISCARD_FREE_SPACE_LARGER_THAN = 4 * 1024 ** 2  # 4 MB
    _DOUBLE_ARENA_SIZE_UNTIL = 4 * 1024 ** 2

    def __init__(self, size=mmap.PAGESIZE):
        self._lengths = []                         # A sorted list of available block sizes in arenas,对应self._len_to_seq的key
        self._len_to_seq = {}                      # key是申请但未使用的的block长度,value是该长度block(arena, real_stop, stop)对象组成的数组
        self._start_to_block = {}                  # key是(arena, real_stop),value是block(arena, real_stop, stop)
        self._stop_to_block = {}                   # key是(arena, stop),value是block(arena, real_stop, stop)

        self._arenas = []                          # 申请内存得到的arena对象
        self._allocated_blocks = defaultdict(set)  # key是arena,value是(start, real_stop)构成的集合,存放已分配的内存
        self._pending_free_blocks = []             # 待释放的block(arena, start, real_stop)

        self._lock = threading.Lock()
        self._size = size                          # Current arena allocation size
        self._n_mallocs = 0                        # 统计用
        self._n_frees = 0                          # 统计用
        self._lastpid = os.getpid()                # 貌似要放到最后

    @staticmethod
    def _roundup(n, alignment):
        # alignment must be a power of 2
        mask = alignment - 1
        return (n + mask) & ~mask  # 相当于 (n + mask) // alignment * alignment

    def malloc(self, size):  # return a block of right size (possibly rounded up)
        if size < 0:
            raise ValueError("Size {0:n} out of range".format(size))
        if sys.maxsize <= size:
            raise OverflowError("Size {0:n} too large".format(size))
        if os.getpid() != self._lastpid:  # reinitialize after fork,快进程创建不同内存变量时会触发
            self.__init__()
        with self._lock:
            self._n_mallocs += 1
            # allow pending blocks to be marked available
            self._free_pending_blocks()
            size = self._roundup(max(size, 1), self._alignment)
            arena, start, stop = self._malloc(size)
            real_stop = start + size
            if real_stop < stop:  # 申请多余的空间释放掉(real_stop可能等于stop)
                # if the returned block is larger than necessary, mark the remainder available
                self._add_free_block((arena, real_stop, stop))
            self._allocated_blocks[arena].add((start, real_stop))
            return arena, start, real_stop

    def _free_pending_blocks(self):
        # Free all the blocks in the pending list - called with the lock held.
        while True:
            try:
                block = self._pending_free_blocks.pop()
            except IndexError:
                break
            self._add_free_block(block)
            self._remove_allocated_block(block)

    def _add_free_block(self, block):
        # make block available and try to merge with its neighbours in the arena
        arena, start, stop = block

        try:
            prev_block = self._stop_to_block[(arena, start)]
        except KeyError:
            pass
        else:
            start, _ = self._absorb(prev_block)

        try:
            next_block = self._start_to_block[(arena, stop)]
        except KeyError:
            pass
        else:
            _, stop = self._absorb(next_block)

        block = (arena, start, stop)
        length = stop - start

        try:
            self._len_to_seq[length].append(block)
        except KeyError:
            self._len_to_seq[length] = [block]
            bisect.insort(self._lengths, length)

        self._start_to_block[(arena, start)] = block
        self._stop_to_block[(arena, stop)] = block

    def _absorb(self, block):
        # deregister this block so it can be merged with a neighbour, 只能针对相同的arena做合并操作(同一个arena可能被多个Value或Array对象使用,当他们被释放时, 需要重新合并)
        arena, start, stop = block
        del self._start_to_block[(arena, start)]    # 销毁键值对
        del self._stop_to_block[(arena, stop)]

        length = stop - start
        seq = self._len_to_seq[length]
        seq.remove(block)
        if not seq:
            del self._len_to_seq[length]
            self._lengths.remove(length)
        return start, stop

    def _remove_allocated_block(self, block):
        arena, start, stop = block
        blocks = self._allocated_blocks[arena]
        blocks.remove((start, stop))
        if not blocks:  # Arena is entirely free, discard it from this process,关键!!!
            self._discard_arena(arena)

    def _new_arena(self, size):  # 每次新申请内存都会比上次申请的内存要大,内存大小按倍数递增
        # Create a new arena with at least the given *size*
        length = self._roundup(max(self._size, size), mmap.PAGESIZE)
        # We carve larger and larger arenas, for efficiency, until we reach a large-ish size (roughly L3 cache-sized)
        if self._size < self._DOUBLE_ARENA_SIZE_UNTIL:
            self._size *= 2
        print(f'allocating a new mmap of length {length}')
        arena = Arena(length)
        self._arenas.append(arena)
        return arena, 0, length

    def _discard_arena(self, arena):
        # Possibly delete the given (unused) arena
        length = arena.size
        # Reusing an existing arena is faster than creating a new one, so we only reclaim space if it's large enough.
        if length < self._DISCARD_FREE_SPACE_LARGER_THAN:
            return
        ############################################################################################
        # 删除关于arena的所有引用,彻底销毁arena,触发Arena注册的os.close函数回收内存
        blocks = self._allocated_blocks.pop(arena)  # 当value为空时对应的key自动被删除
        assert not blocks
        del self._start_to_block[(arena, 0)]
        del self._stop_to_block[(arena, length)]
        self._arenas.remove(arena)
        seq = self._len_to_seq[length]
        seq.remove((arena, 0, length))
        ############################################################################################
        if not seq:
            del self._len_to_seq[length]
            self._lengths.remove(length)

    def _malloc(self, size):
        # returns a large enough block -- it might be much larger
        i = bisect.bisect_left(self._lengths, size)
        if i == len(self._lengths):   # size是self._lengths中的最大值
            return self._new_arena(size)
        else:
            length = self._lengths[i]
            seq = self._len_to_seq[length]
            block = seq.pop()
            if not seq:
                del self._len_to_seq[length], self._lengths[i]

        (arena, start, stop) = block
        del self._start_to_block[(arena, start)]
        del self._stop_to_block[(arena, stop)]
        return block

    def free(self, block):
        # free a block returned by malloc()
        # Since free() can be called asynchronously by the GC, it could happen
        # that it's called while self._lock is held: in that case,
        # self._lock.acquire() would deadlock (issue #12352). To avoid that, a
        # trylock is used instead, and if the lock can't be acquired
        # immediately, the block is added to a list of blocks to be freed
        # synchronously sometimes later from malloc() or free(), by calling
        # _free_pending_blocks() (appending and retrieving from a list is not
        # strictly thread-safe but under CPython it's atomic thanks to the GIL).
        if os.getpid() != self._lastpid:
            raise ValueError("My pid ({0:n}) is not last pid {1:n}".format(os.getpid(),self._lastpid))
        if not self._lock.acquire(False):
            # can't acquire the lock right now, add the block to the list of
            # pending blocks to free
            self._pending_free_blocks.append(block)
        else:
            # we hold the lock
            try:
                self._n_frees += 1
                self._free_pending_blocks()
                self._add_free_block(block)
                self._remove_allocated_block(block)
            finally:
                self._lock.release()

class BufferWrapper:
    # Class wrapping a block allocated out of a Heap -- can be inherited by child process
    _heap = Heap()

    def __init__(self, size):  # 对应c语言类型需要占用的字节数
        if size < 0:
            raise ValueError("Size {0:n} out of range".format(size))
        if sys.maxsize <= size:
            raise OverflowError("Size {0:n} too large".format(size))
        block = BufferWrapper._heap.malloc(size)
        self._state = (block, size)
        util.Finalize(self, BufferWrapper._heap.free, args=(block,))

    def create_memoryview(self):
        (arena, start, stop), size = self._state  # stop-start等于_roundup(size,_alignment),此处_alignment=8
        return memoryview(arena.buffer)[start:start+size]
