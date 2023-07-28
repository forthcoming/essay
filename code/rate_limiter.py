from functools import wraps

from flask import request
from redis.cluster import RedisCluster


class TokenBucket:
    # TODO: 待完善(目前只有核心代码,去掉type相关逻辑,由于涉及到多个缓存,所以变量名需要用hash tag,以便集群下正常运行)
    # 令牌桶算法: 规定固定容量的桶,token以固定速度往桶内填充,当桶满时token不会被继续放入,每来一个请求把token从桶中移除,如果桶中没有token不能请求
    # 参考: https://github.com/redisson/redisson/blob/master/redisson/src/main/java/org/redisson/RedissonRateLimiter.java
    token_bucket = """#!lua name=token_bucket   
        local function try_set_rate(keys,args)   -- 初始化
            redis.call('hsetnx', keys[1], 'rate', args[1])
            return redis.call('hsetnx', keys[1], 'interval', args[2])
        end
    
        local function set_rate(keys,args)   -- 中途修改
            local valueName = keys[2]  -- {name}:value 记录当前令牌桶中的令牌数
            local permitsName = keys[3]  -- {name}:permits 是一个zset,member无实际意义,仅为了有序保存访问的时间戳score
            redis.call('hset', keys[1], 'rate', args[1], 'interval', args[2])
            redis.call('del', valueName, permitsName)
        end

        local function try_acquire(keys,args)   
            local rate = redis.call('hget', keys[1], 'rate')
            local interval = redis.call('hget', keys[1], 'interval')
            assert(rate ~= false and interval ~= false, 'RateLimiter is not initialized')
            
            local valueName = keys[2]
            local permitsName = keys[3]
            assert(tonumber(rate) >= tonumber(args[1]), 'Requested permits amount could not exceed defined rate')

            local currentValue = redis.call('get', valueName)
            local res
            if currentValue ~= false then
                local expiredValues = redis.call('zrangebyscore', permitsName, 0, tonumber(args[2]) - interval)
                local released = 0
                for i, v in ipairs(expiredValues) do
                     local random, permits = struct.unpack('Bc0I', v)
                     released = released + permits
                end

                if released > 0 then
                     redis.call('zremrangebyscore', permitsName, 0, tonumber(args[2]) - interval)
                     if tonumber(currentValue) + released > tonumber(rate) then
                          currentValue = tonumber(rate) - redis.call('zcard', permitsName)
                     else "
                          currentValue = tonumber(currentValue) + released
                     end
                     redis.call('set', valueName, currentValue)
                end

                if tonumber(currentValue) < tonumber(args[1]) then
                    local firstValue = redis.call('zrange', permitsName, 0, 0, 'withscores')
                    res = 3 + interval - (tonumber(args[2]) - tonumber(firstValue[2]))
                else "
                    redis.call('zadd', permitsName, args[2], struct.pack('Bc0I', string.len(args[3]), args[3], args[1]))
                    redis.call('decrby', valueName, args[1])
                    res = nil
                end
            else
                redis.call('set', valueName, rate - args[1])
                -- args[2]: 毫秒为单位的时间戳,args[3]: thread_local下的8位随机字符串,struct.pack类似于python的f字符串
                redis.call('zadd', permitsName, args[2], struct.pack('Bc0I', string.len(args[3]), args[3], args[1]))
                res = nil
            end

            local ttl = redis.call('pttl', keys[1])
            if ttl > 0 then
                redis.call('pexpire', valueName, ttl)
                redis.call('pexpire', permitsName, ttl)
            end
            return res
        end     

        local function available_permits(keys,args)   
            local rate = redis.call('hget', keys[1], 'rate')
            local interval = redis.call('hget', keys[1], 'interval')
            assert(rate ~= false and interval ~= false, 'RateLimiter is not initialized')

            local valueName = keys[2]
            local permitsName = keys[3]

            local currentValue = redis.call('get', valueName)
            if currentValue == false then
                redis.call('set', valueName, rate)
                return rate
            else
                local expiredValues = redis.call('zrangebyscore', permitsName, 0, tonumber(args[1]) - interval)
                local released = 0
                for i, v in ipairs(expiredValues) do
                     local random, permits = struct.unpack('Bc0I', v)
                     released = released + permits
                end

                if released > 0 then
                     redis.call('zremrangebyscore', permitsName, 0, tonumber(args[1]) - interval)
                     currentValue = tonumber(currentValue) + released
                     redis.call('set', valueName, currentValue)
                end

                return currentValue
            end   

        redis.register_function('try_set_rate', try_set_rate)
        redis.register_function('set_rate', set_rate)
        redis.register_function('try_acquire', try_acquire)
        redis.register_function('available_permits', available_permits)
    """
    is_register_script = False

    def __init__(self, rds, name, rate):
        self.rds = rds
        self.name = name
        self.rate = rate
        self.register_lib()

    def register_lib(self):
        if not self.__class__.is_register_script:
            self.rds.function_load(self.__class__.token_bucket, True)
            self.__class__.is_register_script = True


rc: RedisCluster = RedisCluster(host="localhost", port=7000)


class RateLimiter:  # 针对0.9秒1000请求和1.1秒1000请求这种场景无效
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
