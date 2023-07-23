import logging
import random
import threading
import time
from contextlib import contextmanager
from os import urandom
from types import SimpleNamespace

from redis import Redis
from redis.exceptions import RedisError


class ReadWriteRLock:  # 分布式可重入读写锁
    """
    refer:
        https://github.com/redisson/redisson/blob/master/redisson/src/main/java/org/redisson/RedissonWriteLock.java
        https://github.com/redisson/redisson/blob/master/redisson/src/main/java/org/redisson/RedissonReadLock.java

    A线程加写锁成功
        1. 未加过读写锁
        2. A线程加过写锁
    A线程加读锁成功
        1. 未加过读写锁
        2. 加过读锁
        3. A加过写锁

    mode=read,只可能有读锁,但可以包含多个线程
    mode=write,可能有读锁和写锁,但只可能包含一个线程且写锁比读锁先获得
    同一时刻只会按以下一种形式存在,写锁在特定条件下会转换成读锁
    rw_lock = { 'mode':'read','t1':2,'t2':3,'tn':2 }
    rw_lock = { 'mode':'write','t1:w':2,'t1':3 }

    acquire_read_rlock: keys[1]: 锁在redis中的key, args[1]锁超时时间, args[2]读锁的名称, args[3]写锁的名称,它是在锁名称的后面加上write
    加锁流程如下:
    1. 获取锁的mode,如果锁的mode为false,表示之前没有设置过读写锁,此时可以获得读锁
        1. 将锁的mode设置为read,锁名称对应的线程数设置为1,并设置锁的过期时间
    2. 如果当前存在读锁或者持有写锁的是当前线程,都可以加读锁
        1. 将锁名称对应的线程数增加1,并设置锁的过期时间
    3. 否则返回false

    release_read_rlock: keys[1]锁在redis中的key, args[1]锁的名称, args[2]锁的过期时间
    解锁流程如下:
    1. 获取锁的mode,如果锁的mode为false,表示之前没有设置过读写锁,此时可以直接解锁,返回1
    2. 查看锁是否存在,如果不存在锁返回nil
    3. 将锁名称对应的线程数减1,如果剩余的线程数为0,表示没有其他线程持有该锁了,删除该锁
    4. 如果当前锁结构对应的hash表大小大于1,表示有其他线程持有锁
    5. 否则没有其他线程持有锁,此时可以彻底释放锁,删除锁结构,返回1

    acquire_write_rlock: keys[1]锁在redis中的key, args[1]锁的超时时间, args[2]锁的名称
    加锁流程如下:
    1. 获取锁的mode,如果锁的mode为false,表示之前没有设置过读写锁,此时可以获得写锁
        1. 将锁的mode设置为write,将锁名称对应的线程数设置为1
        2. 设置锁的过期时间
    2. 如果持有写锁的线程为当前线程(hexists keys[1] args[2]隐含mode=write),此时可以继续加写锁
        1. 将锁名称对应的线程数增加1
        2. 更新锁的过期时间
    3. 否则返回false

    release_write_rlock: keys[1]锁在redis中的key, args[1]锁的过期时间, args[2]锁的名称
    解锁流程如下:
    1. 获取锁的mode,如果锁的mode为false,表示之前没有设置过读写锁,此时可以直接解锁
    2. 如果锁的mode为read或者非本线程加的写锁,返回nil
    3. 将锁名称对应的线程数减1,如果剩余的线程数大于0,表示还有其他线程持有该锁,重新设置锁结构的过期时间
    4. 如果剩余的线程数为0,表示没有其他线程持有该写锁了,于是删除该锁
       如果当前锁结构对应的hash表大小等于1,表示没有其他线程持有锁,此时可以彻底释放锁,删除锁结构
       否则表示还存在读锁,于是将锁的mode设置为read

    todo:
    使用看门狗给锁续期
    写锁优先
    """

    read_write_rlock_script = """#!lua name=read_write_rlock       
        local function acquire_read_rlock(keys,args) 
            local mode = redis.call('hget', keys[1], 'mode')
            if mode == false then
                redis.call('hmset', keys[1], 'mode', 'read', args[2], 1)       
                redis.call('pexpire', keys[1], args[1])
                return true
            end;
            if mode == 'read' or redis.call('hexists', keys[1], args[3]) == 1 then  -- 如果是读锁或者本线程上过写锁
                redis.call('hincrby', keys[1], args[2], 1)
                redis.call('pexpire', keys[1], args[1])
                return true
            end
            return false
        end
        
        local function release_read_rlock(keys,args)
            local mode = redis.call('hget', keys[1], 'mode')
            if mode == false then
                return 1
            end
            if redis.call('hexists', keys[1], args[1]) == 0 then
                return nil
            end
            if redis.call('hincrby', keys[1], args[1], -1) == 0 then
                redis.call('hdel', keys[1], args[1])
            end
            if redis.call('hlen', keys[1]) > 1 then
                redis.call('pexpire', keys[1], args[2])
                return 0
            else
                redis.call('del', keys[1])
                return 1
            end        
        end

        local function acquire_write_rlock(keys,args)      
            local mode = redis.call('hget', keys[1], 'mode')
            if mode == false then
                redis.call('hmset', keys[1], 'mode', 'write', args[2], 1)
                redis.call('pexpire', keys[1], args[1])
                return true
            end
            if redis.call('hexists', keys[1], args[2]) == 1 then
                redis.call('hincrby', keys[1], args[2], 1)
                redis.call('pexpire', keys[1], args[1])
                return true
            end
            return false  
        end

        local function release_write_rlock(keys,args)  
            local mode = redis.call('hget', keys[1], 'mode')
            if mode == false then
                return 1
            end
            if redis.call('hexists', keys[1], args[2]) == 0 then
                return nil
            else
                if redis.call('hincrby', keys[1], args[2], -1) > 0 then
                    redis.call('pexpire', keys[1], args[1])
                    return 0
                else
                    redis.call('hdel', keys[1], args[2])
                    if redis.call('hlen', keys[1]) == 1 then
                        redis.call('del', keys[1])
                    else
                        redis.call('hset', keys[1], 'mode', 'read')  -- has unlocked read-locks,同线程会出现先释放写锁的情况?
                        redis.call('pexpire', keys[1], args[1])
                    end
                    return 1
                end
            end      
        end
             
        redis.register_function('acquire_read_rlock', acquire_read_rlock) 
        redis.register_function('release_read_rlock', release_read_rlock) 
        redis.register_function('acquire_write_rlock', acquire_write_rlock) 
        redis.register_function('release_write_rlock', release_write_rlock) 
    """
    is_register_script = False

    def __init__(self, rds: Redis, name_prefix, pttl=30000, timeout=30, thread_local=True):
        self.rds = rds
        self.name_prefix = name_prefix
        self.pttl = pttl  # 锁过期时间,单位ms
        self.timeout = timeout  # 上锁最多重试时间,单位s
        self.local = threading.local() if thread_local else type('dummy', (), {})
        self.local.token = None
        self.register_lib()

    def register_lib(self):
        if not self.__class__.is_register_script:
            self.rds.function_load(self.__class__.read_write_rlock_script, True)
            self.__class__.is_register_script = True

    def get_key(self, name):
        return '{}:{}'.format(self.name_prefix, name)

    def get_rlock_name(self):
        if self.local.token is None:
            self.local.token = urandom(16)
        return self.local.token

    def get_wlock_name(self):
        if self.local.token is None:
            self.local.token = urandom(16)
        return '{}:w'.format(self.local.token)

    @contextmanager
    def get_rlock(self, name):
        key = self.get_key(name)
        rlock_name = self.get_rlock_name()
        wlock_name = self.get_wlock_name()
        stop_at = time.time() + self.timeout
        cnt = 0
        try:
            while time.time() < stop_at:
                if self.rds.fcall("acquire_read_rlock", 1, key, self.pttl, rlock_name, wlock_name):
                    yield
                    break
                cnt += 1
                time.sleep(max(random.uniform(0, .02) * cnt, .5))
            else:
                raise Exception('获取读锁超时')
        finally:
            self.rds.fcall("release_read_rlock", 1, key, self.pttl, rlock_name)  # 也可以处理mode='write'模式的写锁

    @contextmanager
    def get_wlock(self, name):
        key = self.get_key(name)
        wlock_name = self.get_wlock_name()
        stop_at = time.time() + self.timeout
        cnt = 0
        try:
            while time.time() < stop_at:
                if self.rds.fcall("acquire_write_rlock", 1, key, self.pttl, wlock_name):
                    yield
                    break
                cnt += 1
                time.sleep(max(random.uniform(0, .02) * cnt, .5))
            else:
                raise Exception('获取写锁超时')
        finally:
            self.rds.fcall("release_write_rlock", 1, key, self.pttl, wlock_name)


