```
Redis集群中内置了16384(2的14次方)个哈希槽,当需要在Redis集群中放置一个key-value时,先对key使用crc16算法算出一个结果,然后把结果对16384求余数
这样每个key都会对应一个编号在0-16383之间的哈希槽,redis会根据节点数量大致均等的将哈希槽映射到不同的节点(没使用一致性哈希)
当主节点A挂掉后其从节点B会自动升级为主节点,重启A后A会成为B的从节点
the minimal cluster that works as expected requires to contain at least three master nodes.

Redis Cluster supports multiple key operations as long as all the keys involved into a single command execution (or whole transaction, or Lua script execution) all belong to the same hash slot. 
The user can force multiple keys to be part of the same hash slot by using a concept called hash tags.
only string in {} is hashed, so for example this{foo}key and another{foo}key are guaranteed to be in the same hash slot, and can be used together in a command with multiple keys as arguments.
redis集群只支持db0,不支持mget,mset,multi,lua脚本,除非这些key落在同一个slot上,keys *只会返回该节点的数据(主从数据一样)
redis-py-cluster的StrictRedisCluster对keys,mget,mset,pipeline做了处理,使用时不需要再考虑key落在不同slot问题,但对于lua脚本则必须落在同一个slot上
其中pipeline原理是先根据for key in keys:crc16(key)%16384给keys分组,再批量执行,效率仍然比单条命令依次执行要高
参考:https://github.com/Grokzen/redis-py-cluster/blob/unstable/rediscluster/pipeline.py#L139 , send_cluster_commands

redis集群不支持事物,In redis-py-cluster, pipelining is all about trying to achieve greater network efficiency. 
Transaction support is disabled in redis-py-cluster. Use pipelines to avoid extra network round-trips, not to ensure atomicity.

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
    left = key.find('{')   # 首次出现的位置
    if left>=0:
        right = key.find('}')
        if right-left>=2:  # 确保{}之间有字符
            return crc16(key[left+1:right]) & 0b11111111111111  # 16383
    return crc16(key) & 0b11111111111111  # 16383
    
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

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

cluster replicate <master-node-id>
In Redis Cluster it is possible to reconfigure a slave to replicate with a different master
手动更改从节点不受cluster-migration-barrier配置影响,集群重启时会再次replicas migration

----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Redis Cluster supports the ability to add and remove nodes while the cluster is running.
Adding or removing a node is abstracted into the same operation: moving a hash slot from one node to another. 
To add a new node to the cluster an empty node is added to the cluster and some set of hash slots are moved from existing nodes to the new node.
To remove a node from the cluster the hash slots assigned to that node are moved to other existing nodes.
Moving a hash slot means moving all the keys that happen to hash into this hash slot.

----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Removing nodes from a cluster(slave节点可以直接删除)
# The first argument is just a random node in the cluster, the second argument is the ID of the node you want to remove.
# You can remove a master node in the same way as well, however in order to remove a master node it must be empty. 
# If the master is not empty you need to reshard data away from it to all the other master nodes before.
# An alternative to remove a master node is to perform a manual failover of it over one of its slaves and remove the node after it turned into a slave of the new master.
# Obviously this does not help when you want to reduce the actual number of masters in your cluster, in that case, a resharding is needed.
# u can remove a node from a cluster,However, the other nodes will still remember its node ID and address, and will attempt to connect with it.
# For this reason, when a node is removed we want to also remove its entry from all the other nodes tables. This is accomplished by using the CLUSTER FORGET <node-id> command.
# The command does two things:
# It removes the node with the specified node ID from the nodes table.
# It sets a 60 second ban which prevents a node with the same node ID from being re-added.
# The second operation is needed because Redis Cluster uses gossip in order to auto-discover nodes, so removing the node X from node A, could result in node B gossiping about node X to A again. 
# Because of the 60 second ban, the Redis Cluster administration tools have 60 seconds in order to remove the node from all the nodes, preventing the re-addition of the node due to auto discovery.
redis-cli --cluster del-node 127.0.0.1:8001 43c59528a792f3758c2df3b2c9fb18f86651904a
>>> Removing node 43c59528a792f3758c2df3b2c9fb18f86651904a from cluster 127.0.0.1:8001
>>> Sending CLUSTER FORGET messages to the cluster...
>>> SHUTDOWN the node.

redis-cli --cluster del-node 127.0.0.1:8006 9dd8ecfd28eae160d8c19d4184c4777f9bde49e8
>>> Removing node 9dd8ecfd28eae160d8c19d4184c4777f9bde49e8 from cluster 127.0.0.1:8006
[ERR] Node 127.0.0.1:8005 is not empty! Reshard data away and try again.

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

# 添加一个新节点8006到集群作为主节点,8006相关集群配置必须有且要运行起来,如果有cluster-config-file设置的文件,需要先删除
redis-cli --cluster add-node 127.0.0.1:8006 127.0.0.1:8002 
>>> Adding node 127.0.0.1:8006 to cluster 127.0.0.1:8002
>>> Performing Cluster Check (using node 127.0.0.1:8002)
>>> Check for open slots...
>>> Check slots coverage...
[OK] All 16384 slots covered.
>>> Send CLUSTER MEET to node 127.0.0.1:8006 to make it join the cluster.
[OK] New node added correctly.

# 在主节点1bf1f4e2cefde5099452aec9dbc9386fea369777(8003)上添加一个新的8006从节点(可用来验证cluster-migration-barrier配置)
redis-cli --cluster add-node 127.0.0.1:8006 127.0.0.1:8002 --cluster-slave --cluster-master-id 1bf1f4e2cefde5099452aec9dbc9386fea369777 
>>> Adding node 127.0.0.1:8006 to cluster 127.0.0.1:8002
>>> Performing Cluster Check (using node 127.0.0.1:8002)
>>> Check for open slots...
>>> Check slots coverage...
[OK] All 16384 slots covered.
>>> Send CLUSTER MEET to node 127.0.0.1:8006 to make it join the cluster.
Waiting for the cluster to join
>>> Configure node as replica of 127.0.0.1:8003.
[OK] New node added correctly.

----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# 槽迁移只能在主节点进行,应为从节点未分配哈希槽
redis-cli --cluster reshard 127.0.0.1:8002
How many slots do you want to move (from 1 to 16384)? 10
What is the receiving node ID? 9dd8ecfd28eae160d8c19d4184c4777f9bde49e8
Please enter all the source node IDs.
  Type 'all' to use all the nodes as source nodes for the hash slots.
  Type 'done' once you entered all the source nodes IDs.
Source node #1: all

Ready to move 10 slots.
  Source nodes:
    M: cba9eef5cf1b30a7b7dea7f2c8543ba2fe8b5e15 127.0.0.1:8002
       slots:[5461-10922] (5462 slots) master
       1 additional replica(s)
    M: f72e454d7a592aef786ce318c4b73de6a0385a9d 127.0.0.1:8004
       slots:[10923-16383] (5461 slots) master
       1 additional replica(s)
  Destination node:
    M: 9dd8ecfd28eae160d8c19d4184c4777f9bde49e8 127.0.0.1:8005
       slots:[0-5460] (5461 slots) master
  Resharding plan:
    Moving slot 5461 from cba9eef5cf1b30a7b7dea7f2c8543ba2fe8b5e15
    Moving slot 5462 from cba9eef5cf1b30a7b7dea7f2c8543ba2fe8b5e15
    Moving slot 5463 from cba9eef5cf1b30a7b7dea7f2c8543ba2fe8b5e15
    Moving slot 5464 from cba9eef5cf1b30a7b7dea7f2c8543ba2fe8b5e15
    Moving slot 5465 from cba9eef5cf1b30a7b7dea7f2c8543ba2fe8b5e15
    Moving slot 5466 from cba9eef5cf1b30a7b7dea7f2c8543ba2fe8b5e15
    Moving slot 10923 from f72e454d7a592aef786ce318c4b73de6a0385a9d
    Moving slot 10924 from f72e454d7a592aef786ce318c4b73de6a0385a9d
    Moving slot 10925 from f72e454d7a592aef786ce318c4b73de6a0385a9d
    Moving slot 10926 from f72e454d7a592aef786ce318c4b73de6a0385a9d
Do you want to proceed with the proposed reshard plan (yes/no)? yes
Moving slot 5461 from 127.0.0.1:8002 to 127.0.0.1:8005: 
Moving slot 5462 from 127.0.0.1:8002 to 127.0.0.1:8005: 
Moving slot 5463 from 127.0.0.1:8002 to 127.0.0.1:8005: 
Moving slot 5464 from 127.0.0.1:8002 to 127.0.0.1:8005: 
Moving slot 5465 from 127.0.0.1:8002 to 127.0.0.1:8005: 
Moving slot 5466 from 127.0.0.1:8002 to 127.0.0.1:8005: 
Moving slot 10923 from 127.0.0.1:8004 to 127.0.0.1:8005: 
Moving slot 10924 from 127.0.0.1:8004 to 127.0.0.1:8005: 
Moving slot 10925 from 127.0.0.1:8004 to 127.0.0.1:8005: 
Moving slot 10926 from 127.0.0.1:8004 to 127.0.0.1:8005: 

redis-cli --cluster reshard 127.0.0.1:8003 --cluster-from 9dd8ecfd28eae160d8c19d4184c4777f9bde49e8 --cluster-to cba9eef5cf1b30a7b7dea7f2c8543ba2fe8b5e15 --cluster-slots 10 --cluster-yes
Ready to move 10 slots.
  Source nodes:
    M: 9dd8ecfd28eae160d8c19d4184c4777f9bde49e8 127.0.0.1:8005
       slots:[0-5466],[10923-10926] (5471 slots) master
  Destination node:
    M: cba9eef5cf1b30a7b7dea7f2c8543ba2fe8b5e15 127.0.0.1:8002
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
Moving slot 0 from 127.0.0.1:8005 to 127.0.0.1:8002: 
Moving slot 1 from 127.0.0.1:8005 to 127.0.0.1:8002: 
Moving slot 2 from 127.0.0.1:8005 to 127.0.0.1:8002: 
Moving slot 3 from 127.0.0.1:8005 to 127.0.0.1:8002: 
Moving slot 4 from 127.0.0.1:8005 to 127.0.0.1:8002: 
Moving slot 5 from 127.0.0.1:8005 to 127.0.0.1:8002: 
Moving slot 6 from 127.0.0.1:8005 to 127.0.0.1:8002: 
Moving slot 7 from 127.0.0.1:8005 to 127.0.0.1:8002: 
Moving slot 8 from 127.0.0.1:8005 to 127.0.0.1:8002: 
Moving slot 9 from 127.0.0.1:8005 to 127.0.0.1:8002: 

----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# 平衡集群中各个节点的slot数量
redis-cli --cluster rebalance 127.0.0.1:8002
>>> Performing Cluster Check (using node 127.0.0.1:8002)
[OK] All nodes agree about slots configuration.
>>> Check for open slots...
>>> Check slots coverage...
[OK] All 16384 slots covered.
>>> Rebalancing across 3 nodes. Total weight = 3.00
Moving 500 slots from 127.0.0.1:8002 to 127.0.0.1:8005
Moving 5 slots from 127.0.0.1:8002 to 127.0.0.1:8004

----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

创建集群(客户端连接集群redis-cli需要带上-c,redis-cli -c -p port): 
1. redis-server 8001[8002|8003|8004|8005|8006|].conf,手动开启每个节点
2. redis-cli --cluster create 127.0.0.1:8001 127.0.0.1:8002 127.0.0.1:8003 127.0.0.1:8004 127.0.0.1:8005 127.0.0.1:8006 --cluster-replicas 1
The option --cluster-replicas 1 means that we want a slave for every master created.(create a cluster with 3 masters and 3 slaves)
The other arguments are the list of addresses of the instances I want to use to create the new cluster.
集群中的主从是在创建集时分配,并不需要在每个节点的配置文件中设置

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

Redis Cluster is not able to guarantee strong consistency. 
In practical terms this means that under certain conditions it is possible that Redis Cluster will lose writes that were acknowledged by the system to the client.
The first reason why Redis Cluster can lose writes is because it uses asynchronous replication. This means that during writes the following happens:
Your client writes to the master B.
The master B replies OK to your client.
The master B propagates the write to its slaves B1, B2 and B3.
As you can see, B does not wait for an acknowledgement from B1, B2, B3 before replying to the client, since this would be a prohibitive latency penalty for Redis, 
so if your client writes something, B acknowledges the write, but crashes before being able to send the write to its slaves, one of the slaves (that did not receive the write) can be promoted to master, losing the write forever.

----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Upgrading slave nodes is easy since you just need to stop the node and restart it with an updated version of Redis. 
Upgrading masters is a bit more complex, and the suggested procedure is:
Use CLUSTER FAILOVER to trigger a manual failover of the master to one of its slaves.Wait for the master to turn into a slave.Finally upgrade the node as you do for slaves.
If you want the master to be the node you just upgraded, trigger a new manual failover in order to turn back the upgraded node into a master.
Following this procedure you should upgrade one node after the other until all the nodes are upgraded.

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

----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

in practical terms, what do you get with Redis Cluster?
The ability to automatically split your dataset among multiple nodes.
The ability to continue operations when a subset of the nodes are experiencing failures or are unable to communicate with the rest of the cluster.

什么时候整个集群不可用(cluster_state:fail)?
如果集群任意master挂掉,且当前master没有slave.集群进入fail状态,也可以理解成集群的slot映射[0-16383]不完整时进入fail状态
如果集群超过半数以上master挂掉,无论是否有slave,集群进入fail状态

The redis-cli cluster support is very basic so it always uses the fact that Redis Cluster nodes are able to redirect a client to the right node.
A serious client is able to do better than that, and cache the map between hash slots and nodes addresses, to directly use the right connection to the right node.
The map is refreshed only when something changed in the cluster configuration, for example after a failover or after the system administrator changed the cluster layout by adding or removing nodes.
Clients usually need to fetch a complete list of slots and mapped node addresses in two different situations:
At startup in order to populate the initial slots configuration.
When a MOVED redirection is received.

数据预热: 预先访问接口或者程序,填充缓存,防止单位时间内大量请求访问数据库
```