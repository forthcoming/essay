### generic
```
type key: 返回key类型 (eg:string, list, set, zset, hash and stream)
randomkey: 返回随机key
ttl key: 返回key剩余的过期时间秒数(不过期的key返回-1,不存在的key返回-2)
rename key newkey: 如果newkey已存在,则newkey的原值和过期时间被覆盖,当发生这种情况时会执行隐式del操作,集群模式下新旧key必须位于同一哈希槽中
del key [key ...]: 当key包含字符串以外的值时,该键的单独复杂度为O(M),其中M是列表、集合、排序集合或哈希中的元素数量
unlink key [key ...]: 在不同的线程中执行O(N)操作删除指定的key以回收内存,它不会阻塞,而del会阻塞
persist key: 把key置为永久有效
exists key [key ...]: 判断key是否存在, 返回1/0
expiretime key: 返回给定key到期的绝对Unix时间戳(以秒为单位)
expireat key unix-time-seconds [NX | XX | GT | LT]

expire key seconds [NX | XX | GT | LT],所有涉及更新key值的操作不会影响原本的过期时间,set命令是替换新建
密钥过期信息存储为绝对Unix时间戳,这意味着即使Redis实例不活动,时间也在流动,为了使过期功能正常工作,计算机时间必须保持稳定
即使正在运行的实例也会始终检查计算机时钟,如果您将key生存时间设置为1000秒,然后将计算机时间设置为未来2000秒,则该key将立即过期
key过期机制如下
key被动过期: 当某个客户端尝试访问它时,发现key超时
key主动过期: 定期(每秒10次,由配置变量hz控制)在设置了过期时间的key中随机测试一些(20个)键,所有已过期的key都将被删除,如果超过1/4的key已过期,再重新开始
内存淘汰机制: 由配置变量maxmemory-policy控制,常用策略allkeys-lru、volatile-lru等

keys pattern: 查找所有符合给定模式pattern的key,生产环境慎用,可考虑使用SCAN或集合
*:通配任意多个字符  ?:通配单个字符  []:通配括号内的某1个字符
127.0.0.1:6379> keys *
(empty list or set)
127.0.0.1:6379> mset one 1 two 2 three 3 four 4
OK
127.0.0.1:6379> keys o*
1) "one"
127.0.0.1:6379> keys ???
1) "one"
2) "two"
127.0.0.1:6379> keys on[dce]
1) "one"

scan cursor [MATCH pattern] [COUNT count] [TYPE type]: 遍历所有键,类似的还有sscan,hscan,zscan
游标从0开始,到0遍历结束,count只是个hint,返回的结果可多可少
遍历过程中如果有数据修改,改动后的数据能不能遍历到是不确定的,返回的结果可能会有重复
scan 0 match premissions:* count 100  

sort key [BY pattern] [LIMIT offset count] [GET pattern [GET pattern ...]] [ASC | DESC] [ALPHA] [STORE destination]
返回或保存给定列表、集合、有序集合key中经过排序的元素,只能根据一个字段排序(无法实现类似order by name,score功能),无法在集群下运行
排序默认以数字作为对象,值被解释为双精度浮点数,当需要对字符串进行排序时,需要显式地添加alpha修饰符
有序集合是根据member而非score排序
lpush rank 1 3 2 5 4
sort rank desc limit 1 3
1) "4"
2) "3"
3) "2"
zadd alphabet 10 a 20 c 0 b -10 e 30 d
sort alphabet alpha
1) "a"
2) "b"
3) "c"
4) "d"
5) "e"
lpush uid 1 2 3 4 0 5
hmset user_info_1 name admin level 9999
hmset user_info_2 name jack level 10
hmset user_info_3 name peter level 25
hmset user_info_4 name mary level 70
通过by可以让uid按其他键的元素来排序,不在user_level_*下面的uid默认比其他uid要小,且也会按指定顺序排序
sort uid by user_info_*->level
1) "0"
2) "5"
3) "2"
4) "3"
5) "4"
6) "1"
get #获取元素本身(被排序键的值),类似与sorted-set withscores
sort uid get # get user_info_*->name get user_info_*->level 
 1) "0"
 2) (nil)
 3) (nil)
 4) "1"
 5) "admin"
 6) "9999"
 7) "2"
 8) "jack"
 9) "10"
10) "3"
11) "peter"
12) "25"
13) "4"
14) "mary"
15) "70"
16) "5"
17) (nil)
18) (nil)
通过给store指定一个key,返回排序结果的元素个数,并将排序结果保存到给定key上,key类型是list
如果被指定key已存在,那么原有的值将被排序结果覆盖
sort uid by user_info_*->level store result
(integer) 6
lrange result 0 -1
1) "0"
2) "5"
3) "2"
4) "3"
5) "4"
6) "1"
通过将一个不存在的键作为参数传给by选项,可以跳过排序
通过将这种用法和GET选项配合,就可以在不排序的情况下获取多个外部键,类似于SQL的join
sort uid by not-exists-key get user_info_*->level get user_info_*->name
 1) (nil)
 2) (nil)
 3) (nil)
 4) (nil)
 5) "70"
 6) "mary"
 7) "25"
 8) "peter"
 9) "10"
10) "jack"
11) "9999"
12) "admin"
```