class Redlock:
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
    可以通过每个线程一个锁实例解决,具有相同name的锁视为专门处理某一任务的锁集合
    如果一个线程获得锁,然后把这个锁实例传递给另一个线程稍后释放它,这种情况不能用threading.local
    """
    redlock_script = """#!lua name=redlock   
        local function release(keys,args)    -- return 1 if the lock was released, otherwise 0   
            if redis.call("get",keys[1]) == args[1] then
                return redis.call("del",keys[1])
            else
                return 0
            end
        end
    
        redis.register_function('release', release)
    """
    is_register_script = False

    def __init__(self, instances, name, timeout=10, blocking_timeout=20, thread_local=True):
        self.instances = instances
        self.quorum = (len(instances) >> 1) + 1
        self.name = name
        self.timeout_ms = int(1000 * timeout)  # 锁的最长寿命,转换为毫秒
        self.blocking_timeout_s = blocking_timeout  # 尝试获取锁阻塞的最长时间
        self.local = threading.local() if thread_local else SimpleNamespace()
        self.local.token = None
        self.register_lib()

    def register_lib(self):
        if not self.__class__.is_register_script:
            for instance in self.instances:
                instance.function_load(self.__class__.redlock_script, True)
            self.__class__.is_register_script = True  # 注意这里要明确指定修改类变量is_register_script

    def __enter__(self):
        if self.acquire():
            return self
        raise Exception("Unable to acquire lock within the time specified")

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()
        print('exc_type: {}, exc_value: {}, traceback: {}.'.format(exc_type, exc_value, traceback))

    def get_key(self, suffix):
        if suffix:
            return f'{self.name}:{suffix}'
        else:
            return self.name

    def acquire(self, suffix=""):
        self.local.token = urandom(16)
        drift = int(self.timeout_ms * .01) + 2
        start_time = time.monotonic()
        stop_at = start_time + self.blocking_timeout_s
        key = self.get_key(suffix)
        while start_time < stop_at:
            n = 0
            for server in self.instances:
                try:
                    if server.set(key, self.local.token, nx=True, px=self.timeout_ms):
                        n += 1
                except RedisError as e:
                    logging.exception(e)
            elapsed_time = int((time.monotonic() - start_time) * 1000)
            validity = int(self.timeout_ms - elapsed_time - drift)
            if validity > 0 and n >= self.quorum:
                return True
            else:  # 如果锁获取失败应立马释放获取的锁定
                self.release(suffix)
                time.sleep(random.uniform(0, .4))  # 随机延迟,防止脑裂情况(split brain condition),仅适用于多节点
            start_time = time.monotonic()
        return False

    def release(self, suffix=""):
        key = self.get_key(suffix)
        for instance in self.instances:
            instance.fcall('release', 1, key, self.local.token)
        return True


def do_something(idx, lock, another_lock):
    # 如果do_something耗时大于锁生存周期timeout,会出现并发问题,总耗时变小
    # 如果锁内部token未使用threading.local存储,会出现并发问题,总耗时变小(其他线程拿不到锁时会尝试释放锁导致误删)
    print('Im doing something in idx {}'.format(idx))
    if idx & 1:
        lock = another_lock
    with lock:
        time.sleep(2)


if __name__ == '__main__':
    t1 = time.monotonic()
    servers = [  # 建议基数个redis实例
        Redis(host="localhost", port=6379),
        # Redis(host="localhost", port=6380),
        # Redis(host="localhost", port=2345),
    ]
    room_lock = Redlock(servers, 'room', timeout=3, thread_local=False)
    song_lock = Redlock(servers, 'song', timeout=3, thread_local=False)
    threads = [threading.Thread(target=do_something, args=(idx, room_lock, song_lock)) for idx in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    print(f'cost {time.monotonic() - t1} seconds')
