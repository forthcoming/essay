import time
from itertools import chain

from redis.commands import CoreCommands, RedisModuleCommands, SentinelCommands
from redis.exceptions import ConnectionError, ExecAbortError, RedisError, ResponseError, TimeoutError, WatchError

from redis_connection import ConnectionPool


# 仅包含unix代码实现部分,参考 https://github.com/redis/redis-py/blob/master/redis/client.py

class Redis(RedisModuleCommands, CoreCommands, SentinelCommands):
    """
    以游标值为0开始迭代,调用SCAN直到返回的游标再次为0称为完整迭代,Redis客户端实例可以在线程之间安全地共享,线程之间传递PubSub或Pipeline对象是不安全
    SELECT命令允许您切换连接当前使用的数据库,这会导致不同数据库连接返回到同一个连接池,因此不会在客户端实例上实现SELECT命令
    如果您在同一应用程序中使用多个Redis数据库,则应该为每个数据库创建一个单独的客户端实例
    redis命令都是调用的Commands类的函数,再通过execute_command调用子类Redis函数
    """

    def __init__(self, host='localhost', port=6379, db=0, password=None, connection_pool=None, max_connections=None):
        if not connection_pool:
            kwargs = {
                'host': host,
                'port': port,
                'db': db,
                'password': password,
                'max_connections': max_connections
            }
            connection_pool = ConnectionPool(**kwargs)
        self.connection_pool = connection_pool

    def execute_command(self, *args, **options):  # Execute a command and return a parsed response
        # command_name = args[0], hget,geohash等
        connection = self.connection_pool.get_connection()  # 第一次运行命令时才会尝试去建立新连接
        try:
            connection.send_command(*args)
            return connection.read_response()
        except (ConnectionError, TimeoutError) as e:
            connection.disconnect()
            if not (connection.retry_on_timeout and isinstance(e, TimeoutError)):
                raise
            connection.send_command(*args)
            return connection.read_response()
        finally:
            self.connection_pool.release(connection)

    def pipeline(self, transaction=True, shard_hint=None):
        return Pipeline(self.connection_pool, transaction, shard_hint)

    def transaction(self, func, *watches, **kwargs):
        """
        Convenience method for executing the callable `func` as a transaction
        while watching all keys specified in `watches`. The 'func' callable
        should expect a single argument which is a Pipeline object.
        """
        shard_hint = kwargs.pop("shard_hint", None)
        value_from_callable = kwargs.pop("value_from_callable", False)
        watch_delay = kwargs.pop("watch_delay", None)
        with self.pipeline(True, shard_hint) as pipe:
            while True:
                try:
                    if watches:
                        pipe.watch(*watches)
                    func_value = func(pipe)
                    exec_value = pipe.execute()
                    return func_value if value_from_callable else exec_value
                except WatchError:
                    if watch_delay is not None and watch_delay > 0:
                        time.sleep(watch_delay)
                    continue