### connection
```
ping #测试服务器是否可用
select 0|1|2...: 从0到15编号,可从配置文件修改,所有数据库保留在同一个RDB/AOF文件中,集群无法使用
实际项目中数据库应该用于分隔属于同一应用的不同键,而不是为多个不相关的应用使用单个Redis实例
client id:  返回当前连接的ID,不重复且单调递增,ID大说明后来新建的连接
client info:  返回有关当前客户端连接服务器的信息和统计信息
client list [id client-id [client-id ...]]: 返回有关所有客户端连接服务器的信息和统计信息
client kill: 杀死某个连接 client kill addr 127.0.0.1:43501
```
>#### client info参数解读
- id: a unique 64-bit client ID
- addr: address/port of the client
- laddr: address/port of local address client connected to (bind address)
- fd: file descriptor corresponding to the socket
- name: the name set by the client with CLIENT SETNAME
- age: total duration of the connection in seconds
- idle: idle time of the connection in seconds
- flags: client flags (see below)
- db: current database ID
- sub: number of channel subscriptions
- psub: number of pattern matching subscriptions
- ssub: number of shard channel subscriptions. Added in Redis 7.0.3
- multi: number of commands in a MULTI/EXEC context
- qbuf: query buffer length (0 means no query pending)
- qbuf-free: free space of the query buffer (0 means the buffer is full)
- argv-mem: incomplete arguments for the next command (already extracted from query buffer)
- multi-mem: memory is used up by buffered multi commands. Added in Redis 7.0
- obl: output buffer length
- oll: output list length (replies are queued in this list when the buffer is full)
- omem: output buffer memory usage
- tot-mem: total memory consumed by this client in its various buffers
- events: file descriptor events (see below)
- cmd: last command played
- user: the authenticated username of the client
- redir: client id of current client tracking redirection
- resp: client RESP protocol version. Added in Redis 7.0

### bitmap
```
bitop and|or|xor|not destkey key1 [key2 ...]: 对key1,key2..keyN位运算,结果存到destkey
bitpos key bit [start [end]]: 返回字符串第一个设置为1或0的位置,范围参考getrange,默认单位是字节
bitcount key [start end]: 统计1的个数,范围参考getrange
getbit key offset: 获取值的二进制表示对应位上的值,offset从0编号,最大值2^32-1,so key最大为512M
setbit key offset 0|1: 设置offset对应二进制位上的值,返回该位上的旧值
当需要多次调用setbit完成初始化时,可以使用set来设置整个位图
位图不是实际的数据类型,而是在string类型上定义的一组面向位的操作,这意味着位图可以与字符串命令一起使用
127.0.0.1:6379> setbit lower 2 1
(integer) 0
127.0.0.1:6379> get lower
" "
127.0.0.1:6379> set char Q
OK
127.0.0.1:6379> bitop or char char lower
(integer) 1
127.0.0.1:6379> get char
"q"
```

