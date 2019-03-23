https://github.com/redisson/redisson    
https://blog.wangqi.love/articles/redis/Redisson%E5%88%86%E5%B8%83%E5%BC%8F%E9%94%81%E7%9A%84%E5%AE%9E%E7%8E%B0.html    
RedissonFairLock是基于Redis的分布式可重入公平锁,它保证了当多个Redisson客户端线程同时请求加锁时,优先分配给先发出请求的线程   
RReadWriteLock是基于Redis的读写锁,该对象允许同时有多个读取锁,但是最多只能有一个写入锁.  
读写锁分为读锁和写锁两个对象,他们的实现类分别是RedissonReadLock和RedissonWriteLock.   

