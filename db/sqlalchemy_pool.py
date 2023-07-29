import time
from multiprocessing.dummy import Lock
from .base import Pool
from .. import util
from ..util import queue as sqla_queue

'''
sqla_queue.Queue跟queue.Queue基本一致,但前者用的是可重入锁
refer: https://github.com/sqlalchemy/sqlalchemy/blob/master/lib/sqlalchemy/util/queue.py
'''


class QueuePool(Pool):  # sqlalchemy连接池源码(稍微有精简),refer: impl.py
    def __init__(self, creator, pool_size=5, max_overflow=10, timeout=30, use_lifo=False, **kw):
        """
        pool_size:
        Note that the pool begins with no connections; once this number of connections is requested, that number of connections will remain.
        pool_size can be set to 0 to indicate no size limit; to disable pooling, use a NullPool instead.

        max_overflow:
        When the number of checked-out connections reaches the size set in pool_size,additional connections will be returned up to this limit.
        When those additional connections are returned to the pool,they are disconnected and discarded.
        the total number of simultaneous connections the pool will allow is pool_size + max_overflow,and the total number of "sleeping" connections the pool will allow is pool_size.
        max_overflow can be set to -1 to indicate no overflow limit;

        kw:
        Other keyword arguments including Pool.recycle,Pool.echo,Pool.reset_on_return and others are passed to the class Pool constructor.
        """
        Pool.__init__(self, creator, **kw)
        self._pool = sqla_queue.Queue(pool_size, use_lifo=use_lifo)
        self._overflow = -pool_size  # 注意
        self._max_overflow = max_overflow
        self._timeout = timeout
        self._overflow_lock = Lock()

    def _do_return_conn(self, conn):  # 释放连接调用(连接资源归还至连接池不会被调用)
        try:
            self._pool.put(conn, False)
        except Full:
            try:
                conn.close()
            finally:
                self._dec_overflow()  # 注意

    def _do_get(self):  # 获取连接调用
        use_overflow = self._max_overflow > -1

        try:
            wait = use_overflow and self._overflow >= self._max_overflow  # 如果使用max_overflow并且连接数已达上限
            return self._pool.get(wait, self._timeout)  # 获取连接池中的连接将被阻塞
        except Empty:
            # don't do things inside of "except Empty", because when we say we timed out or can't connect and raise,
            # Python 3 tells people the real error is queue.Empty which it isn't.
            pass
        if use_overflow and self._overflow >= self._max_overflow:
            if not wait:
                return self._do_get()
            else:
                raise TimeoutError(
                    "QueuePool limit of overflow {} reached, connection timed out, timeout {}".format(self.overflow(),
                                                                                                      self._timeout))

        if self._inc_overflow():
            try:
                return self._create_connection()
            except:
                with util.safe_reraise():
                    self._dec_overflow()
        else:
            return self._do_get()

    def _inc_overflow(self):
        if self._max_overflow == -1:
            self._overflow += 1
            return True
        with self._overflow_lock:
            if self._overflow < self._max_overflow:
                self._overflow += 1
                return True
            else:
                return False

    def _dec_overflow(self):
        if self._max_overflow == -1:
            self._overflow -= 1
            return True
        with self._overflow_lock:
            self._overflow -= 1
            return True

    def recreate(self):
        self.logger.info("Pool recreating")
        return self.__class__(self._creator, pool_size=self._pool.maxsize, max_overflow=self._max_overflow,
                              timeout=self._timeout, recycle=self._recycle, echo=self.echo,
                              logging_name=self._orig_logging_name, use_threadlocal=self._use_threadlocal,
                              reset_on_return=self._reset_on_return, _dispatch=self.dispatch, dialect=self._dialect, )

    def dispose(self):
        while True:
            try:
                conn = self._pool.get(False)
                conn.close()
            except Empty:
                break

        self._overflow = 0 - self.size()
        self.logger.info("Pool disposed. %s", self.status())

    def status(self):
        return "Pool size: {}  Connections in pool: {} Current Overflow: {} Current Checked out connections: {}".format(
            self.size(), self.checkedin(), self.overflow(), self.checkedout())

    def size(self):
        return self._pool.maxsize  # 连接池大小

    def checkedin(self):
        return self._pool.qsize()  # 连接池中的连接数

    def overflow(self):
        return self._overflow

    def checkedout(self):
        return self._overflow + self._pool.maxsize - self._pool.qsize()  # 现有已申请连接总数-池子中的连接数