### geospatial
```
geoadd key [NX | XX] [CH] longitude latitude member [longitude latitude member ...]
时间复杂度: O(log(N)) for each item added, 其中N是zset中的元素数量,数据存储在有序集合,score对应geohash的值
geohash值的前缀相同的位数越多,代表的位置越接近,反之不成立,位置接近的geoHash值不一定相似

geohash key [member [member ...]]: 返回一个包含指定元素位置的11个字符数组
geodist key member1 member2 [M | KM | FT | MI]
geopos key [member [member ...]]: 返回指定成员的经度、纬度

geosearch key <FROMMEMBER member | FROMLONLAT longitude latitude> 
<BYRADIUS radius <M | KM | FT | MI> | BYBOX width height <M | KM | FT | MI>> 
[ASC | DESC] [COUNT count [ANY]] [WITHCOORD] [WITHDIST] [WITHHASH]
Time complexity:O(N+log(M)) where N is the number of elements in the grid-aligned bounding box area 
around the shape provided as the filter and M is the number of items inside the shape
默认情况下匹配项返回时未排序,使用ANY选项时,一旦找到足够的匹配项就返回,这意味着结果可能不是最接近指定点的结果,但速度会快很多
```

### hash(字典)
```
hset key field value [field value ...]: 如果有field,则覆盖原field域的值
hsetnx key field value
hlen key: 返回key中元素的数量,时间复杂度O(1)
hkeys key: 返回key中所有的field,时间复杂度O(N)
hvals key: 返回key中所有的value
hexists key field: 判断key中有没有field域,时间复杂度O(1)
hdel key field [field ...]
hgetall key: 返回key中所有得field-value
hmget key field [field ...]
hincrbyfloat key field increment
hstrlen key field: 返回key中的field关联的值的字符串长度
```

### hyperloglog
```shell
pfcount key [key ...]: 当使用单个key时,时间复杂度O(1),用12k(加上键本身的几个字节)内存来计算集合中唯一元素个数,标准误差为0.81%
当使用多个key时,在内部将存储在key处的数据结构合并到临时HyperLogLog中,返回并集,比较慢慎用
HyperLogLog使用双重表示法来表示:稀疏表示法适用于计算少量元素的HLL,而密集表示法适用于较高基数,当需要时Redis会自动从稀疏表示切换到稠密表示
存储结构是字符串,可以使用GET检索并使用SET恢复
127.0.0.1:6379> pfadd hll a b c d a      
(integer) 1       # 1 if at least 1 HyperLogLog internal register was altered. 0 otherwise.
127.0.0.1:6379> pfcount hll
(integer) 4
```

### list(链表+数组)
```
llen key: 计算key元素个数,时间复杂度O(1)
lindex key index: 返回index位置上的值,时间复杂度O(N),N是要遍历以到达索引处的元素的元素数,查询列表第一个或最后一个元素的时间复杂度为O(1)
ltrim key start stop: 使列表只存储[start,stop]范围内的数据,支持负索引,时间复杂度O(N),N是操作要删除的元素数量
lset key index element: 时间复杂度O(N),N是list长度
lrange key start stop: 返回list中[start, stop]中的元素,左数从0开始,右数从-1开始
lrem key count element: 从列表里移除前count次出现的值为element的元素(count>0从头往尾,count<0从尾往头,count=0移除所有)
lmove source destination <LEFT | RIGHT> <LEFT | RIGHT>: 原子地返回并删除源中第一/最后个元素,并将该元素存到目标列表第一/最后个元素
blmove source destination <LEFT | RIGHT> <LEFT | RIGHT> timeout: lmove阻塞版

lpush key element [element ...]: 把值按顺意一个个插入到list头部,类似还有rpush
lpop key [count]: 从list头部按顺序一个个弹出count个元素,类似还有rpop
blpop key [key ...] timeout: 类似还有brpop
lpop阻塞版,超时为零可无限阻塞,当没有元素可以从给定列表弹出时,会阻塞连接直到超时或发现可弹出元素
当给定多个key参数时,按key的先后顺序依次检查各个列表,弹出第一个非空列表的名字和头元素
相同的key可以被多个客户端同时阻塞,不同的客户端被放进一个队列中,按先阻塞先服务(first-BLPOP,first-served)顺序为客户端执行BLPOP命令
如果list在同一时刻接收到多个元素(LPUSH,MULTI块,Lua脚本),会等元素接受完再执行blpop,下面Client B会接受c
Client A: BLPOP foo 0
Client B: LPUSH foo a b c
可与管道一起使用,但这种设置仅在它是管道的最后一个命令时才有意义,在MULTI/EXEC块内使用阻塞命令没有意义,行为表现为对应的非阻塞版命令

lmpop numkeys key [key ...] <LEFT | RIGHT> [COUNT count]: 从key列表中的第一个非空列表键中弹出一个或多个元素
blmpop timeout numkeys key [key ...] <LEFT | RIGHT> [COUNT count]: lmpop阻塞版
redis> LPUSH mylist "1" "2" "3"
(integer) 3
redis> LPUSH mylist2 "a" "b" "c" "d" "e"
(integer) 5
redis> LMPOP 2 mylist mylist2 right count 4
1) "mylist"
2) 1) "1"
   2) "2"
   3) "3"
redis> LRANGE mylist 0 -1
(empty array)
redis> LMPOP 2 mylist mylist2 right count 2
1) "mylist2"
2) 1) "a"
   2) "b"
```

