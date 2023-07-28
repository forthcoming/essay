from functools import wraps

from flask import request
from redis.cluster import RedisCluster

rc: RedisCluster = RedisCluster(host="localhost", port=7000)


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
