# -*- coding: utf-8 -*-
import functools,pickle
from flask import request
from rediscluster import StrictRedisCluster

startup_nodes = [
    {"host": "localhost", "port": "8001"}, 
    {"host": "localhost", "port": "8002"},
    {"host": "localhost", "port": "8003"},
    {"host": "localhost", "port": "8004"},
    {"host": "localhost", "port": "8005"},
    {"host": "localhost", "port": "8006"},
]
rc = StrictRedisCluster(startup_nodes=startup_nodes)

class RedisCache:  # 接口缓存
    def __init__(self, client, default_timeout=300, key_prefix=None):
        self._client = client  # decode_responses is not supported by RedisCache
        self.key_prefix = key_prefix or ''
        self.default_timeout = default_timeout

    def cached(self,timeout=None,key_prefix="view%s"):
        def decorator(f):
            @functools.wraps(f)
            def decorated_function(*args, **kwargs):
                cache_key = _make_cache_key()
                rv = self.get(cache_key)
                if rv is None:
                    rv = f(*args, **kwargs)
                    self.set(cache_key,rv,timeout)
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

    def dump_object(self, value):
        # Dumps an object into a string for redis.By default it serializes integers as regular string and pickle dumps everything else.
        if type(value) is int:
            return str(value).encode('ascii')
        return b'!' + pickle.dumps(value)

    def load_object(self, value):
        if value is None:
            return None
        if value.startswith(b'!'):
            try:
                return pickle.loads(value[1:])
            except pickle.PickleError:
                return None
        return int(value)

    def get(self, key):
        return self.load_object(self._client.get(self.key_prefix + key))

    def set(self, key, value, timeout=None):
        timeout = timeout or self.default_timeout
        dump = self.dump_object(value)
        if timeout == -1:
            return self._client.set(name=self.key_prefix + key,value=dump)
        return self._client.setex(name=self.key_prefix + key, time=timeout, value=dump)

    def get_many(self, *keys):
        if self.key_prefix:
            keys = [self.key_prefix + key for key in keys]
        return [self.load_object(x) for x in self._client.mget(keys)]

    def set_many(self, mapping, timeout=None):
        timeout = timeout or self.default_timeout
        # Use transaction=False to batch without calling redis MULTI which is not supported by twemproxy
        pipe = self._client.pipeline(transaction=False)

        for key, value in mapping.items():
            dump = self.dump_object(value)
            if timeout == -1:
                pipe.set(name=self.key_prefix + key, value=dump)
            else:
                pipe.setex(name=self.key_prefix + key, time=timeout, value=dump)
        return pipe.execute()

cache=RedisCache(rc)

@cache.cached(timeout=250,key_prefix='test')
def test():
    import random
    return str(random.randint(0,99))+'akatsuki'

if __name__=='__main__':
    print(test())
    print(test())
