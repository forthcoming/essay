public class RedissonWriteLock extends RedissonLock implements RLock {

    @Override
    protected String getLockName(long threadId) {
        return super.getLockName(threadId) + ":write";
    }
    
    '''
    tryLockInnerAsync方法是写锁加锁的最终方法
    KEYS[1]: 锁在redis中的key
    ARGV[1]: 锁的超时时间
    ARGV[2]: 锁的名称
    加锁流程如下: 
    1. 获取锁的mode,如果锁的mode为false,表示之前没有设置过读写锁,此时可以获得写锁
        1. 将锁的mode设置为write,将锁名称对应的线程数设置为1
        2. 设置锁的过期时间
    2. 如果锁的mode为write,并且持有写锁的线程为当前线程,此时可以继续加写锁
        1. 将锁名称对应的线程数增加1
        2. 增加锁的过期时间
    3. 否则返回当前锁的过期时间
    '''
    @Override
    <T> RFuture<T> tryLockInnerAsync(long leaseTime, TimeUnit unit, long threadId, RedisStrictCommand<T> command) {
        internalLockLeaseTime = unit.toMillis(leaseTime);

        return commandExecutor.evalWriteAsync(getName(), LongCodec.INSTANCE, command,
                            "local mode = redis.call('hget', KEYS[1], 'mode'); " +
                            "if (mode == false) then " +
                                "redis.call('hmset', KEYS[1], 'mode', 'write', ARGV[2], 1); " +
                                "redis.call('pexpire', KEYS[1], ARGV[1]); " +
                                "return nil; " +
                            "end; " +
                            "if (mode == 'write') then " +
                                "if (redis.call('hexists', KEYS[1], ARGV[2]) == 1) then " +
                                    "redis.call('hincrby', KEYS[1], ARGV[2], 1); " + 
                                    "local currentExpire = redis.call('pttl', KEYS[1]); " +
                                    "redis.call('pexpire', KEYS[1], currentExpire + ARGV[1]); " +
                                    "return nil; " +
                                "end; " +
                            "end;" +
                            "return redis.call('pttl', KEYS[1]);",
                        Arrays.<Object>asList(getName()), 
                        internalLockLeaseTime, getLockName(threadId));
    }
    
    '''
    unlockInnerAsync方法是写锁解锁的最终方法
    KEYS[1]: 锁在redis中的key
    KEYS[2]: channel名称,用于发送解锁的消息
    ARGV[1]: 解锁消息
    ARGV[2]: 锁的过期时间
    ARGV[3]: 锁的名称
    解锁流程如下:
    1. 获取锁的mode,如果锁的mode为false,表示之前没有设置过读写锁,此时可以直接解锁,发送解锁消息,返回1
    2. 如果锁的mode为write
        1. 检查锁是否存在,如果不存在则返回nil
        2. 将锁名称对应的线程数减1,如果剩余的线程数大于0,表示还有其他线程持有该锁,重新设置锁结构的过期时间
        3. 如果剩余的线程数为0,表示没有其他线程持有该写锁了,于是删除该锁,返回1.
           如果当前锁结构对应的hash表大小等于1,表示没有其他线程持有锁,此时可以彻底释放锁,删除锁结构,发送解锁消息,
           否则表示还存在读锁,于是将锁的mode设置为read
    '''
    @Override
    protected RFuture<Boolean> unlockInnerAsync(long threadId) {
        return commandExecutor.evalWriteAsync(getName(), LongCodec.INSTANCE, RedisCommands.EVAL_BOOLEAN,
                "local mode = redis.call('hget', KEYS[1], 'mode'); " +
                "if (mode == false) then " +
                    "redis.call('publish', KEYS[2], ARGV[1]); " +
                    "return 1; " +
                "end;" +
                "if (mode == 'write') then " +
                    "local lockExists = redis.call('hexists', KEYS[1], ARGV[3]); " +
                    "if (lockExists == 0) then " +
                        "return nil;" +
                    "else " +
                        "local counter = redis.call('hincrby', KEYS[1], ARGV[3], -1); " +
                        "if (counter > 0) then " +
                            "redis.call('pexpire', KEYS[1], ARGV[2]); " +
                            "return 0; " +
                        "else " +
                            "redis.call('hdel', KEYS[1], ARGV[3]); " +
                            "if (redis.call('hlen', KEYS[1]) == 1) then " +
                                "redis.call('del', KEYS[1]); " +
                                "redis.call('publish', KEYS[2], ARGV[1]); " + 
                            "else " +
                                "redis.call('hset', KEYS[1], 'mode', 'read'); " +   // has unlocked read-locks
                            "end; " +
                            "return 1; "+
                        "end; " +
                    "end; " +
                "end; " +
                "return nil;",
        Arrays.<Object>asList(getName(), getChannelName()), 
        LockPubSub.READ_UNLOCK_MESSAGE, internalLockLeaseTime, getLockName(threadId));
    }

    @Override
    public RFuture<Boolean> forceUnlockAsync() {
        cancelExpirationRenewal(null);
        return commandExecutor.evalWriteAsync(getName(), LongCodec.INSTANCE, RedisCommands.EVAL_BOOLEAN,
              "if (redis.call('hget', KEYS[1], 'mode') == 'write') then " +
                  "redis.call('del', KEYS[1]); " +
                  "redis.call('publish', KEYS[2], ARGV[1]); " +
                  "return 1; " +
              "end; " +
              "return 0; ",
              Arrays.<Object>asList(getName(), getChannelName()), LockPubSub.READ_UNLOCK_MESSAGE);
    }

}
