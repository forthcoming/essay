### keys 
```
keys pattern:查找所有符合给定模式pattern的key
有3个通配符 *, ? ,[]
*:通配任意多个字符
?:通配单个字符
[]:通配括号内的某1个字符
127.0.0.1:6379> keys *
(empty list or set)
127.0.0.1:6379> mset one 1 two 2 three 3 four 4
OK
127.0.0.1:6379> keys o*
1) "one"
127.0.0.1:6379> keys *o
1) "two"
127.0.0.1:6379> keys ???
1) "one"
2) "two"
127.0.0.1:6379> keys on[dce]
1) "one"
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

### hash(字典)
```
hset key field value : 把key中filed域的值设为value,如果有field,则覆盖原field域的值
hmset key field1 value1 [field2 value2 field3 value3 ......fieldn valuen]
hdel key field : 删除key中field域
hlen key : 返回key中元素的数量
hexists key field : 判断key中有没有field域,时间复杂度O(1)
hinrby float key field value : 把key中的field域的值增长浮点值value
hkeys key : 返回key中所有的field,时间复杂度O(N)
hvals key : 返回key中所有的value
hgetall key : 返回key中所有得field-value
```

### hyperloglog
```
127.0.0.1:6379> pfadd hll a b c d a      
(integer) 1       # 1 if at least 1 HyperLogLog internal register was altered. 0 otherwise.
127.0.0.1:6379> pfcount hll
(integer) 4
```