### 发布订阅(建议使用redis stream代替)
```
subscribe channel [channel ...]: 客户端订阅指定频道
psubscribe pattern [pattern ...]: 客户端订阅给定的模式,匹配规则同keys
subscribe foo
psubscribe f*
if a message is sent to channel foo, the client will receive two messages: one of type message and one of type pmessage.

unsubscribe [channel [channel ...]]: 取消客户端对给定频道的订阅,如果没有给定频道则取消订阅所有频道
punsubscribe [pattern [pattern ...]]: 参考unsubscribe

publish channel message: 将消息发布到给定频道,时间复杂度O(N+M),N是订阅接收通道的客户端数量,M是订阅模式的任何客户端总数
在集群中可以发布到每个节点,因此客户端可以通过连接任何一个节点来订阅任何频道,返回收到消息的客户端数量,在集群中只统计同一节点接收的客户端数量

pubsub numpat: 返回所有客户端PSUBSCRIBE订阅的唯一模式的总数(不是订阅模式的客户端计数)
pubsub channels [pattern]: 列出当前活跃频道,活跃频道是具有一个或多个订阅者(不包括订阅模式的客户端)的通道
如果未指定模式,则列出所有通道,如果指定模式,则仅列出与指定模式匹配的通道
消息将被传递一次,如果订阅者无法处理消息(如错误或网络断开),则消息将永远丢失,不支持数据持久化
pubsub numsub [channel [channel ...]]: 返回指定通道的订阅者数量(不包括订阅模式的客户端)
```
```python
from redis import Redis

r = Redis()
p = r.pubsub()
p.subscribe('my-first-channel')
p.psubscribe('my-*')
r.publish('my-first-channel', 'some data')
print(p.get_message())
print(p.get_message())
print(p.get_message())
print(p.get_message())
print(p.get_message())
r.publish('my-first-channel', 'some data')
print(p.get_message())
print(p.get_message())
print(p.get_message())
'''
With [un]subscribe messages, this value will be the number of channels and patterns the connection is currently subscribed to.
With [p]message messages, this value will be the actual published message.
{'type': 'subscribe', 'pattern': None, 'channel': b'my-first-channel', 'data': 1}
{'type': 'psubscribe', 'pattern': None, 'channel': b'my-*', 'data': 2}
{'type': 'message', 'pattern': None, 'channel': b'my-first-channel', 'data': b'some data'}
{'type': 'pmessage', 'pattern': b'my-*', 'channel': b'my-first-channel', 'data': b'some data'}
None
{'type': 'message', 'pattern': None, 'channel': b'my-first-channel', 'data': b'some data'}
{'type': 'pmessage', 'pattern': b'my-*', 'channel': b'my-first-channel', 'data': b'some data'}
None
'''
```

### scripting and functions
```
script flush [ASYNC | SYNC]: 清空所有脚本缓存,redis重启or关闭也会触发该命令
script load script: 将脚本加载到脚本缓存中,但不执行,返回脚本的SHA1摘要(sha1(b'lua script').hexdigest())
evalsha sha1 numkeys [key [key ...]] [arg [arg ...]]: 与eval相似,前提是sha1已被注册
eval script numkeys [key [key ...]] [arg [arg ...]]: 脚本以原子方式执行,执行脚本时不会执行其他脚本或命令,类似于MULTI/EXEC
为了确保脚本正确执行,脚本访问的所有keys都必须显式提供为输入键参数,而不应访问具有以编程方式生成的key
eval "return redis.call('get', KEYS[1])" 1 zgt  # 执行脚本,返回脚本的值,并注册脚本的sha值到redis
```


