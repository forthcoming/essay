# -*- coding: utf-8 -*-
import functools
import os
import pickle
import random
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from functools import wraps

from flask import request
from rediscluster import RedisCluster

startup_nodes = [
    {"host": "localhost", "port": "8001"},
    {"host": "localhost", "port": "8002"},
    {"host": "localhost", "port": "8003"},
    {"host": "localhost", "port": "8004"},
    {"host": "localhost", "port": "8005"},
    {"host": "localhost", "port": "8006"},
]
rc = RedisCluster(startup_nodes=startup_nodes)


class RedisCache:  # 接口缓存
    def __init__(self, client, default_timeout=300, key_prefix=None):
        self._client = client  # decode_responses is not supported by RedisCache
        self.key_prefix = key_prefix or ''
        self.default_timeout = default_timeout

    def cached(self, timeout=None, key_prefix="view%s"):
        def decorator(f):
            @functools.wraps(f)
            def decorated_function(*args, **kwargs):
                cache_key = _make_cache_key()
                rv = self.get(cache_key)
                if rv is None:
                    rv = f(*args, **kwargs)
                    self.set(cache_key, rv, timeout)
                return rv

            def _make_cache_key():
                if callable(key_prefix):
                    cache_key = key_prefix()
                elif "%s" in key_prefix:
                    cache_key = key_prefix % request.path
                else:
                    cache_key = key_prefix
                return cache_key

            return decorated_function

        return decorator

    @staticmethod
    def dump_object(value):
        # Dumps an object into a string for redis.By default it serializes integers as regular string and pickle dumps everything else.
        if type(value) is int:
            return str(value).encode('ascii')
        return b'!' + pickle.dumps(value)

    @staticmethod
    def load_object(value):
        if value is None:
            return None
        if value.startswith(b'!'):
            try:
                return pickle.loads(value[1:])
            except pickle.PickleError:
                return None
        return int(value)

    def get(self, key):
        return RedisCache.load_object(self._client.get(self.key_prefix + key))

    def set(self, key, value, timeout=None):
        timeout = timeout or self.default_timeout
        dump = RedisCache.dump_object(value)
        if timeout == -1:
            return self._client.set(name=self.key_prefix + key, value=dump)
        return self._client.setex(name=self.key_prefix + key, time=timeout, value=dump)

    def get_many(self, *keys):
        if self.key_prefix:
            keys = [self.key_prefix + key for key in keys]
        return [RedisCache.load_object(x) for x in self._client.mget(keys)]

    def set_many(self, mapping, timeout=None):
        timeout = timeout or self.default_timeout
        # Use transaction=False to batch without calling redis MULTI which is not supported by twemproxy
        pipe = self._client.pipeline(transaction=False)

        for key, value in mapping.items():
            dump = RedisCache.dump_object(value)
            if timeout == -1:
                pipe.set(name=self.key_prefix + key, value=dump)
            else:
                pipe.setex(name=self.key_prefix + key, time=timeout, value=dump)
        return pipe.execute()


cache = RedisCache(rc)


@cache.cached(timeout=250, key_prefix='test')
def test():
    import random
    return str(random.randint(0, 99)) + 'akatsuki'


class RateLimiter:
    # KEYS[1]: key_name
    # ARGV[1]: rate
    # ARGV[2]: interval
    rate_limiter_script = '''
        local currentValue = redis.call('get', KEYS[1]);
        if currentValue ~= false then
            if tonumber(currentValue) <= 0 then
                return redis.call('pttl', KEYS[1]);
            else
                redis.call('decr', KEYS[1]);
                return nil;
            end;
        else
            assert(tonumber(ARGV[1]) > 0, 'Requested permits amount could not exceed defined rate');
            redis.call('set', KEYS[1], ARGV[1]-1, 'px', ARGV[2]);
            return nil;
        end;
    '''

    rate_limiter_sha = rc.script_load(rate_limiter_script)

    def rate_limiter(self, rate, interval, use_ip=False, use_uid=False):
        def decorator(f):
            name_prefix = 'rate_limiter:{}:{}'.format(f.__module__.split('.')[-1], f.__name__)

            @wraps(f)  # 必须,不然flask会认为视图函数重名
            def wrapper(*args, **kwargs):
                ip = '0.0.0.0'
                uid = 0
                params = request.json or request.args or request.form
                if use_ip:
                    if 'X-Forwarded-For' in request.headers:
                        ip = request.headers['X-Forwarded-For'].split(',')[0]
                    else:
                        ip = request.remote_addr
                if use_uid:
                    uid = params.get('user_id', 0) or params.get('uid')
                key_name = '{}:{}:{}'.format(name_prefix, ip, uid)  # key_name组成必须放在这里,应为每次被装饰函数调用时这些值都不一样
                if rc.evalsha(self.rate_limiter_sha, 1, key_name, rate, interval):
                    print('{} reach the access limit,params:{}'.format(name_prefix, params))
                    raise  # 需要放在check_response之前装饰接口函数
                else:
                    return f(*args, **kwargs)

            return wrapper

        return decorator


