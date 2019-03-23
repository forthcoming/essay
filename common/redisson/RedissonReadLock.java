public class RedissonReadLock extends RedissonLock implements RLock {
    
    String getWriteLockName(long threadId) {
        return super.getLockName(threadId) + ":write";
    }

    String getReadWriteTimeoutNamePrefix(long threadId) {
        return suffixName(getName(), getLockName(threadId)) + ":rwlock_timeout"; 
    }
    
    '''
    tryLockInnerAsync方法是读锁加锁的最终方法
    KEYS[1]: 锁在redis中的key
    KEYS[2]: 超时名称的前缀
    ARGV[1]: 锁超时时间
    ARGV[2]: 锁的名称
    ARGV[3]: 写锁的名称,它是在锁名称的后面加上write
    加锁流程如下:
    1. 获取锁的mode,如果锁的mode为false,表示之前没有设置过读写锁,此时可以获得读锁.
        1. 将锁的mode设置为read
        2. 将锁名称对应的线程数设置为1
        3. 设置超时名称
        4. 设置超时名称的过期时间
        5. 设置锁的过期时间
    2. 如果锁的mode为read或者mode为write并且持有写锁的线程为当前线程,此时可以继续加读锁.换句话说,如果当前存在读锁或者持有写锁的是当前线程,都可以加读锁。
        1. 将锁名称对应的线程数增加1
        2. 设置超时名称
        3. 设置超时名称的过期时间
        4. 设置锁的过期时间
    3. 否则返回当前锁的过期时间
    '''
    @Override
    <T> RFuture<T> tryLockInnerAsync(long leaseTime, TimeUnit unit, long threadId, RedisStrictCommand<T> command) {
        internalLockLeaseTime = unit.toMillis(leaseTime);

        return commandExecutor.evalWriteAsync(getName(), LongCodec.INSTANCE, command,
                                "local mode = redis.call('hget', KEYS[1], 'mode'); " +
                                "if (mode == false) then " +
                                  "redis.call('hset', KEYS[1], 'mode', 'read'); " +
                                  "redis.call('hset', KEYS[1], ARGV[2], 1); " +
                                  "redis.call('set', KEYS[2] .. ':1', 1); " +
                                  "redis.call('pexpire', KEYS[2] .. ':1', ARGV[1]); " +
                                  "redis.call('pexpire', KEYS[1], ARGV[1]); " +
                                  "return nil; " +
                                "end; " +
                                "if (mode == 'read') or (mode == 'write' and redis.call('hexists', KEYS[1], ARGV[3]) == 1) then " +
                                  "local ind = redis.call('hincrby', KEYS[1], ARGV[2], 1); " + 
                                  "local key = KEYS[2] .. ':' .. ind;" +
                                  "redis.call('set', key, 1); " +
                                  "redis.call('pexpire', key, ARGV[1]); " +
                                  "redis.call('pexpire', KEYS[1], ARGV[1]); " +
                                  "return nil; " +
                                "end;" +
                                "return redis.call('pttl', KEYS[1]);",
                        Arrays.<Object>asList(getName(), getReadWriteTimeoutNamePrefix(threadId)), 
                        internalLockLeaseTime, getLockName(threadId), getWriteLockName(threadId));
    }
    
    '''
    unlockInnerAsync方法是读锁解锁的最终方法
    KEYS[1]: 锁在redis中的key
    KEYS[2]: channel名称,用于发送解锁的消息
    KEYS[3]: 超时名称的前缀
    KEYS[4]: key的前缀
    ARGV[1]: 解锁消息
    ARGV[2]: 锁的名称
    解锁流程如下: 
    1. 获取锁的mode,如果锁的mode为false,表示之前没有设置过读写锁,此时可以直接解锁,发送解锁消息,返回1
    2. 查看锁是否存在,如果不存在锁返回nil
    3. 将锁名称对应的线程数减1,如果剩余的线程数为0,表示没有其他线程持有该锁了,删除该锁
    4. 删除超时名称
    5. 如果当前锁结构对应的hash表大小大于1,表示有其他线程持有锁,遍历其中里面所有锁的超时时间,将最大的超时时间(maxRemainTime)作为整个锁结构的超时时间
       如果最大的超时时间(maxRemainTime)大于0,表示还有其他线程持有锁,不能完全释放锁,返回0,如果锁的mode为write返回0,不能释放写锁.
    6. 否则没有其他线程持有锁,此时可以彻底释放锁,删除锁结构,发送解锁消息,返回1
    '''
    @Override
    protected RFuture<Boolean> unlockInnerAsync(long threadId) {
        String timeoutPrefix = getReadWriteTimeoutNamePrefix(threadId);
        String keyPrefix = getKeyPrefix(threadId, timeoutPrefix);

        return commandExecutor.evalWriteAsync(getName(), LongCodec.INSTANCE, RedisCommands.EVAL_BOOLEAN,
                "local mode = redis.call('hget', KEYS[1], 'mode'); " +
                "if (mode == false) then " +
                    "redis.call('publish', KEYS[2], ARGV[1]); " +
                    "return 1; " +
                "end; " +
                "local lockExists = redis.call('hexists', KEYS[1], ARGV[2]); " +
                "if (lockExists == 0) then " +
                    "return nil;" +
                "end; " +
                    
                "local counter = redis.call('hincrby', KEYS[1], ARGV[2], -1); " + 
                "if (counter == 0) then " +
                    "redis.call('hdel', KEYS[1], ARGV[2]); " + 
                "end;" +
                "redis.call('del', KEYS[3] .. ':' .. (counter+1)); " +
                
                "if (redis.call('hlen', KEYS[1]) > 1) then " +
                    "local maxRemainTime = -3; " + 
                    "local keys = redis.call('hkeys', KEYS[1]); " + 
                    "for n, key in ipairs(keys) do " + 
                        "counter = tonumber(redis.call('hget', KEYS[1], key)); " + 
                        "if type(counter) == 'number' then " + 
                            "for i=counter, 1, -1 do " + 
                                "local remainTime = redis.call('pttl', KEYS[4] .. ':' .. key .. ':rwlock_timeout:' .. i); " + 
                                "maxRemainTime = math.max(remainTime, maxRemainTime);" + 
                            "end; " + 
                        "end; " + 
                    "end; " +
                            
                    "if maxRemainTime > 0 then " +
                        "redis.call('pexpire', KEYS[1], maxRemainTime); " +
                        "return 0; " +
                    "end;" + 
                        
                    "if mode == 'write' then " + 
                        "return 0;" + 
                    "end; " +
                "end; " +
                    
                "redis.call('del', KEYS[1]); " +
                "redis.call('publish', KEYS[2], ARGV[1]); " +
                "return 1; ",
                Arrays.<Object>asList(getName(), getChannelName(), timeoutPrefix, keyPrefix), 
                LockPubSub.UNLOCK_MESSAGE, getLockName(threadId));
    }

    @Override
    protected RFuture<Boolean> renewExpirationAsync(long threadId) {
        String timeoutPrefix = getReadWriteTimeoutNamePrefix(threadId);
        String keyPrefix = getKeyPrefix(threadId, timeoutPrefix);
        
        return commandExecutor.evalWriteAsync(getName(), LongCodec.INSTANCE, RedisCommands.EVAL_BOOLEAN,
                "local counter = redis.call('hget', KEYS[1], ARGV[2]); " +
                "if (counter ~= false) then " +
                    "redis.call('pexpire', KEYS[1], ARGV[1]); " +
                    
                    "if (redis.call('hlen', KEYS[1]) > 1) then " +
                        "local keys = redis.call('hkeys', KEYS[1]); " + 
                        "for n, key in ipairs(keys) do " + 
                            "counter = tonumber(redis.call('hget', KEYS[1], key)); " + 
                            "if type(counter) == 'number' then " + 
                                "for i=counter, 1, -1 do " + 
                                    "redis.call('pexpire', KEYS[2] .. ':' .. key .. ':rwlock_timeout:' .. i, ARGV[1]); " + 
                                "end; " + 
                            "end; " + 
                        "end; " +
                    "end; " +
                    
                    "return 1; " +
                "end; " +
                "return 0;",
            Arrays.<Object>asList(getName(), keyPrefix), 
            internalLockLeaseTime, getLockName(threadId));
    }
    

    @Override
    public RFuture<Boolean> forceUnlockAsync() {
        cancelExpirationRenewal(null);
        return commandExecutor.evalWriteAsync(getName(), LongCodec.INSTANCE, RedisCommands.EVAL_BOOLEAN,
                "if (redis.call('hget', KEYS[1], 'mode') == 'read') then " +
                    "redis.call('del', KEYS[1]); " +
                    "redis.call('publish', KEYS[2], ARGV[1]); " +
                    "return 1; " +
                "end; " +
                "return 0; ",
                Arrays.<Object>asList(getName(), getChannelName()), LockPubSub.UNLOCK_MESSAGE);
    }

}