### string
```
append key value
incr key: key值加1,并返回加1后的值,key必须是数字型字符串,不存在时初始值为0,对立操作是decr
get key
decrby key decrement
incrbyfloat key increment
setrange key offset value: 把字符串key的第offset个位置起替换成value,只覆盖value个长度
getrange key start stop: 获取字符串中[start, stop]范围的值，左数从0开始,右数从-1开始
mget key1 key2...: 类似的还有mset
strlen key: 返回存储在key处的字符串值的长度
lcs key1 key2 [LEN]: 返回最长公共子串,len意思是只返回子串长度
set key value [NX | XX] [GET] [PX milliseconds | EXAT unix-time-seconds | KEEPTTL]
如果key已存在,则无论其类型如何都会被覆盖,成功后该key先前生存时间将被丢弃
[NX | XX]-- key[不存在|存在]时生效
GET -- Return the old string stored at key
PX milliseconds -- 设置指定的过期时间,以毫秒为单位
EXAT timestamp-seconds -- 设置key过期的指定Unix时间,以秒为单位
KEEPTTL -- 保留key原有的生存周期
```

### set(唯一性,无序性)
```
sadd key value1 value2:往集合key中增加元素
srem key value1 value2: 删除集合中集为value1 value2的元素,返回实际删除的元素个数
spop key:返回并删除集合中key中1个随机元素
srandmember key n:返回集合key中随机的n个不相同元素,默认返回1个,当n大于集合元素总数时顺序不再随机
smembers key:返回集中所有的元素
sismember key value:判断value是否在 key集合中
scard key:返回集合中元素的个数
smove source dest value:把source中的 value删除 ,并添加到 dest集合中
sinter  key1 key2 key3: 求出key1 key2 key3三个集合中的交集(公共部分) ,并返回
sinterstore dest key1 key2 key3:求出key1 key2 key3 三个集合中的交集 ,并赋给dest
suion key1 key2.. Keyn:求出key1 key2 keyn的并集并返回(类似的还有sunionstore)
sdiff key1 key2 key3:求出key1与key2 key3的差集,即key1-key2-key3
```

### zset(有序集合)
```
zadd key score1 value1 score2 value2:如果添加的成员已经存在于有序集合中,则会更新成员的score并更新到正确的排序位置
zincrby key increment member: 如果member不在有序集合,it is added with increment as its score (as if its previous score was 0.0). 如果key不存在,会先创建一个只带有member的有序集合
zcard key: 返回元素个数
zrem key value1 value2: 删除集合中的元素
zrank key member: 返回member的排名(升续0名开始)
zrevrank key memeber:查询member的排名(降续0名开始)
zrange key start stop [withscores]:返回名次[start,stop]的元素,默认升续排列,Withscores是把score也打印出来(类似的还有zrevrange)
zrangebyscore  key min max [withscores] limit m n: 取score在 [min,max]内的元素
zcount key min max:返回[min,max] 区间内元素的数量
zremrangebyrank key start end:按排名删除元素,删除名次在 [start,end]之间的
zremrangebyscore key min max:按照socre来删除元素,删除 score在 [min,max]之间的
说明: 
score类型是double,按键score的大小顺序存放
虽然double类型精度是15位小数,但并不意味着一定可以精确保存15位小数,如2.4503599627370496,参考c语言浮点数内存表示
```


