### 集群相关

```
集群至少需要三个主节点,当主节点A挂掉后其从节点A1会自动升级为主节点,重启A后A会成为A1的从节点
将哈希槽从一个节点移动到另一个节点不需要停止任何操作,因此添加/删除/节点不需要停机
Redis集群中有16384(2的14次方)个哈希槽,每个key都会对应一个编号在0-16383之间的哈希槽,redis会根据节点数量大致均等的将哈希槽映射到不同的节点
当一个key插入时,哈希槽通过CRC16(key) % 16384计算,仅{}中的字符串经过哈希处理,例如this{foo}key和another{foo}key保证位于同一哈希槽中
集群支持多个key操作,只要单个命令执行(或整个事务/Lua脚本执行涉及的所有key都属于同一个哈希槽
集群只支持db0,不支持mget,mset,multi,lua脚本,除非这些key落在同一个哈希槽上,keys *只会返回该节点的数据(主从数据一样)

集群不保证强一致性,在某些情况下可能会丢失写入(网络分区或异步复制),分析如下:
客户端给主节点B发送写请求
主节点B向客户端回复OK
主节点B将写入传播到其副本B1、B2
B在回复客户端前不会等待B1、B2确认,因为会有很大延迟,但在B将写入发送到其副本之前崩溃了,其中一个副本(未接收到写入)会被提升为主副本而永远丢失写入
```

### 哈希槽计算

```python
def crc16(message):
    crc = 0
    for char in message:
        crc ^= char << 8
        for i in range(8):
            if crc & 0x8000:
                crc = (crc << 1 ^ 0x1021) & 0xffff
            else:
                crc <<= 1
    return crc


def hash_slot(key):
    left = key.find('{')  # 首次出现的位置
    if left >= 0:
        right = key.find('}')
        if right - left >= 2:  # 确保{}之间有字符
            key = key[left + 1:right]
    return crc16(key) & 0b11111111111111  # 16383
```

### 创建集群(参考 https://github.com/redis/redis/blob/unstable/utils/create-cluster/create-cluster)

```
1. cd 7000[7001|7002|7003|7004|7005] && redis-server redis_cluster.conf,手动启动每个节点
2. redis-cli --cluster create 127.0.0.1:7000 127.0.0.1:7001 127.0.0.1:7002 127.0.0.1:7003 127.0.0.1:7004 127.0.0.1:7005 --cluster-replicas 1
--cluster-replicas 1意味着每个主节点创建一个副本,不需要在每个节点的配置文件中设置(create a cluster with 3 masters and 3 slaves)
```

### 节点升级

```
升级从节点只需停止该节点并使用更新版本的Redis重新启动
升级主节点使用CLUSTER FAILOVER手动触发主节点故障转移到其中一个从节点,等待主节点变成从节点,最后像升级从节点一样升级节点
如果希望主节点成为刚刚升级的节点,请手动触发新的故障转移,以便将升级后的节点恢复为主节点
CLUSTER FAILOVER必须在要进行故障转移的主服务器的副本之一中执行
```

### reshard(哈希槽从一组节点移动到另一组节点)