class RWLock:
    """
    Referer:
        https://github.com/redisson/redisson/blob/master/redisson/src/main/java/org/redisson/RedissonWriteLock.java
        https://github.com/redisson/redisson/blob/master/redisson/src/main/java/org/redisson/RedissonReadLock.java
        https://blog.csdn.net/zhxdick/article/details/82693646
    todo:
    使用看门狗给锁续期
    使用发布订阅功能发布锁释放消息
    写锁优先

    分布式可重入读写锁(mode=read,只可能有读锁,但可以包含多个线程;mode=write,可能有读锁和写锁,但只可能包含一个线程,同一时刻只会按以下一种形式存在,写锁在特定条件下会转换成读锁)
    ###################################################
    rw_lock = { 'mode':'read','t1':2,'t2':3,'tn':2 }
    ----------------------------------------------------
    rw_lock = { 'mode':'write','t1:w':2,'t1':3 }
    ###################################################
    A线程加写锁成功
        1. 未加过读写锁
        2. A线程加过写锁
    A线程加读锁成功
        1. 未加过读写锁
        2. 加过读锁
        3. A加过写锁
    """

    # KEYS[1]: 锁在redis中的key
    # ARGV[1]: 锁超时时间
    # ARGV[2]: 锁的名称
    # ARGV[3]: 写锁的名称,它是在锁名称的后面加上write
    # 加锁流程如下:
    # 1. 获取锁的mode,如果锁的mode为false,表示之前没有设置过读写锁,此时可以获得读锁
    #     1. 将锁的mode设置为read,锁名称对应的线程数设置为1,并设置锁的过期时间
    # 2. 如果当前存在读锁或者持有写锁的是当前线程,都可以加读锁
    #     1. 将锁名称对应的线程数增加1,并设置锁的过期时间
    # 3. 否则返回false
    get_rlock_script = """
        local mode = redis.call('hget', KEYS[1], 'mode');
        if mode == false then
            redis.call('hmset', KEYS[1], 'mode', 'read', ARGV[2], 1);          
            redis.call('pexpire', KEYS[1], ARGV[1]);
            return true;
        end;
        if mode == 'read' or redis.call('hexists', KEYS[1], ARGV[3]) == 1 then  -- 如果是读锁或者本线程上过写锁
            redis.call('hincrby', KEYS[1], ARGV[2], 1);
            redis.call('pexpire', KEYS[1], ARGV[1]);
            return true;
        end;
        return false;
    """

    # KEYS[1]: 锁在redis中的key
    # ARGV[1]: 锁的名称
    # ARGV[2]: 锁的过期时间
    # 解锁流程如下:
    # 1. 获取锁的mode,如果锁的mode为false,表示之前没有设置过读写锁,此时可以直接解锁,返回1
    # 2. 查看锁是否存在,如果不存在锁返回nil
    # 3. 将锁名称对应的线程数减1,如果剩余的线程数为0,表示没有其他线程持有该锁了,删除该锁
    # 4. 如果当前锁结构对应的hash表大小大于1,表示有其他线程持有锁
    # 5. 否则没有其他线程持有锁,此时可以彻底释放锁,删除锁结构,返回1
    free_rlock_script = """
        local mode = redis.call('hget', KEYS[1], 'mode');

        if mode == false then
            return 1;
        end;

        if redis.call('hexists', KEYS[1], ARGV[1]) == 0 then
            return nil;
        end;

        if redis.call('hincrby', KEYS[1], ARGV[1], -1) == 0 then
            redis.call('hdel', KEYS[1], ARGV[1]);
        end;

        if redis.call('hlen', KEYS[1]) > 1 then
            redis.call('pexpire', KEYS[1], ARGV[2]);
            return 0;
        else
            redis.call('del', KEYS[1]);
            return 1;
        end;
    """

    # KEYS[1]: 锁在redis中的key
    # ARGV[1]: 锁的超时时间
    # ARGV[2]: 锁的名称
    # 加锁流程如下:
    # 1. 获取锁的mode,如果锁的mode为false,表示之前没有设置过读写锁,此时可以获得写锁
    #     1. 将锁的mode设置为write,将锁名称对应的线程数设置为1
    #     2. 设置锁的过期时间
    # 2. 如果持有写锁的线程为当前线程(hexists KEYS[1] ARGV[2]隐含mode=write),此时可以继续加写锁
    #     1. 将锁名称对应的线程数增加1
    #     2. 更新锁的过期时间
    # 3. 否则返回false
    get_wlock_script = """
        local mode = redis.call('hget', KEYS[1], 'mode');
        if mode == false then
            redis.call('hmset', KEYS[1], 'mode', 'write', ARGV[2], 1);
            redis.call('pexpire', KEYS[1], ARGV[1]);
            return true;
        end;
        if redis.call('hexists', KEYS[1], ARGV[2]) == 1 then
            redis.call('hincrby', KEYS[1], ARGV[2], 1);
            redis.call('pexpire', KEYS[1], ARGV[1]);
            return true;
        end;
        return false;
    """

    # KEYS[1]: 锁在redis中的key
    # ARGV[1]: 锁的过期时间
    # ARGV[2]: 锁的名称
    # 解锁流程如下:
    # 1. 获取锁的mode,如果锁的mode为false,表示之前没有设置过读写锁,此时可以直接解锁
    # 2. 如果锁的mode为read或者非本线程加的写锁,返回nil
    # 3. 将锁名称对应的线程数减1,如果剩余的线程数大于0,表示还有其他线程持有该锁,重新设置锁结构的过期时间
    # 4. 如果剩余的线程数为0,表示没有其他线程持有该写锁了,于是删除该锁
    #    如果当前锁结构对应的hash表大小等于1,表示没有其他线程持有锁,此时可以彻底释放锁,删除锁结构
    #    否则表示还存在读锁,于是将锁的mode设置为read
    free_wlock_script = """
        local mode = redis.call('hget', KEYS[1], 'mode');
        if mode == false then
            return 1;
        end;

        if redis.call('hexists', KEYS[1], ARGV[2]) == 0 then
            return nil;
        else
            if redis.call('hincrby', KEYS[1], ARGV[2], -1) > 0 then
                redis.call('pexpire', KEYS[1], ARGV[1]);
                return 0;
            else
                redis.call('hdel', KEYS[1], ARGV[2]);
                if redis.call('hlen', KEYS[1]) == 1 then
                    redis.call('del', KEYS[1]);
                else
                    redis.call('hset', KEYS[1], 'mode', 'read');   -- has unlocked read-locks,同线程会出现先释放写锁的情况??
                    redis.call('pexpire', KEYS[1], ARGV[1]);
                end;
                return 1;
            end;
        end;
    """

    get_rlock_sha = rc.script_load(get_rlock_script)
    free_rlock_sha = rc.script_load(free_rlock_script)
    get_wlock_sha = rc.script_load(get_wlock_script)
    free_wlock_sha = rc.script_load(free_wlock_script)

    def __init__(self, name_prefix, pttl=30000, timeout=30, thread_local=True):
        self.name_prefix = name_prefix
        self.pttl = pttl  # 锁过期时间,单位ms
        self.timeout = timeout  # 上锁最多重试时间,单位s
        self.local = threading.local() if thread_local else type('dummy', (), {})
        self.local.token = None

    def get_key(self, name):
        return '{}:{}'.format(self.name_prefix, name)

    def get_rlock_name(self):
        if self.local.token is None:
            self.local.token = os.urandom(16)
        return self.local.token

    def get_wlock_name(self):
        if self.local.token is None:
            self.local.token = os.urandom(16)
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
                if rc.evalsha(self.get_rlock_sha, 1, key, self.pttl, rlock_name, wlock_name):
                    yield
                    break
                cnt += 1
                time.sleep(max(random.uniform(0, .02) * cnt, .5))
            else:
                raise Exception('获取读锁超时')
        finally:
            rc.evalsha(self.free_rlock_sha, 1, key, self.pttl, rlock_name)  # 也可以处理mode='write'模式的写锁

    @contextmanager
    def get_wlock(self, name):
        key = self.get_key(name)
        wlock_name = self.get_wlock_name()
        stop_at = time.time() + self.timeout
        cnt = 0
        try:
            while time.time() < stop_at:
                if rc.evalsha(self.get_wlock_sha, 1, key, self.pttl, wlock_name):
                    yield
                    break
                cnt += 1
                time.sleep(max(random.uniform(0, .02) * cnt, .5))
            else:
                raise Exception('获取写锁超时')
        finally:
            rc.evalsha(self.free_wlock_sha, 1, key, self.pttl, wlock_name)


