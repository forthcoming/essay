import logging
import os
import random
import threading
import time
from contextlib import contextmanager
from types import SimpleNamespace

from redis import Redis
from redis.exceptions import RedisError

'''
程序如何防止死锁:
1. 锁不要嵌套,如果必须嵌套则使用递归锁
2. 不同线程间加锁顺序尽量一致,如果线程1要获取LockA,LockB,线程2要获取LockB,LockA,则很容易死锁
3. 锁设置超时时间或死锁检测
'''


class ReadWriteRLock:  # 分布式可重入读写锁
    """
    互斥锁适合对共享资源的互斥访问即同时只允许一个线程访问资源; 读写锁适合读取频率较高,写入频率较低的情况,以提高并发性能
    当读写锁处于读模式时,如果有另外线程试图以写模式加锁,读写锁通常会阻塞随后的读模式锁请求,这样可以避免读模式锁长期占用,而等待的写模式锁请求长期阻塞
    只用写锁就会退化为互斥锁
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
    同一时刻只会按以下一种形式存在,mode=write在释放写锁时有可能转换为mode=read
    rw_lock = { 'mode':'read','t1':2,'t2':3,'tn':2 }
    rw_lock = { 'mode':'write','t1:w':2,'t1':3 }

    todo:
    使用看门狗给锁续期
    写锁优先
    """

    # acquire_read_rlock: keys[1]锁在redis中的key, args[1]锁过期时间, args[2]读锁的名称, args[3]写锁的名称,它是在读锁后面加上":w"
    # 加锁流程:
    # 1. 获取锁的mode,如果mode=false,表示之前没有设置过读写锁,此时可以获得读锁
    #     将锁的mode设置为read,锁对应的线程数设置为1,并设置锁的过期时间
    # 2. 如果mode=read或者持有写锁的是当前线程(隐含mode=write),都可以加读锁
    #     将锁对应的线程数加1并更新过期时间
    #
    # release_read_rlock: keys[1]锁在redis中的key, args[1]读锁的名称
    # 解锁流程:
    # 1. 获取锁的mode,如果mode=false,表示之前没有设置过读写锁,直接返回
    # 2. 查看锁对应的线程,如果不存在直接返回
    # 3. 将锁对应的线程数减1,如果剩余线程数为0,删除锁对应的线程
    #     如果当前锁结构对应的hash大小等于1,表示没有线程持有锁,可以删除锁结构
    #
    # acquire_write_rlock: keys[1]锁在redis中的key, args[1]锁过期时间, args[2]写锁的名称
    # 加锁流程:
    # 1. 获取锁的mode,如果mode=false,表示之前没有设置过读写锁,此时可以获得写锁
    #     将锁的mode设置为write,锁对应的线程数设置为1,并设置锁的过期时间
    # 2. 如果持有写锁的是当前线程(hexists keys[1] args[2]隐含mode=write),此时可以继续加写锁
    #     将锁对应的线程数增加1并更新过期时间
    #
    # release_write_rlock: keys[1]锁在redis中的key, args[1]写锁的名称
    # 解锁流程:
    # 1. 获取锁的mode,如果mode=false,表示之前没有设置过读写锁,直接返回
    # 2. 查看锁对应的线程,如果不存在直接返回
    # 3. 将锁对应的线程数减1,如果剩余的线程数为0,删除锁对应的线程
    #     如果当前锁结构对应的hash大小等于1,表示没有线程持有锁,可以删除锁结构
    #     否则表示还存在读锁,将mode设为read
    read_write_rlock_script = """#!lua name=read_write_rlock       
        local function acquire_read_rlock(keys,args) 
            local mode = redis.call('hget', keys[1], 'mode')
            if mode == false then
                redis.call('hmset', keys[1], 'mode', 'read', args[2], 1)       
                redis.call('pexpire', keys[1], args[1])
                return true
            end
            if (mode == 'read') or (redis.call('hexists', keys[1], args[3]) == 1) then  -- 如果是读锁或者本线程写锁
                redis.call('hincrby', keys[1], args[2], 1)
                local remain_time = redis.call('pttl', keys[1])
                redis.call('pexpire', keys[1], math.max(remain_time, args[1]))
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
                return 1
            end
            
            if redis.call('hincrby', keys[1], args[1], -1) == 0 then
                redis.call('hdel', keys[1], args[1])
                if redis.call('hlen', keys[1]) == 1 then
                    redis.call('del', keys[1])
                end  
            end
            return 1      
        end

        local function acquire_write_rlock(keys,args)      
            local mode = redis.call('hget', keys[1], 'mode')
            if mode == false then
                redis.call('hmset', keys[1], 'mode', 'write', args[2], 1)
                redis.call('pexpire', keys[1], args[1])
                return true
            end
            if redis.call('hexists', keys[1], args[2]) == 1 then  -- 隐含mode=write
                redis.call('hincrby', keys[1], args[2], 1)
                local remain_time = redis.call('pttl', keys[1])
                redis.call('pexpire', keys[1], remain_time + args[1])
                return true
            end
            return false  
        end


        local function release_write_rlock(keys,args)  
            local mode = redis.call('hget', keys[1], 'mode')
            if mode == false then
                return 1
            end
            if redis.call('hexists', keys[1], args[1]) == 0 then
                return 1
            end

            if redis.call('hincrby', keys[1], args[1], -1) == 0 then  -- 隐含mode=write
                redis.call('hdel', keys[1], args[1])
                if redis.call('hlen', keys[1]) == 1 then
                    redis.call('del', keys[1])
                else
                    redis.call('hset', keys[1], 'mode', 'read')  -- has unlocked read-locks
                end
            end    
            return 1    
        end
             
        redis.register_function('acquire_read_rlock', acquire_read_rlock) 
        redis.register_function('release_read_rlock', release_read_rlock) 
        redis.register_function('acquire_write_rlock', acquire_write_rlock) 
        redis.register_function('release_write_rlock', release_write_rlock) 
    """
    is_register_script = False

    def __init__(self, rds, timeout=10, blocking_timeout=5, thread_local=True):
        self.rds = rds
        self.timeout_ms = int(1000 * timeout)  # 锁过期时间,单位ms
        self.blocking_timeout_s = blocking_timeout  # 尝试获取锁阻塞的最长时间,单位s
        self.local = threading.local() if thread_local else SimpleNamespace()
        self.register_lib()

    def register_lib(self):
        if not self.__class__.is_register_script:
            self.rds.function_load(self.__class__.read_write_rlock_script, True)
            self.__class__.is_register_script = True

    def read_rlock_name(self):
        if not hasattr(self.local, 'token'):
            self.local.token = os.urandom(16)
        return self.local.token

    def write_rlock_name(self):
        if not hasattr(self.local, 'token'):
            self.local.token = os.urandom(16)
        return f'{self.local.token}:w'

    @contextmanager
    def acquire_read_rlock(self, key, blocking_timeout_s=None):
        read_rlock_name = self.read_rlock_name()
        write_rlock_name = self.write_rlock_name()
        if blocking_timeout_s is None:
            blocking_timeout_s = self.blocking_timeout_s
        stop_at = time.monotonic() + blocking_timeout_s
        cnt = 0
        try:
            while time.monotonic() <= stop_at:
                if self.rds.fcall("acquire_read_rlock", 1, key, self.timeout_ms, read_rlock_name, write_rlock_name):
                    yield
                    break
                cnt += 1
                time.sleep(max(.02 * cnt * random.random(), .05))
            else:
                raise Exception('获取读锁超时')
        finally:
            self.rds.fcall("release_read_rlock", 1, key, read_rlock_name)  # mode=write也可以处理

    @contextmanager
    def acquire_write_rlock(self, key, blocking_timeout_s=None):
        write_rlock_name = self.write_rlock_name()
        if blocking_timeout_s is None:
            blocking_timeout_s = self.blocking_timeout_s
        stop_at = time.monotonic() + blocking_timeout_s
        cnt = 0
        try:
            while time.monotonic() <= stop_at:
                if self.rds.fcall("acquire_write_rlock", 1, key, self.timeout_ms, write_rlock_name):
                    yield
                    break
                cnt += 1
                time.sleep(max(.02 * cnt * random.random(), .05))
            else:
                raise Exception('获取写锁超时')
        finally:
            self.rds.fcall("release_write_rlock", 1, key, write_rlock_name)


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
    如果不想让token存储在threading.local,可以通过每个线程一个锁实例解决,具有相同name的锁视为专门处理某一任务的锁集合
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

    def __init__(self, instances: list[Redis], name, timeout=10, blocking_timeout=20, thread_local=True):
        self.instances = instances
        self.quorum = (len(instances) >> 1) + 1
        self.name = name
        self.timeout_ms = int(1000 * timeout)  # 锁的最长寿命,转换为毫秒
        self.blocking_timeout_s = blocking_timeout  # 尝试获取锁阻塞的最长时间
        self.local = threading.local() if thread_local else SimpleNamespace()
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

    def acquire(self, suffix="", blocking_timeout_s=None):
        self.local.token = os.urandom(16)
        drift = int(self.timeout_ms * .01) + 2
        start_time = time.monotonic()
        if blocking_timeout_s is None:
            blocking_timeout_s = self.blocking_timeout_s
        stop_at = start_time + blocking_timeout_s
        key = self.get_key(suffix)
        while start_time <= stop_at:
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


