from itertools import chain
import sys
from redis.connection import ConnectionPool
from redis.exceptions import ConnectionError,ExecAbortError,RedisError,ResponseError,TimeoutError,WatchError

'''
Starting an iteration with a cursor value of 0, and calling SCAN until the returned cursor is 0 again is called a full iteration.

Redis client instances can safely be shared between threads. 
Internally, connection instances are only retrieved from the connection pool during command execution, and returned to the pool directly after. Command execution never modifies state on the client instance.
However, there is one caveat: the Redis SELECT command. The SELECT command allows you to switch the database currently in use by the connection. 
That database remains selected until another is selected or until the connection is closed. This creates an issue in that connections could be returned to the pool that are connected to a different database.
As a result, redis-py does not implement the SELECT command on client instances. 
If you use multiple Redis databases within the same application, you should create a separate client instance (and possibly a separate connection pool) for each database.
It is not safe to pass PubSub or Pipeline objects between threads.
'''
class Redis:
    def __init__(self, host='localhost', port=6379,db=0, password=None,connection_pool=None,max_connections=None):
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

    def parse_response(self, connection, **options):
        response = connection.read_response()  #   "Parses a response from the Redis server"
        pass

    def execute_command(self, *args, **options):
        "Execute a command and return a parsed response"
        pool = self.connection_pool
        command_name = args[0]
        connection = pool.get_connection(command_name, **options)  # 此处才会尝试去建立新连接
        try:
            connection.send_command(*args)
            return self.parse_response(connection, command_name, **options)
        except (ConnectionError, TimeoutError) as e:
            raise
        finally:
            pool.release(connection)

    def pipeline(self, transaction=True, shard_hint=None):
        return Pipeline(self.connection_pool,transaction,shard_hint)

