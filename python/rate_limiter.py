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
