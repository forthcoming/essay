import logging
import random
import threading
import time
from hashlib import sha1
from os import urandom
from types import SimpleNamespace

import redis
from redis.exceptions import RedisError, NoScriptError


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

    def __init__(self, instances, name, timeout=10, blocking_timeout=20, thread_local=True):
        """
        The Redlock Algorithm(refer: https://redis.io/docs/manual/patterns/distributed-locks)
        假设有N=5个完全独立的Redis主节点(无副本),因此需要在不同的计算机上运行5个Redis实例,为了获取锁,客户端执行以下操作:
        1. 获取当前以毫秒为单位时间
        2. 尝试在N个实例中使用相同key-value和比总锁自动释放时间小很多的超时时间(如果某个实例不可用应该尽快尝试与下一个实例通信)来获取锁
        3. 当前时间减去步骤1中的时间戳来计算获取锁花费的时间,当且仅当客户端在大多数实例(至少3个)中获取锁,且获取锁花费时间小于锁有效期才认为获取了锁
        4. 如果获取了锁,则其有效时间为初始有效时间减去经过的时间(步骤3中的计算)
        5. 如果客户端未能获取锁(要么无法锁定N/2+1个实例,要么有效期为负),它将尝试解锁所有实例(甚至是它认为无法锁定的实例)
        说明: 如果是一主一丛,主节点挂掉,但锁还未来得及同步到从节点会导致其他进程再次获取锁

        refer: https://github.com/redis/redis-py/blob/master/redis/lock.py
        time: 0, thread-1 acquires `my-lock`, with a timeout of 5 seconds.thread-1 sets the token to "abc"
        time: 1, thread-2 blocks trying to acquire `my-lock` using the Lock instance.
        time: 5, thread-1 has not yet completed. redis expires the lock key.
        time: 5, thread-2 acquired `my-lock` now that it's available.thread-2 sets the token to "xyz"
        time: 6, thread-1完成任务并调用release(),如果token未存储在threading.local中,那么thread-1会将token值视为"xyz",并且能够成功释放thread-2的锁
        如果一个线程获得锁,然后把这个锁实例传递给另一个线程稍后释放它,这种情况不能用threading.local
        """
        self.instances = instances
        self.quorum = (len(instances) >> 1) + 1
        self.name = name
        self.timeout_ms = int(1000 * timeout)  # 锁的最长寿命,转换为毫秒
        self.blocking_timeout_s = blocking_timeout  # 尝试获取锁阻塞的最长时间
        self.local = threading.local() if thread_local else SimpleNamespace()
        self.local.token = None

    def __enter__(self):
        if self.lock():
            return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.unlock()
        print('exc_type: {}, exc_value: {}, traceback: {}.'.format(exc_type, exc_value, traceback))
        return True  # 注意

    def lock(self):
        self.local.token = urandom(16)
        drift = int(self.timeout_ms * .01) + 2
        start_time = time.time()
        stop_at = start_time + self.blocking_timeout_s
        while start_time < stop_at:
            n = 0
            try:
                for server in self.instances:
                    if server.set(self.name, self.local.token, nx=True, px=self.timeout_ms):
                        n += 1
            except RedisError as e:
                logging.exception(e)
            elapsed_time = int((time.time() - start_time) * 1000)
            validity = int(self.timeout_ms - elapsed_time - drift)
            if validity > 0 and n >= self.quorum:
                return True
            else:  # 如果锁获取失败应立马释放获取的锁定
                self.unlock()
                time.sleep(random.uniform(0, .4))  # 随机延迟,防止脑裂情况(split brain condition),仅适用于多节点
            start_time = time.time()
        raise Exception("lock timeout")

    def unlock(self):
        for server in self.instances:
            try:
                server.evalsha(self.unlock_script_sha, 1, self.name, self.local.token)  # 原子操作
            except NoScriptError:
                server.eval(self.unlock_script, 1, self.name, self.local.token)
            except RedisError as e:
                logging.exception("Error: unlocking lock {}".format(self.name))
                raise
        return True


def do_something(idx, lock, another_lock):
    # 如果do_something耗时大于锁生存周期ttl,会出现并发问题,总耗时变小
    # 如果锁内部token未使用threading.local存储,会出现并发问题,总耗时变小
    print('Im doing something in idx {}'.format(idx))
    if idx & 1:
        lock = another_lock
    with lock:
        time.sleep(1)
        1 / 0


if __name__ == '__main__':
    servers = [
        redis.Redis(host="localhost", port=2345),
        redis.Redis(host="localhost", port=6379),
        redis.Redis(host="localhost", port=6380),
    ]
    room_lock = Redlock(servers, 'room_lock', timeout=500)
    song_lock = Redlock(servers, 'song_lock', timeout=500)
    threads = [threading.Thread(target=do_something, args=(idx, room_lock, song_lock)) for idx in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    print('after doing something')