```
--cluster-yes指示自动对命令提示回答“是”,从而允许其以非交互模式运行
redis-cli --cluster reshard 127.0.0.1:7002 --cluster-from 9dd8ecfd28eae160d8c19d4184c4777f9bde49e8 --cluster-to cba9eef5cf1b30a7b7dea7f2c8543ba2fe8b5e15 --cluster-slots 10 --cluster-yes
Ready to move 10 slots.
  Source nodes:
    M: 9dd8ecfd28eae160d8c19d4184c4777f9bde49e8 127.0.0.1:7004
       slots:[0-5466],[10923-10926] (5471 slots) master
  Destination node:
    M: cba9eef5cf1b30a7b7dea7f2c8543ba2fe8b5e15 127.0.0.1:7001
       slots:[5467-10922] (5456 slots) master
       1 additional replica(s)
  Resharding plan:
    Moving slot 0 from 9dd8ecfd28eae160d8c19d4184c4777f9bde49e8
    Moving slot 1 from 9dd8ecfd28eae160d8c19d4184c4777f9bde49e8
    Moving slot 2 from 9dd8ecfd28eae160d8c19d4184c4777f9bde49e8
    Moving slot 3 from 9dd8ecfd28eae160d8c19d4184c4777f9bde49e8
    Moving slot 4 from 9dd8ecfd28eae160d8c19d4184c4777f9bde49e8
    Moving slot 5 from 9dd8ecfd28eae160d8c19d4184c4777f9bde49e8
    Moving slot 6 from 9dd8ecfd28eae160d8c19d4184c4777f9bde49e8
    Moving slot 7 from 9dd8ecfd28eae160d8c19d4184c4777f9bde49e8
    Moving slot 8 from 9dd8ecfd28eae160d8c19d4184c4777f9bde49e8
    Moving slot 9 from 9dd8ecfd28eae160d8c19d4184c4777f9bde49e8
Moving slot 0 from 127.0.0.1:7004 to 127.0.0.1:7001: 
Moving slot 1 from 127.0.0.1:7004 to 127.0.0.1:7001: 
Moving slot 2 from 127.0.0.1:7004 to 127.0.0.1:7001: 
Moving slot 3 from 127.0.0.1:7004 to 127.0.0.1:7001: 
Moving slot 4 from 127.0.0.1:7004 to 127.0.0.1:7001: 
Moving slot 5 from 127.0.0.1:7004 to 127.0.0.1:7001: 
Moving slot 6 from 127.0.0.1:7004 to 127.0.0.1:7001: 
Moving slot 7 from 127.0.0.1:7004 to 127.0.0.1:7001: 
Moving slot 8 from 127.0.0.1:7004 to 127.0.0.1:7001: 
Moving slot 9 from 127.0.0.1:7004 to 127.0.0.1:7001: 
```

### rebalance(平衡集群中各个节点的slot数量)

```
redis-cli --cluster rebalance 127.0.0.1:8002
>>> Performing Cluster Check (using node 127.0.0.1:8002)
[OK] All nodes agree about slots configuration.
>>> Check for open slots...
>>> Check slots coverage...
[OK] All 16384 slots covered.
>>> Rebalancing across 3 nodes. Total weight = 3.00
Moving 500 slots from 127.0.0.1:8002 to 127.0.0.1:8005
Moving 5 slots from 127.0.0.1:8002 to 127.0.0.1:8004
```

### 新增节点

```
# 添加一个新节点7006到集群作为主节点,7006相关集群配置必须有且要运行起来,如果有cluster-config-file设置的文件,需要先删除
# 7006不会分配哈希槽,可以使用redis-cli的reshard功能将哈希槽分配给该节点
redis-cli --cluster add-node 127.0.0.1:7006 127.0.0.1:7001 
>>> Adding node 127.0.0.1:7006 to cluster 127.0.0.1:7001
>>> Performing Cluster Check (using node 127.0.0.1:7001)
>>> Check for open slots...
>>> Check slots coverage...
[OK] All 16384 slots covered.
>>> Send CLUSTER MEET to node 127.0.0.1:7006 to make it join the cluster.
[OK] New node added correctly.

# 在主节点1bf1f4e2cefde5099452aec9dbc9386fea369777(7002)上添加一个新的7006从节点(可用来验证cluster-migration-barrier配置)
redis-cli --cluster add-node 127.0.0.1:7006 127.0.0.1:7001 --cluster-slave --cluster-master-id 1bf1f4e2cefde5099452aec9dbc9386fea369777 
>>> Adding node 127.0.0.1:7006 to cluster 127.0.0.1:7001
>>> Performing Cluster Check (using node 127.0.0.1:7001)
>>> Check for open slots...
>>> Check slots coverage...
[OK] All 16384 slots covered.
>>> Send CLUSTER MEET to node 127.0.0.1:7006 to make it join the cluster.
Waiting for the cluster to join
>>> Configure node as replica of 127.0.0.1:7002.
[OK] New node added correctly.
```