class Pipeline(Redis):  # 一般通过调用Redis实例的pipeline方法获取Pipeline实例

    UNWATCH_COMMANDS = {'DISCARD', 'EXEC', 'UNWATCH'}

    def __init__(self, connection_pool, transaction, shard_hint):
        self.connection_pool = connection_pool
        self.connection = None
        self.transaction = transaction
        self.shard_hint = shard_hint
        self.watching = False
        self.reset()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def __del__(self):
        self.reset()

    def reset(self):
        self.command_stack = []
        self.scripts = set()
        # make sure to reset the connection state in the event that we were watching something
        if self.watching and self.connection:
            try:
                # call this manually since our unwatch or immediate_execute_command methods can call reset()
                self.connection.send_command('UNWATCH')
                self.connection.read_response()
            except ConnectionError:
                self.connection.disconnect()  # disconnect will also remove any previous WATCHes
        self.watching = False  # clean up the other instance attributes
        self.explicit_transaction = False
        # we can safely return the connection to the pool here since we're sure we're no longer WATCHing anything
        if self.connection:
            self.connection_pool.release(self.connection)
            self.connection = None

    def multi(self):  # 发出WATCH命令后启动管道的事务块,使用“execute”结束事务块
        if self.explicit_transaction:
            raise RedisError('Cannot issue nested calls to MULTI')
        if self.command_stack:
            raise RedisError('Commands without an initial WATCH have already been issued')
        self.explicit_transaction = True

    def execute_command(self, *args, **kwargs):
        if (self.watching or args[0] == 'WATCH') and not self.explicit_transaction:
            return self.immediate_execute_command(*args)
        return self.pipeline_execute_command(*args, **kwargs)

    def immediate_execute_command(self, *args):
        command_name = args[0]
        conn = self.connection
        # if this is the first call, we need a connection
        if not conn:
            conn = self.connection_pool.get_connection()
            self.connection = conn
        try:
            conn.send_command(*args)
            return self.parse_response(conn, command_name)
        except (ConnectionError, TimeoutError):
            conn.disconnect()
            try:
                if not self.watching:  # 如果我们已经在watch变量,则遇到ConnectionError不会自动重试
                    conn.send_command(*args)
                    return self.parse_response(conn, command_name)
            except ConnectionError:
                conn.disconnect()
                self.reset()
                raise

    def pipeline_execute_command(self, *args, **options):
        # 暂存命令返回当前Pipeline对象,以便可以将命令链接在一起,如pipe = pipeline.set('foo', 'bar').incr('baz')
        # 运行pipe.execute()将执行管道中所有命令
        self.command_stack.append((args, options))
        return self

    def _execute_transaction(self, connection, commands):
        cmds = chain([(('MULTI',), {})], commands, [(('EXEC',), {})])
        all_cmds = connection.pack_commands([args for args, options in cmds])
        connection.send_packed_command(all_cmds)
        self.parse_response(connection, '_')  # parse off the response for MULTI
        for _ in commands:  # parse off all the other commands
            self.parse_response(connection, '_')
        try:
            response = self.parse_response(connection, '_')  # parse the EXEC
        except ExecAbortError:
            raise
        self.watching = False  # EXEC clears any watched keys
        if response is None:
            raise WatchError("Watched variable changed.")
        return response  # to be parsed, just for learning

    def _execute_pipeline(self, connection, commands):
        # build up all commands into a single request to increase network perf
        all_cmds = connection.pack_commands([args for args, _ in commands])
        connection.send_packed_command(all_cmds)
        response = []
        for args, options in commands:
            try:
                response.append(self.parse_response(connection, args[0]))
            except ResponseError as e:
                response.append(e)
        return response

    def parse_response(self, connection, command_name, disable_decoding=True):
        result = connection.read_response()
        if command_name in self.UNWATCH_COMMANDS:
            self.watching = False
        elif command_name == 'WATCH':
            self.watching = True
        return result

    def load_scripts(self):
        # make sure all scripts that are about to be run on this pipeline exist
        scripts = list(self.scripts)
        immediate = self.immediate_execute_command
        # we can't use the normal script_* methods because they would just get buffered in the pipeline.
        exists = immediate("SCRIPT EXISTS", *[s.sha for s in scripts])
        if not all(exists):
            for s, exist in zip(scripts, exists):
                if not exist:
                    s.sha = immediate("SCRIPT LOAD", s.script)

    def execute(self):  # Execute all the commands in the current pipeline
        stack = self.command_stack
        if not stack and not self.watching:
            return []
        if self.scripts:
            self.load_scripts()
        if self.transaction or self.explicit_transaction:
            execute = self._execute_transaction
        else:
            execute = self._execute_pipeline
        conn = self.connection
        if not conn:
            conn = self.connection_pool.get_connection()
            # assign to self.connection so reset() releases the connection back to the pool after we're done
            self.connection = conn
        try:
            return execute(conn, stack)
        finally:
            self.reset()

    def discard(self):  # Flushes all previously queued commands See: https://redis.io/commands/DISCARD
        self.execute_command("DISCARD")

    def watch(self, *names):
        if self.explicit_transaction:
            raise RedisError('Cannot issue a WATCH after a MULTI')
        return self.execute_command('WATCH', *names)

    def unwatch(self):
        return self.watching and self.execute_command('UNWATCH') or True