class DispatchWork:  # 功能类似分布式锁,保证同一时刻服务只在一台机器上运行
    # KEYS[1]: webapi_common_service_hbt:suffix:idx
    # ARGV[1]: ip
    # ARGV[2]: 过期时间
    running_status = '''
        local ip = redis.call('get',KEYS[1]);  -- 没有返回nil
        if ip==false then
            redis.call('setex',KEYS[1],ARGV[2],ARGV[1]);
            return true;
        elseif ip==ARGV[1] then
            redis.call('expire',KEYS[1],ARGV[2]);
            return true;
        else 
            return false;
        end
    '''
    running_status_sha = rc.script_load(running_status)

    def __init__(self, suffix):
        self.suffix = suffix

    def start(self, ip, working, work_timeout=4, cache_timeout=120):  # 服务只包含一个任务
        cache = 'webapi:{{common_service_hbt}}:{}:{}'.format(self.suffix, 0)
        count = 0
        while True:
            try:
                print('local ip: {},running machine: {},time: {}'.format(ip, rc.get(cache), datetime.now()))
                if rc.evalsha(self.running_status_sha, 1, cache, ip, cache_timeout):
                    working()
                    count = 0
            except Exception as e:
                print(e)
                print('update_rank_cache fail:{}:{}:{}'.format(ip, cache, working))  # 告警
                count += 1
                if count >= 5:  # 连续错误达到阈值
                    rc.delete(cache)  # 尽量保证切换到其他机器执行(非必须)
                    time.sleep(work_timeout)  # 尽量保证切换到其他机器执行(非必须)
                    os._exit(0)  # 退出子进程,由supervisord的autorestart=true机制重启程序
            time.sleep(work_timeout)

    def multiple_start(self, ip, workings, work_timeout=4):  # 服务包含多个任务
        count = 0
        while True:
            for name, working in workings.items():
                cache = 'webapi:{{common_service_hbt}}:{}:{}'.format(self.suffix, name)
                if rc.set(cache, ip, nx=True, px=10000):
                    print('work_name: {},cache_name: {},time: {}'.format(name, cache, datetime.now()))
                    try:
                        working()
                    except Exception as e:
                        print(e)
                        print('multiple_start fail:{}:{}:{}'.format(name, cache, working.__module__))  # 告警
                        count += 1
                        if count >= 5:
                            os._exit(0)  # 不会触发finally语句,退出子进程,由supervisord的autorestart=true机制重启程序
                    finally:
                        rc.expire(cache, work_timeout)  # 防止其他机器在work_timeout时间内执行相同任务
            print('multiple_start traversal over')
            time.sleep(work_timeout + .1)  # redis的key过期时间有一点点延迟


if __name__ == '__main__':
    print(test())
    print(test())