### 删除节点

```
# 第一个参数是集群中的随机节点,第二个参数是要删除的节点ID,删除主节点时必须为空,如果非空需要将其数据重新分片到其他主节点
redis-cli --cluster del-node 127.0.0.1:7000 43c59528a792f3758c2df3b2c9fb18f86651904a
>>> Removing node 43c59528a792f3758c2df3b2c9fb18f86651904a from cluster 127.0.0.1:7000
>>> Sending CLUSTER FORGET messages to the cluster...
>>> SHUTDOWN the node.
CLUSTER FORGET <node-id>说明:
从节点表中删除指定ID的节点,60秒内具有相同ID的节点禁止重新添加(因为使用了gossip自动发现节点机制,留足时间从所有节点中删除该节点,防止被重新添加)
```



### tobedone

```
cluster replicate <master-node-id>: 连上从节点,更改其主节点为指定的主节点ID
手动更改从节点不受cluster-migration-barrier配置影响,集群重启时会再次replicas migration

cluster info 
cluster slots  # returns details about which cluster slots map to which Redis instances
cluster nodes  # 返回信息跟cluster slots差不多,一行显示
cluster keyslot key # 计算键key被放置在哪个槽上
cluster countkeysinslot <slot(num)>  # 计算槽上有多少个键值对
cluster getkeysinslot <slot(num)> <count> # 返回count个slot槽中的键

cluster setslot <slot> importing <source-node-id>
将一个槽设置为importing状态,槽下的keys从指定源节点导入目标节点,该命令仅能在目标节点不是指定槽的所有者时生效

cluster setslot <slot> migrating <destination-node-id>
将一个槽设置为migrating状态,该命令的节点必须是该哈希槽的所有者,节点将会有如下操作: 
1. 如果处理的是存在的key,命令正常执行
2. 如果要处理的key不存在,接收命令的节点将发出一个重定向ASK,让客户端在destination-node重试该查询.在这种情况下客户端不应该将该哈希槽更新为节点映射.
3. 如果命令包含多个keys,如果都不存在处理方式同2;如果都存在,处理方式同1;
   如果只是部分存在,针对即将完成迁移至目标节点的keys按序返回TRYAGAIN错误,以便批量keys命令可以执行,The client can try the operation after some time, or report back the error.

cluster forget node-id
The command is used in order to remove a node, specified via its node ID, In other words the specified node is removed from the nodes table of the node receiving the command.
we'll show why the command must not just remove a given node from the nodes table, but also prevent it for being re-inserted again for some time.
Let's assume we have four nodes, A, B, C and D. In order to end with just a three nodes cluster A, B, C we may follow these steps:
Reshard all the hash slots from D to nodes A, B, C.
D is now empty, but still listed in the nodes table of A, B and C.
We contact A, and send CLUSTER FORGET D.
B sends node A a heartbeat packet, where node D is listed.
A does no longer known node D (see step 3), so it starts an handshake with D.
D ends re-added in the nodes table of A.
As you can see in this way removing a node is fragile, we need to send CLUSTER FORGET commands to all the nodes ASAP hoping there are no gossip sections processing in the meantime.
Because of this problem the command implements a ban-list with an expire time for each entry.

----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# 从节点不分配槽位
redis-cli --cluster check 127.0.0.1:8005
127.0.0.1:8005 (9dd8ecfd...) -> 13 keys | 5461 slots | 0 slaves.
127.0.0.1:8003 (1bf1f4e2...) -> 9 keys | 5461 slots | 1 slaves.
127.0.0.1:8002 (cba9eef5...) -> 21 keys | 5462 slots | 0 slaves.
[OK] 43 keys in 3 masters.
0.00 keys per slot on average.
>>> Performing Cluster Check (using node 127.0.0.1:8005)
M: 9dd8ecfd28eae160d8c19d4184c4777f9bde49e8 127.0.0.1:8005
   slots:[0-5460] (5461 slots) master
S: f72e454d7a592aef786ce318c4b73de6a0385a9d 127.0.0.1:8004
   slots: (0 slots) slave
   replicates 1bf1f4e2cefde5099452aec9dbc9386fea369777
M: 1bf1f4e2cefde5099452aec9dbc9386fea369777 127.0.0.1:8003
   slots:[10923-16383] (5461 slots) master
   1 additional replica(s)
M: cba9eef5cf1b30a7b7dea7f2c8543ba2fe8b5e15 127.0.0.1:8002
   slots:[5461-10922] (5462 slots) master
[OK] All nodes agree about slots configuration.
>>> Check for open slots...
>>> Check slots coverage...
[OK] All 16384 slots covered.

----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

epoch(epoch is used in order to give incremental versioning to events)

The currentEpoch is a 64 bit unsigned number.At node creation every Redis Cluster node, both slaves and master nodes, set the currentEpoch to 0.
Every time a packet is received from another node, if the epoch of the sender (part of the cluster bus messages header) is greater than the local node epoch, the currentEpoch is updated to the sender epoch.
Because of these semantics, eventually all the nodes will agree to the greatest configEpoch in the cluster.
This information is used when the state of the cluster is changed and a node seeks agreement in order to perform some action.
Currently this happens only during slave promotion
In order to be elected, the first step for a slave is to increment its currentEpoch counter, and request votes from master instances.
Votes are requested by the slave by broadcasting a FAILOVER_AUTH_REQUEST packet to every master node of the cluster. 
Then it waits for a maximum time of two times the NODE_TIMEOUT for replies to arrive (but always for at least 2 seconds).
Once the slave receives ACKs from the majority of masters, it wins the election. Otherwise if the majority is not reached within the period of two times NODE_TIMEOUT (but always at least 2 seconds), 
the election is aborted and a new one will be tried again after NODE_TIMEOUT * 4 (and always at least 4 seconds).

The configEpoch is set to zero in masters when a new node is created.
the configEpoch helps to resolve conflicts when different nodes claim divergent configurations (a condition that may happen because of network partitions and node failures).
Slave nodes also advertise the configEpoch field in ping and pong packets, but in the case of slaves the field represents the configEpoch of its master as of the last time they exchanged packets. 
This allows other instances to detect when a slave has an old configuration that needs to be updated (master nodes will not grant votes to slaves with an old configuration).
Every time the configEpoch changes for some known node, it is permanently stored in the nodes.conf file by all the nodes that receive this information. The same also happens for the currentEpoch value. 
These two variables are guaranteed to be saved and fsync-ed to disk when updated before a node continues its operations.

----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

reshard原理
对目标节点发送 cluster setslot <slot> importing <sourceNodeId> 命令,让目标节点准备导入槽的数据
对源节点发送 cluster setslot <slot> migrating <targetNodeId> 命令,让源节点准备迁出槽的数据
源节点循环执行 cluster getkeysinslot <slot> <count> 命令,获取count个属于槽slot的键
在源节点上执行 migrate target_host target_port key target_database id timeout 命令,把获取的键批量迁移到目标节点
重复执行步骤3和步骤4直到槽下所有的键值数据迁移到目标节点
Use cluster setslot <slot> node <destination-node-id>.为了保证槽节点映射变更及时传播,需要遍历发送给所有节点更新被迁移的槽指向新节点
步骤1和步骤2的顺序很重要,我们希望在源节点配置了重定向之后目的节点已经可以接受ASK重定向

MIGRATE will send a serialized version of the key, and once an OK code is received, the old key from its own dataset will be deleted. 
From the point of view of an external client a key exists either in A or B at any given time.
In Redis Cluster there is no need to specify a database other than 0, but MIGRATE is a general command that can be used for other tasks not involving Redis Cluster. 

in order to migrate a hash slot from one node to another.
When a slot is set as MIGRATING, the node will accept all queries that are about this hash slot, but only if the key in question exists, 
otherwise the query is forwarded using a -ASK redirection to the node that is target of the migration.
When a slot is set as IMPORTING, the node will accept all queries that are about this hash slot, but only if the request is preceded by an ASKING command. 
If the ASKING command was not given by the client, the query is redirected to the real hash slot owner via a -MOVED redirection error, as would happen normally.
Let's make this clearer with an example of hash slot migration. Assume that we have two Redis master nodes A and B. We want to move hash slot 8 from A to B:
We send B: CLUSTER SETSLOT 8 IMPORTING A
We send A: CLUSTER SETSLOT 8 MIGRATING B
All the other nodes will continue to point clients to node "A" every time they are queried with a key that belongs to hash slot 8, so what happens is that:
All queries about existing keys are processed by "A".
All queries about non-existing keys in A are processed by "B", because "A" will redirect clients to "B".

ASK redirection
In the previous section we briefly talked about ASK redirection.Why can't we simply use MOVED redirection? 
Because while MOVED means that we think the hash slot is permanently served by a different node and the next queries should be tried against the specified node, 
ASK means to send only the next query to the specified node.
This is needed because the next query about hash slot 8 can be about a key that is still in A, so we always want the client to try A and then B if needed. 
Since this happens only for one hash slot out of 16384 available, the performance hit on the cluster is acceptable.
We need to force that client behavior, so to make sure that clients will only try node B after A was tried, 
node B will only accept queries of a slot that is set as IMPORTING if the client sends the ASKING command before sending the query.
Basically the ASKING command sets a one-time flag on the client that forces a node to serve a query about an IMPORTING slot.
The full semantics of ASK redirection from the point of view of the client is as follows:
If ASK redirection is received, send only the query that was redirected to the specified node but continue sending subsequent queries to the old node.
Start the redirected query with the ASKING command.Don't yet update local client tables to map hash slot 8 to B.
Once hash slot 8 migration is completed, A will send a MOVED message and the client may permanently map hash slot 8 to the new IP and port pair. 
Note that if a buggy client performs the map earlier this is not a problem since it will not send the ASKING command before issuing the query, so B will redirect the client to A using a MOVED redirection error.

8005
cluster setslot 1742 importing cba9eef5cf1b30a7b7dea7f2c8543ba2fe8b5e15
127.0.0.1:8005> asking
OK
127.0.0.1:8005> get {user_info}:avatar
"guess"
127.0.0.1:8005> get {user_info}:avatar
-> Redirected to slot [1742] located at 127.0.0.1:8002
(error) ASK 1742 127.0.0.1:8005
cluster setslot 1742 node 9dd8ecfd28eae160d8c19d4184c4777f9bde49e8

8002
cluster setslot 1742 migrating 9dd8ecfd28eae160d8c19d4184c4777f9bde49e8
127.0.0.1:8002> get {user_info}:avatar
(error) ASK 1742 127.0.0.1:8005
cluster setslot 1742 node cba9eef5cf1b30a7b7dea7f2c8543ba2fe8b5e15

什么时候整个集群不可用(cluster_state:fail)?
如果集群任意master挂掉,且当前master没有slave.集群进入fail状态,也可以理解成集群的slot映射[0-16383]不完整时进入fail状态
如果集群超过半数以上master挂掉,无论是否有slave,集群进入fail状态

RedisCluster对keys,mget,mset,pipeline做了处理,使用时不需要再考虑key落在不同slot问题,但对于lua脚本则必须落在同一个slot上
其中pipeline原理是先根据for key in keys:crc16(key)%16384给keys分组,再批量执行,效率仍然比单条命令依次执行要高
参考:https://github.com/Grokzen/redis-py-cluster/blob/unstable/rediscluster/pipeline.py#L139 , send_cluster_commands
redis集群不支持事物,In redis-py, pipelining is all about trying to achieve greater network efficiency. 
Transaction support is disabled in redis-py-cluster. Use pipelines to avoid extra network round-trips, not to ensure atomicity.
```
