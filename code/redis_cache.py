# -*- coding: utf-8 -*-
import functools
import os
import pickle
import time
from datetime import datetime
from functools import wraps

from flask import request
from redis.cluster import RedisCluster, ClusterNode

from tutorial import get_ip

startup_nodes = [
    ClusterNode(host="localhost", port=8001),
    ClusterNode(host="localhost", port=8002),
    ClusterNode(host="localhost", port=8003),
    ClusterNode(host="localhost", port=8004),
    ClusterNode(host="localhost", port=8005),
    ClusterNode(host="localhost", port=8006),
]
rc: RedisCluster = RedisCluster(startup_nodes=startup_nodes)


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

    def start(self, working, work_timeout=4, cache_timeout=120):  # 服务只包含一个任务
        ip = get_ip()
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

    def multiple_start(self, workings, work_timeout=4):  # 服务包含多个任务
        ip = get_ip()
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