class Pipeline(Redis):
    """
    MULTI/EXEC: These are implemented as part of the Pipeline class. The pipeline is wrapped with the MULTI and EXEC statements by default when it is executed, which can be disabled by specifying transaction=False. 
    Apart from making a group of operations atomic, pipelines are useful for reducing the back-and-forth overhead between the client and server.
    In addition, pipelines can also ensure the buffered commands are executed atomically as a group. This happens by default. 
    If you want to disable the atomic nature of a pipeline but still want to buffer commands, you can turn off transactions.
    >>> pipe = r.pipeline(transaction=False)

    A common issue occurs when requiring atomic transactions but needing to retrieve values in Redis prior for use within the transaction.
    For instance, let's assume that the INCR command didn't exist and we need to build an atomic version of INCR in Python.
    The completely naive implementation could GET the value, increment it in Python, and SET the new value back.
    However, this is not atomic because multiple clients could be doing this at the same time, each getting the same value from GET.
    Enter the WATCH command. WATCH provides the ability to monitor one or more keys prior to starting a transaction. 
    If any of those keys change prior the execution of that transaction, the entire transaction will be canceled and a WatchError will be raised. 
    To implement our own client-side INCR command, we could do something like this:
    >>> with r.pipeline() as pipe:
            while True:
                try:
                    pipe.watch('OUR-SEQUENCE-KEY')  # put a WATCH on the key that holds our sequence value
                    # after WATCHing, the pipeline is put into immediate execution mode until we tell it to start buffering commands again. this allows us to get the current value of our sequence
                    current_value = pipe.get('OUR-SEQUENCE-KEY')
                    next_value = int(current_value) + 1
                    pipe.multi()  # now we can put the pipeline back into buffered mode with MULTI
                    pipe.set('OUR-SEQUENCE-KEY', next_value)
                    pipe.execute()  #  and finally, execute the pipeline (the set command)
                    # if a WatchError wasn't raised during execution, everything we just did happened atomically.
                    break
               except WatchError:
                    # another client must have changed 'OUR-SEQUENCE-KEY' between the time we started WATCHing it and the pipeline's execution. our best bet is to just retry.
                    continue
    """

    UNWATCH_COMMANDS = {'DISCARD', 'EXEC', 'UNWATCH'}

    def __init__(self, connection_pool, transaction,shard_hint):
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
        # make sure to reset the connection state in the event that we were watching something
        if self.watching and self.connection:
            try:
                # call this manually since our unwatch or
                # immediate_execute_command methods can call reset()
                self.connection.send_command('UNWATCH')
                self.connection.read_response()
            except ConnectionError:
                # disconnect will also remove any previous WATCHes
                self.connection.disconnect()
        # clean up the other instance attributes
        self.watching = False
        self.explicit_transaction = False
        # we can safely return the connection to the pool here since we're sure we're no longer WATCHing anything
        if self.connection:
            self.connection_pool.release(self.connection)
            self.connection = None

    def watch(self, *names):
        "Watches the values at keys ``names``"
        if self.explicit_transaction:
            raise RedisError('Cannot issue a WATCH after a MULTI')
        return self.execute_command('WATCH', *names)

    def unwatch(self):
        "Unwatches all previously specified keys"
        return self.watching and self.execute_command('UNWATCH') or True

    def multi(self):
        """
        Start a transactional block of the pipeline after WATCH commands are issued. End the transactional block with `execute`.
        """
        if self.explicit_transaction:
            raise RedisError('Cannot issue nested calls to MULTI')
        if self.command_stack:
            raise RedisError('Commands without an initial WATCH have already been issued')
        self.explicit_transaction = True

    def execute_command(self, *args, **kwargs):
        if (self.watching or args[0] == 'WATCH') and not self.explicit_transaction:
            return self.immediate_execute_command(*args, **kwargs)
        return self.pipeline_execute_command(*args, **kwargs)

    def immediate_execute_command(self, *args, **options):
        """
        Execute a command immediately, but don't auto-retry on a ConnectionError if we're already WATCHing a variable. 
        Used when issuing WATCH or subsequent commands retrieving their values but before MULTI is called.
        """
        command_name = args[0]
        conn = self.connection
        # if this is the first call, we need a connection
        if not conn:
            conn = self.connection_pool.get_connection(command_name,self.shard_hint)
            self.connection = conn
        try:
            conn.send_command(*args)
            return self.parse_response(conn, command_name, **options)
        except (ConnectionError, TimeoutError) as e:
            conn.disconnect()
            # if we're not already watching, we can safely retry the command
            try:
                if not self.watching:
                    conn.send_command(*args)
                    return self.parse_response(conn, command_name, **options)
            except ConnectionError:
                # the retry failed so cleanup.
                conn.disconnect()
                self.reset()
                raise

    def pipeline_execute_command(self, *args, **options):
        """
        Stage a command to be executed when execute() is next called Returns the current Pipeline object back so commands can be chained together, 
        such as: pipe = pipe.set('foo', 'bar').incr('baz').decr('bang')
        At some other point, you can then run: pipe.execute(),which will execute all commands queued in the pipe.
        """
        self.command_stack.append((args, options))
        return self

    def execute(self):
        "Execute all the commands in the current pipeline"
        stack = self.command_stack
        if not stack:
            return []
        if self.transaction or self.explicit_transaction:
            execute = self._execute_transaction
        else:
            execute = self._execute_pipeline
        conn = self.connection
        if not conn:
            conn = self.connection_pool.get_connection('MULTI', self.shard_hint)
            # assign to self.connection so reset() releases the connection back to the pool after we're done
            self.connection = conn

        try:
            return execute(conn, stack)
        except (ConnectionError, TimeoutError) as e:
            conn.disconnect()
            if not conn.retry_on_timeout and isinstance(e, TimeoutError):
                raise
            # if we were watching a variable, the watch is no longer valid since this connection has died. 
            # raise a WatchError, which indicates the user should retry his transaction. 
            # If this is more than a temporary failure, the WATCH that the user next issues will fail, propegating the real ConnectionError
            if self.watching:
                raise WatchError("A ConnectionError occured on while watching one or more keys")
            # otherwise, it's safe to retry since the transaction isn't predicated on any state
            return execute(conn, stack)
        finally:
            self.reset()
            
    def _execute_transaction(self, connection, commands):
        cmds = chain([(('MULTI', ), {})], commands, [(('EXEC', ), {})])
        all_cmds = connection.pack_commands([args for args, options in cmds if EMPTY_RESPONSE not in options])
        connection.send_packed_command(all_cmds)
        errors = []
        # parse off the response for MULTI
        # NOTE: we need to handle ResponseErrors here and continue
        # so that we read all the additional command messages from
        # the socket
        try:
            self.parse_response(connection, '_')
        except ResponseError:
            errors.append((0, sys.exc_info()[1]))

        # and all the other commands
        for i, command in enumerate(commands):
            if EMPTY_RESPONSE in command[1]:
                errors.append((i, command[1][EMPTY_RESPONSE]))
            else:
                try:
                    self.parse_response(connection, '_')
                except ResponseError:
                    ex = sys.exc_info()[1]
                    self.annotate_exception(ex, i + 1, command[0])
                    errors.append((i, ex))

        # parse the EXEC.
        try:
            response = self.parse_response(connection, '_')
        except ExecAbortError:
            if self.explicit_transaction:
                self.immediate_execute_command('DISCARD')
            if errors:
                raise errors[0][1]
            raise sys.exc_info()[1]

        if response is None:
            raise WatchError("Watched variable changed.")

        # put any parse errors into the response
        for i, e in errors:
            response.insert(i, e)

        if len(response) != len(commands):
            self.connection.disconnect()
            raise ResponseError("Wrong number of response items from pipeline execution")
        return response  # to be parsed, just for learning

    def _execute_pipeline(self, connection, commands):
        # build up all commands into a single request to increase network perf
        all_cmds = connection.pack_commands([args for args, _ in commands])
        connection.send_packed_command(all_cmds)

        response = []
        for args, options in commands:
            try:
                response.append(self.parse_response(connection, args[0], **options))
            except ResponseError:
                response.append(sys.exc_info()[1])
        return response


    def parse_response(self, connection, command_name, **options):
        result = Redis.parse_response(self, connection, command_name, **options)
        if command_name in self.UNWATCH_COMMANDS:
            self.watching = False
        elif command_name == 'WATCH':
            self.watching = True
        return result

