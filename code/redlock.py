import logging, time, redis, random, threading
from redis.exceptions import RedisError, NoScriptError
from os import urandom
from hashlib import sha1


def get_servers(connection_list):
    servers = []
    for connection_info in connection_list:
        if isinstance(connection_info, str):
            server = redis.Redis.from_url(connection_info)
        elif isinstance(connection_info, dict):
            server = redis.Redis(**connection_info)
        else:
            server = connection_info
        servers.append(server)
    return servers

def do_something(idx,room_lock,song_lock):
    print('Im doing something in idx {}'.format(idx))
    lock = room_lock if idx & 1 else song_lock
    with lock:
        time.sleep(1)
        1 / 0
        
class Redlock:
    # KEYS[1] - lock name
    # ARGS[1] - token
    # return 1 if the lock was released, otherwise 0
    unlock_script = """
        if redis.call("get",KEYS[1]) == ARGV[1] then
            return redis.call("del",KEYS[1])
        else
            return 0
        end
    """
    unlock_script_sha = sha1(bytes(unlock_script, encoding='utf8')).hexdigest()

    def __init__(self, servers, name, ttl=10000, blocking_timeout=20):
        '''
        reference:
            https://redis.io/topics/distlock
            https://github.com/SPSCommerce/redlock-py
            https://github.com/andymccurdy/redis-py/blob/master/redis/lock.py
        ttl is the number of milliseconds for the validity time.如果担心加锁业务在锁过期时还未执行完,可以给该业务加一个定时任务,定时检测业务是否还存活并决定是否给锁续期
        the token is placed in thread local storage so that a thread only sees its token, not a token set by another thread. Consider the following timeline:
        time: 0, thread-1 acquires `my-lock`, with a timeout of 5 seconds.thread-1 sets the token to "abc"
        time: 1, thread-2 blocks trying to acquire `my-lock` using the Lock instance.
        time: 5, thread-1 has not yet completed. redis expires the lock key.
        time: 5, thread-2 acquired `my-lock` now that it's available.thread-2 sets the token to "xyz"
        time: 6, thread-1 finishes its work and calls release(). if the token is *not* stored in thread local storage,then thread-1 would see the token value as "xyz" and would be able to successfully release the thread-2's lock.
        In some use cases it's necessary to disable thread local storage.
        For example, if you have code where one thread acquires a lock and passes that lock instance to a worker thread to release later.
        If thread local storage isn't disabled in this case, the worker thread won't see the token set by the thread that acquired the lock.
        Our assumption is that these cases aren't common and as such default to using thread local storage.
        '''
        assert isinstance(ttl, int), 'ttl {} is not an integer'.format(ttl)
        self.servers = servers
        self.quorum = len(servers) // 2 + 1
        self.name = name
        self.ttl = ttl
        self.blocking_timeout = blocking_timeout
        self.local = threading.local()

    def __enter__(self):
        if self.lock():
            return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.unlock()
        print('exc_type: {}, exc_value: {}, traceback: {}.'.format(exc_type, exc_value, traceback))
        return True  # 注意

    def lock(self):
        self.local.token = urandom(16)
        drift = int(self.ttl * .01) + 2  # Add 2 milliseconds to the drift to account for Redis expires precision which is 1 millisecond, plus 1 millisecond min drift for small TTLs.
        start_time = time.time()
        stop_at = start_time + self.blocking_timeout
        while start_time < stop_at:
            n = 0
            try:
                for server in self.servers:
                    if server.set(self.name, self.local.token, nx=True, px=self.ttl):
                        n += 1
            except RedisError as e:
                logging.exception(e)
            elapsed_time = int((time.time() - start_time) * 1000)
            validity = int(self.ttl - elapsed_time - drift)
            if validity > 0 and n >= self.quorum:
                return True
            else:  # 如果锁获取失败应立马释放获取的锁定
                self.unlock()
                time.sleep(random.uniform(0,.4))  # a random delay in order to try to desynchronize multiple clients trying to acquire the lock for the same resource at the same time
            start_time = time.time()
        raise Exception("lock timeout")

    def unlock(self):
        for server in self.servers:
            try:
                server.evalsha(self.unlock_script_sha, 1, self.name, self.local.token)  # 原子操作
            except NoScriptError:
                server.eval(self.unlock_script, 1, self.name, self.local.token)
            except RedisError as e:
                logging.exception("Error: unlocking lock {}".format(self.name))
                raise
        return True

servers = get_servers([
    {"host": "localhost", "port": 2345, "db": 0},
    {"host": "localhost", "port": 8002, "db": 0},
    {"host": "localhost", "port": 8003, "db": 0},
])

'''
如果do_something耗时大于锁生存周期ttl,会出现并发问题,总耗时变小
如果锁内部token未使用threading.local存储,会出现并发问题,总耗时变小
'''
room_lock = Redlock(servers, 'room_lock', ttl=500)
song_lock = Redlock(servers, 'song_lock', ttl=500)

if __name__ == '__main__':
    threads = [threading.Thread(target=do_something,args=(idx,room_lock,song_lock)) for idx in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    print('after doing something')