```
通用操作
redis-py存进去的是数字类型,再取出来时都会是字符串类型
redis-cli -h 10.1.138.63 -n 1 --bigkeys -i 0.01   # 分析数据库中的大key,-i参数表示扫描过程中每次扫描的时间间隔,单位是秒
redis-cli --eval Desktop/test.lua key1 key2 , argv1 argv2 # 注意逗号两边要用空格隔开

memory usage(时间复杂度：O(N) where N is the number of samples)
The MEMORY USAGE command reports the number of bytes that a key and its value require to be stored in RAM.Longer keys and values show asymptotically linear usage.
127.0.0.1:6379> memory usage avatar
(integer) 48
127.0.0.1:6379> memory usage avatar1
(integer) 49
For nested data types, the optional SAMPLES option can be provided, where count is the number of sampled nested values. 
By default, this option is set to 5. To sample the all of the nested values, use SAMPLES 0.
127.0.0.1:6379> hlen hkey                       // hkey有100w个字段,每个字段value长度介于1~1024字节
(integer) 1000000
127.0.0.1:6379> MEMORY usage hkey               //默认SAMPLES为5
(integer) 521588753
127.0.0.1:6379> MEMORY usage hkey SAMPLES 1000  //指定SAMPLES为1000
(integer) 617977753
127.0.0.1:6379> MEMORY usage hkey SAMPLES 10000 //指定SAMPLES为10000
(integer) 624950853
这是使用抽样求平均的算法,要想获取key较精确的内存值,就指定更大SAMPLES个数,但过大会占用CPU时间

Usage: redis-benchmark [-h <host>] [-p <port>] [-c <clients>] [-n <requests>]
 -h <hostname>      Server hostname (default 127.0.0.1)
 -p <port>          Server port (default 6379)
 -c <clients>       Number of parallel connections (default 50)
 -n <requests>      Total number of requests (default 100000)
 -d <size>          Data size of SET/GET value in bytes (default 3)
 --dbnum <db>       SELECT the specified db number (default 0)
 -q                 Quiet. Just show query/sec values
 -P <numreq>        Pipeline <numreq> requests. Default 1 (no pipeline).
 -t <tests>         Only run the comma separated list of tests. The test names are the same as the ones produced as output.

Examples:
 Use 20 parallel clients, for a total of 100k requests, against 192.168.1.1:
   $ redis-benchmark -h 192.168.1.1 -p 6379 -n 100000 -c 20

 Benchmark 127.0.0.1:6379 for a few commands:
   $ redis-benchmark -t ping,set,get -n 100000

 Benchmark a specific command line:
   $ redis-benchmark -r 10000 -n 10000 eval 'return redis.call("ping")' 0

---------------------------------------------------------------------------------------------------------------------------------------

monitor
streams back every command processed by the Redis server. It can help in understanding what is happening to the database
如果redis是集群,该命令只会监控指定ip:port下的key,可以看到哪个ip正在执行的所有redis操作
redis-cli -h 127.0.0.1 -p 8001 -a 'password' monitor |grep "common_service_hbt"   # redis没有用户名

安装redis到/usr/local/redis目录
$ wget http://download.redis.io/releases/redis-3.2.9.tar.gz
$ tar xzf redis-3.2.9.tar.gz
$ cd redis-3.2.9
$ make PREFIX=/opt/redis install #安装到指定目录中(没该目录则会自动创建)
$ mv redis.conf /opt/redis

ll ~/redis/bin
-rwxr-xr-x. 1 root root 2075842 Jan 31 01:10 redis-benchmark
-rwxr-xr-x. 1 root root   25173 Jan 31 01:10 redis-check-aof
-rwxr-xr-x. 1 root root   56020 Jan 31 01:10 redis-check-dump
-rwxr-xr-x. 1 root root 2205500 Jan 31 01:10 redis-cli
lrwxrwxrwx. 1 root root      12 Jan 31 01:10 redis-sentinel -> redis-server
-rwxr-xr-x. 1 root root 4358017 Jan 31 01:10 redis-server

redis-benchmark: redis性能测试工具
redis-check-aof: 检查aof日志的工具
redis-check-dump: 检查rbd日志的工具
redis-server /root/redis/redis.conf    # 指定启动redis时的配置文件


事务
redis由于是单进程执行命令,所以不存在并发事物和并发读写,也不需要读写锁,redis事务只需要保证原子性即可

import redis
r = redis.Redis(host='localhost', port=6379, db=0)
r.flushdb()
pipe = r.pipeline(transaction=True) # The following SET commands are buffered
pipe.set('bing', 'baz')
pipe.set('foo', 'bar').get('bing')  # 所有缓冲到pipeline的命令返回pipeline对象本身,因此可以链式调用
pipe.execute()  # returning a list of responses, one for each command.  [True, True, b'baz']

# pipelines can also ensure the buffered commands are executed atomically(原子性地) as a group. This happens by default. 
# If you want to disable the atomic nature of a pipeline but still want to buffer commands, you can turn off transactions.
# The pipeline is wrapped with the MULTI and EXEC statements by default when it is executed, which can be disabled by specifying transaction=False.
with r.pipeline(transaction=False) as pipe:  # 默认transaction=True,会在命令两端分别加multi和exec,管道对减少客户端和服务器之间来回开销很有用
    while True:
        try:
            pipe.watch('OUR-SEQUENCE-KEY')  # put a WATCH on the key that holds our sequence value
            # after WATCHing, the pipeline is put into immediate execution mode until we tell it to start buffering commands again.
            # this allows us to get the current value of our sequence
            current_value = pipe.get('OUR-SEQUENCE-KEY')
            next_value = int(current_value) + 1
            pipe.multi()   # now we can put the pipeline back into buffered mode with MULTI,此时不管初始话是否用事物,后面的命令会以transaction=True模式运行(原子性)
            pipe.set('OUR-SEQUENCE-KEY', next_value)
            time.sleep(10) # 可以在watch之后multi之前,此时如果OUR-SEQUENCE-KEY被其他客户端更改,execute将会抛WatchError异常
            pipe.execute() # finally, execute the pipeline (the set command)
            break
       except WatchError:  # if a WatchError wasn't raised during execution, everything we just did happened atomically.
            # another client must have changed 'OUR-SEQUENCE-KEY' between the time we started WATCHing it and the pipeline's execution.
            # our best bet is to just retry.
            continue
           
watch
要求所有受监控的键在执行exec前都没有被修改时才会执行事务(相同客户端在事务内部修改这些键不影响事务的运行)
只能在客户端进入事务状态之前执行才有效
当前客户端的事务执行失败,程序需要做的就是不断重试这个操作,直到没有发生碰撞为止
这种形式的锁被称作乐观锁,它是一种非常强大的锁机制.因为大多数情况下不同的客户端会访问不同的键,碰撞的情况一般都很少,所以通常并不需要进行重试

multi
It can never happen that a request issued by another client is served in the middle of the execution of a Redis transaction. 
This guarantees that the commands are executed as a single isolated operation.
Redis是单线程的服务,天生所有操作均具有原子性
事务状态是以一个事务为单位,执行事务队列中的所有命令:除非当前事务执行完毕,否则服务器不会中断事务,也不会执行其他客户端的其他命令
事物存在语法错误,则整个事务都不会执行
事务存在逻辑错误,比如set a 1,lpop a则会跳过该命令,执行剩下的命令,不支持回滚

exec
开始顺序执行各条命令,之后终止watch命令

discard
中止事务运行

客户端pipeline vs lua-script
pipeline优点:
    1. 集群中如果keys不落在同一个slot上,则只能用pipeline,无法使用脚本
lua-script优点:
    1. A Redis script(lua script) is transactional by definition and usually the script will be both simpler and faster
    2. 命令之间存在逻辑(如if,赋值等),则只能使用脚本,无法使用pipeline

--------------------------------------------------------------------------------------------------------

持久化(推荐两种方案同时使用)
快照(rdb)
每隔N分钟或者N次写操作后从内存dump数据形成rdb文件,压缩放在备份目录(导入导出速度快,容易出现丢失几分钟的数据,可以通过aof弥补)
快照配置选项
save 900 1           # 900内,有1 条写入,则产生快照
save 300 1000        # 如果300秒内有1000次写入,则产生快照(每300秒唤醒一次)
save 60 10000        # 如果60秒内有10000次写入,则产生快照(每60秒唤醒一次,从下往上看,这3个选项都屏蔽,则rdb禁用)

日志(aof)
# 注意在导出rdb过程中,aof如果停止同步,所有的操作缓存在内存的队列里,dump完成后统一操作
恢复时rdb比aof快,因为其是数据的内存映射,直接载入到内存,而aof是命令,需要逐条执行
当rdb跟aof同时开启时,则只加载aof里面的数据
主从关系中一般主开启aof,从开启一个rdb
当执行shutdown命令时会自动将内存中数据写进rdb(之前与aof不一致的数据会被覆盖掉)

---------------------------------------------------------------------------------------------------------

key设计原则
1: 把表名转换为key前缀,如tag
2: 放置用于区分key的字段,对应mysql中的主键的列名,如userid
3: 放置主键值,如2,3,4...., a , b ,c
4: 存储的列名

create table book (bookid int,title char(20))engine myisam charset utf8;
insert into book values(5 , 'PHP圣经'),(6 , 'ruby实战'),(7 , 'mysql运维')(8, 'ruby服务端编程');
create table tags (tid int,bookid int,content char(20))engine myisam charset utf8;
insert into tags values(10 , 5 , 'PHP'),(11 , 5 , 'WEB'),(12 , 6 , 'WEB'),(13 , 6 , 'ruby'),(14 , 7 , 'database'),(15 , 8 , 'ruby'),(16 , 8 , 'server';

# 查询既有web标签又有PHP标签的书
select * from tags join tags as t on tags.bookid=t.bookid where tags.content='PHP' and t.content='WEB';

换成key-value存储
set book:bookid:5:title 'PHP 圣经'
set book:bookid:6:title 'ruby实战'
set book:bookid:7:title 'mysql运难'
set book:bookid:8:title 'ruby server'

sadd tag:PHP 5
sadd tag:WEB 5 6
sadd tag:database 7
sadd tag:ruby 6 8
sadd tag:SERVER 8

查:既有PHP又有WEB的书
sinter tag:PHP tag:WEB  # 查集合的交集

查:有PHP或有WEB标签的书
sunin tag:PHP tag:WEB

查:含有ruby不含WEB标签的书
sdiff tag:ruby tag:WEB # 求差集

注意:
在关系型数据中,除主键外,还有可能其他列也步骤查询
如上表中username也是极频繁查询的 ,往往这种列也是加了索引的
转换到k-v数据中,则也要相应的生成一条按照该列为主的key-value
set user:username:lisi:uid 9
我们可以根据username:lisi:uid,查出userid=9
再查user:9:password/email ...


服务端命令
time  返回时间戳+微秒
dbsize 当前数据库未过期key的数量
bgrewriteaof 重写aof
bgsave 后台开启子进程dump数据
save 阻塞进程dump数据
lastsave
slaveof host port 做host port的从服务器(数据清空,复制新主内容)
slaveof no one 变成主服务器(原数据不丢失,一般用于主服失败后)
flushdb  清空当前数据库的所有数据
flushall 清空所有数据库数据
注: 
如果不小心运行了flushall,立即shutdown nosave(看作强制停止服务器的一个ABORT命令),关闭服务器然后手工编辑aof文件,去掉文件中的"flushall"相关行,然后开启服务器,就可以导入回原来数据
如果flushall之后,系统恰好bgrewriteaof了,那么aof就清空了,数据丢失
shutdown [save/nosave] 关闭服务器,保存数据,修改AOF(如果设置)
slowlog get N 获取慢查询日志
127.0.0.1:6379> SLOWLOG GET 1
1) 1) (integer) 26            // slowlog唯一编号id
   2) (integer) 1440057815    // 查询的时间戳
   3) (integer) 47            // 查询耗时(微妙),表示本条命令查询耗时47微秒
   4) 1) "SLOWLOG"            // 查询命令,完整命令为 SLOWLOG GET
      2) "GET"
slowlog len 获取慢查询日志条数
slowlog reset 清空慢查询
info []  可以查看主从,内存/CPU使用,持久化,每个库使用情况/配置文件位置
config get 选项(支持*通配)
config set 选项 值
config rewrite 把值写到配置文件
config restart 更新info命令的信息
debug object key #调试选项,看一个key的情况
debug segfault #模拟段错误,让服务器崩溃

ACL:访问控制列表,可针对任意用户和组进行权限控制
多线程IO模型中的多线程仅用于接受,解析客户端请求,然后将解析出的请求写入到任务队列,对具体任务的处理仍是主线程执行
redis读速度可达11w/s,写速度可达8w/s
https://redis.io/docs/manual/patterns/distributed-locks/
https://redis.io/docs/reference/clients/
https://redis.io/docs/manual/keyspace/
https://blog.getspool.com/2011/11/29/fast-easy-realtime-metrics-using-redis-bitmaps
http://antirez.com/news/75
```