class TestLock:
    servers = [  # 建议基数个redis实例
        Redis(host="192.168.1.243", port=6379),
        # Redis(host="localhost", port=6380),
        # Redis(host="localhost", port=2345),
    ]

    @staticmethod
    def do_something(idx, lock, another_lock):
        # 如果do_something耗时大于锁生存周期timeout,会出现并发问题,总耗时变小
        # 如果锁内部token未使用threading.local存储,会出现并发问题,总耗时变小(其他线程拿不到锁时会尝试释放锁导致误删)
        print('Im doing something in idx {}'.format(idx))
        if idx & 1:
            lock = another_lock
        with lock:
            time.sleep(2)

    def test_redlock(self):
        t1 = time.monotonic()
        room_lock = Redlock(self.servers, 'room', timeout=3, thread_local=False)
        song_lock = Redlock(self.servers, 'song', timeout=3, thread_local=False)
        threads = [threading.Thread(target=TestLock.do_something, args=(idx, room_lock, song_lock)) for idx in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        print(f'cost {time.monotonic() - t1} seconds')

    @staticmethod
    def acquire_read_rlock_work(lock, name):
        with lock.acquire_read_rlock('test', blocking_timeout_s=.5):
            print(f"{name} get read lock")
            time.sleep(2)

    @staticmethod
    def acquire_write_rlock_work(lock, name):
        with lock.acquire_write_rlock('test', blocking_timeout_s=.5):
            print(f"{name} get write lock")
            time.sleep(2)

    @staticmethod
    def acquire_read_write_rlock_work(lock, name):
        with lock.acquire_write_rlock('test', blocking_timeout_s=.5):
            print(f"{name} get write lock")
            with lock.acquire_read_rlock('test', blocking_timeout_s=.5):
                print(f"{name} get read lock")
        print(f"{name} has release read and write locks")
        with lock.acquire_read_rlock('test', blocking_timeout_s=.5):
            print(f"{name} get read lock")
            with lock.acquire_write_rlock('test', blocking_timeout_s=.5):
                print(f"{name} get write lock")

    @staticmethod
    def acquire_rlock_work(lock: ReadWriteRLock, name):
        with lock.acquire_write_rlock('test', blocking_timeout_s=.5):
            print(f"{name} get write lock")
            with lock.acquire_write_rlock('test', blocking_timeout_s=.5):
                print(f"{name} get write lock")
                with lock.acquire_read_rlock('test', blocking_timeout_s=.5):
                    print(f"{name} get read lock")
                    with lock.acquire_read_rlock('test', blocking_timeout_s=.5):
                        print(f"{name} get read lock")
                    print(f"{name} has release read lock")
                    # 模拟释放写锁
                    lock.rds.fcall("release_write_rlock", 1, 'test', lock.write_rlock_name())
                    lock.rds.fcall("release_write_rlock", 1, 'test', lock.write_rlock_name())
                    print(f"{name} has release all write locks")
                    time.sleep(2)

    def test_read_write_rlock(self):
        lock = ReadWriteRLock(self.servers[0])

        def test_scenario_one():
            # 线程A获取了读锁
            # 线程B尝试获取读锁, 获取成功
            # 线程C尝试获取写锁, 获取失败
            threads = [
                threading.Thread(target=self.__class__.acquire_read_rlock_work, args=(lock, 'thread_a')),
                threading.Thread(target=self.__class__.acquire_read_rlock_work, args=(lock, 'thread_b')),
                threading.Thread(target=self.__class__.acquire_write_rlock_work, args=(lock, 'thread_c')),
            ]
            for thread in threads:
                thread.start()
                time.sleep(.4)

        def test_scenario_two():
            # 线程A获取了写锁
            # 线程B尝试获取读锁, 获取失败
            # 线程C尝试获取写锁, 获取失败
            threads = [
                threading.Thread(target=self.__class__.acquire_write_rlock_work, args=(lock, 'thread_a')),
                threading.Thread(target=self.__class__.acquire_read_rlock_work, args=(lock, 'thread_b')),
                threading.Thread(target=self.__class__.acquire_write_rlock_work, args=(lock, 'thread_c')),
            ]
            for thread in threads:
                thread.start()
                time.sleep(.4)

        def test_scenario_three():
            # 线程A获取了写锁
            # 线程A尝试获取读锁, 获取成功
            # 线程A释放读写锁
            # 线程A获取了读锁
            # 线程A尝试获取写锁, 获取失败
            thread = threading.Thread(target=self.__class__.acquire_read_write_rlock_work, args=(lock, 'thread_a'))
            thread.start()

        def test_scenario_four():
            # 线程A获取了写锁
            # 线程A再次尝试获取写锁, 获取成功
            # 线程A尝试获取读锁, 获取成功
            # 线程A再次尝试获取读锁, 获取成功
            # 线程A释放读锁, 线程A还是持有读锁
            # 线程A释放写锁, 线程A还是持有写锁
            # 线程A释放写锁, 线程A不再持有写锁
            # 线程B尝试获取读锁, 获取成功
            threads = [
                threading.Thread(target=self.__class__.acquire_rlock_work, args=(lock, 'thread_a')),
                threading.Thread(target=self.__class__.acquire_read_rlock_work, args=(lock, 'thread_b')),
            ]
            for thread in threads:
                thread.start()
                time.sleep(.4)

        # test_scenario_one()
        # test_scenario_two()
        # test_scenario_three()
        test_scenario_four()


if __name__ == '__main__':
    test = TestLock()
    # test.test_redlock()
    test.test_read_write_rlock()
