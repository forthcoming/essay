环境
mongod --dbpath E:/MongoDB/01 --replSet amazon --port 27001
mongod --dbpath E:/MongoDB/02 --replSet amazon --port 27002
mongod --dbpath E:/MongoDB/03 --replSet amazon --port 27003


C:\Users\Administrator>mongo --port 27001
config = {
  _id:"amazon",
  members:[
    {_id:0,host:"127.0.0.1:27001"},
    {_id:1,host:"127.0.0.1:27002"},
    {_id:2,host:"127.0.0.1:27003"}
  ]
}
amazon:PRIMARY> rs.initiate(config);
amazon:PRIMARY> rs.conf();
{
  "_id" : "amazon",    # 副本集名称,必须与replSet名称一致
  "version" : 1,       # 每改变一次集群的配置,副本集的version都会加1
  "protocolVersion" : NumberLong(1),
  "members" : [
  {
  "_id" : 0,
  "host" : "127.0.0.1:27001",
  "arbiterOnly" : false,       # 是否为仲裁节点,仲裁节点只参与投票,不接收数据,也不能成为活跃节点
  "buildIndexes" : true,
  "hidden" : false,
  "priority" : 1,     # 默认为1,优先级0为被动节点,不能成为活跃节点.优先级不是0则按照大到小选出活跃节点作为PRIMARY
  "slaveDelay" : NumberLong(0),
  "votes" : 1
  },
  {
  "_id" : 1,
  "host" : "127.0.0.1:27002",
  "arbiterOnly" : false,
  "buildIndexes" : true,
  "hidden" : false,
  "priority" : 1,
  "slaveDelay" : NumberLong(0),
  "votes" : 1
  },
  {
  "_id" : 2,
  "host" : "127.0.0.1:27003",
  "arbiterOnly" : false,
  "buildIndexes" : true,
  "hidden" : false,
  "priority" : 1,
  "slaveDelay" : NumberLong(0),
  "votes" : 1
  }
  ],
  "settings" : {
  "chainingAllowed" : true,
  "heartbeatIntervalMillis" : 2000,
  "heartbeatTimeoutSecs" : 10,
  "electionTimeoutMillis" : 10000,
  "catchUpTimeoutMillis" : 2000,
  "getLastErrorDefaults" : {
  "w" : 1,
  "wtimeout" : 0
  },
  "replicaSetId" : ObjectId("5948af870505bcf5453e9717")
  }
}
amazon:OTHER> rs.status()
{
  "set" : "amazon",
  "date" : ISODate("2017-06-20T05:18:12.339Z"),
  "myState" : 1,
  "term" : NumberLong(1),
  "heartbeatIntervalMillis" : NumberLong(2000),
  "optimes" : {
  "lastCommittedOpTime" : {
  "ts" : Timestamp(1497935885, 1),
  "t" : NumberLong(1)
  },
  "appliedOpTime" : {
  "ts" : Timestamp(1497935885, 1),
  "t" : NumberLong(1)
  },
  "durableOpTime" : {
  "ts" : Timestamp(1497935885, 1),
  "t" : NumberLong(1)
  }
  },
  "members" : [
  {
  "_id" : 0,
  "name" : "127.0.0.1:27001",
  "health" : 1,
  "state" : 1,
  "stateStr" : "PRIMARY",
  "uptime" : 703,
  "optime" : {
  "ts" : Timestamp(1497935885, 1),
  "t" : NumberLong(1)
  },
  "optimeDate" : ISODate("2017-06-20T05:18:05Z"),
  "electionTime" : Timestamp(1497935763, 1),
  "electionDate" : ISODate("2017-06-20T05:16:03Z"),
  "configVersion" : 1,
  "self" : true
  },
  {
  "_id" : 1,
  "name" : "127.0.0.1:27002",
  "health" : 1,
  "state" : 2,
  "stateStr" : "SECONDARY",
  "uptime" : 139,
  "optime" : {
  "ts" : Timestamp(1497935885, 1),
  "t" : NumberLong(1)
  },
  "optimeDurable" : {
  "ts" : Timestamp(1497935885, 1),
  "t" : NumberLong(1)
  },
  "optimeDate" : ISODate("2017-06-20T05:18:05Z"),
  "optimeDurableDate" : ISODate("2017-06-20T05:18:05Z"),
  "lastHeartbeat" : ISODate("2017-06-20T05:18:12.006Z"),
  "lastHeartbeatRecv" : ISODate("2017-06-20T05:18:11.192Z"
),
  "pingMs" : NumberLong(0),
  "syncingTo" : "127.0.0.1:27001",
  "configVersion" : 1
  },
  {
  "_id" : 2,
  "name" : "127.0.0.1:27003",
  "health" : 1,
  "state" : 2,
  "stateStr" : "SECONDARY",
  "uptime" : 139,
  "optime" : {
  "ts" : Timestamp(1497935885, 1),
  "t" : NumberLong(1)
  },
  "optimeDurable" : {
  "ts" : Timestamp(1497935885, 1),
  "t" : NumberLong(1)
  },
  "optimeDate" : ISODate("2017-06-20T05:18:05Z"),
  "optimeDurableDate" : ISODate("2017-06-20T05:18:05Z"),
  "lastHeartbeat" : ISODate("2017-06-20T05:18:12.017Z"),
  "lastHeartbeatRecv" : ISODate("2017-06-20T05:18:11.168Z"
),
  "pingMs" : NumberLong(0),
  "syncingTo" : "127.0.0.1:27001",
  "configVersion" : 1
  }
  ],
  "ok" : 1
}


mongodb默认从主节点读写数据,副本节点上不允许读,需要设置副本节点可以读
"errmsg" : "not master and slaveOk=false"
amazon:PRIMARY> db.getMongo().setSlaveOk(); //但仍然不可以写


故障转移测试: 将主节点27001停掉模仿服务器故障,在27002上执行rs.status()
amazon:SECONDARY> rs.status()
{
  "set" : "amazon",
  "date" : ISODate("2017-06-20T05:34:30.635Z"),
  "myState" : 1,
  "term" : NumberLong(2),
  "heartbeatIntervalMillis" : NumberLong(2000),
  "optimes" : {
  "lastCommittedOpTime" : {
  "ts" : Timestamp(1497936861, 1),
  "t" : NumberLong(2)
  },
  "appliedOpTime" : {
  "ts" : Timestamp(1497936861, 1),
  "t" : NumberLong(2)
  },
  "durableOpTime" : {
  "ts" : Timestamp(1497936861, 1),
  "t" : NumberLong(2)
  }
  },
  "members" : [
  {
  "_id" : 0,
  "name" : "127.0.0.1:27001",
  "health" : 0,
  "state" : 8,
  "stateStr" : "(not reachable/healthy)",
  "uptime" : 0,
  "optime" : {
  "ts" : Timestamp(0, 0),
  "t" : NumberLong(-1)
  },
  "optimeDurable" : {
  "ts" : Timestamp(0, 0),
  "t" : NumberLong(-1)
  },
  "optimeDate" : ISODate("1970-01-01T00:00:00Z"),
  "optimeDurableDate" : ISODate("1970-01-01T00:00:00Z"),
  "lastHeartbeat" : ISODate("2017-06-20T05:34:27.377Z"),
  "lastHeartbeatRecv" : ISODate("2017-06-20T05:33:10.066Z"),
  "pingMs" : NumberLong(0),
  "lastHeartbeatMessage" : "",
  "configVersion" : -1
  },
  {
  "_id" : 1,
  "name" : "127.0.0.1:27002",
  "health" : 1,
  "state" : 1,
  "stateStr" : "PRIMARY",
  "uptime" : 1571,
  "optime" : {
  "ts" : Timestamp(1497936861, 1),
  "t" : NumberLong(2)
  },
  "optimeDate" : ISODate("2017-06-20T05:34:21Z"),
  "infoMessage" : "could not find member to sync from",
  "electionTime" : Timestamp(1497936799, 1),
  "electionDate" : ISODate("2017-06-20T05:33:19Z"),
  "configVersion" : 1,
  "self" : true
  },
  {
  "_id" : 2,
  "name" : "127.0.0.1:27003",
  "health" : 1,
  "state" : 2,
  "stateStr" : "SECONDARY",
  "uptime" : 1116,
  "optime" : {
  "ts" : Timestamp(1497936861, 1),
  "t" : NumberLong(2)
  },
  "optimeDurable" : {
  "ts" : Timestamp(1497936861, 1),
  "t" : NumberLong(2)
  },
  "optimeDate" : ISODate("2017-06-20T05:34:21Z"),
  "optimeDurableDate" : ISODate("2017-06-20T05:34:21Z"),
  "lastHeartbeat" : ISODate("2017-06-20T05:34:29.957Z"),
  "lastHeartbeatRecv" : ISODate("2017-06-20T05:34:28.795Z"
),
  "pingMs" : NumberLong(0),
  "syncingTo" : "127.0.0.1:27002",
  "configVersion" : 1
  }
  ],
  "ok" : 1
}


当副本集中只剩一台机器时,stateStr只能是SECONDARY,即此时只能进行查操作,直至大于2台主机为止
如果是手动移除,则最后一个是主节点,仍然可以进行读写操作
amazon:PRIMARY> rs.remove('127.0.0.1:27002') #该操作只能在PRIMARY库下进行
amazon:PRIMARY> rs.remove('127.0.0.1:27001') #该操作只能在PRIMARY库下进行
amazon:PRIMARY> rs.status()
{
  "set" : "amazon",
  "date" : ISODate("2017-06-20T06:19:43.643Z"),
  "myState" : 1,
  "term" : NumberLong(5),
  "heartbeatIntervalMillis" : NumberLong(2000),
  "optimes" : {
  "lastCommittedOpTime" : {
  "ts" : Timestamp(1497939576, 1),
  "t" : NumberLong(5)
  },
  "appliedOpTime" : {
  "ts" : Timestamp(1497939576, 1),
  "t" : NumberLong(5)
  },
  "durableOpTime" : {
  "ts" : Timestamp(1497939576, 1),
  "t" : NumberLong(5)
  }
  },
  "members" : [
  {
  "_id" : 2,
  "name" : "127.0.0.1:27003",
  "health" : 1,
  "state" : 1,
  "stateStr" : "PRIMARY",
  "uptime" : 736,
  "optime" : {
  "ts" : Timestamp(1497939576, 1),
  "t" : NumberLong(5)
  },
  "optimeDate" : ISODate("2017-06-20T06:19:36Z"),
  "electionTime" : Timestamp(1497938865, 1),
  "electionDate" : ISODate("2017-06-20T06:07:45Z"),
  "configVersion" : 3,
  "self" : true
  }
  ],
  "ok" : 1
}


amazon:PRIMARY> rs.add({host: "127.0.0.1:27001", priority: 3}) #执行完,27001立马变成PRIMARY,此时的27003变成SECONDARY,切换到27001继续执行
amazon:PRIMARY> rs.add({host: "127.0.0.1:27002", priority: 0})
amazon:PRIMARY> rs.conf()
{
  "_id" : "amazon",
  "version" : 5,
  "protocolVersion" : NumberLong(1),
  "members" : [
  {
  "_id" : 2,
  "host" : "127.0.0.1:27003",
  "arbiterOnly" : false,
  "buildIndexes" : true,
  "hidden" : false,
  "priority" : 1,
  "slaveDelay" : NumberLong(0),
  "votes" : 1
  },
  {
  "_id" : 3,
  "host" : "127.0.0.1:27001",
  "arbiterOnly" : false,
  "buildIndexes" : true,
  "hidden" : false,
  "priority" : 3,
  "slaveDelay" : NumberLong(0),
  "votes" : 1
  },
  {
  "_id" : 4,
  "host" : "127.0.0.1:27002",
  "arbiterOnly" : false,
  "buildIndexes" : true,
  "hidden" : false,
  "priority" : 0,
  "slaveDelay" : NumberLong(0),
  "votes" : 1
  }
  ],
  "settings" : {
  "chainingAllowed" : true,
  "heartbeatIntervalMillis" : 2000,
  "heartbeatTimeoutSecs" : 10,
  "electionTimeoutMillis" : 10000,
  "catchUpTimeoutMillis" : 2000,
  "getLastErrorModes" : {

  },
  "getLastErrorDefaults" : {
  "w" : 1,
  "wtimeout" : 0
  },
  "replicaSetId" : ObjectId("5948af870505bcf5453e9717")
  }
}
amazon:PRIMARY> rs.status()
{
  "set" : "amazon",
  "date" : ISODate("2017-06-20T06:24:32.300Z"),
  "myState" : 1,
  "term" : NumberLong(6),
  "heartbeatIntervalMillis" : NumberLong(2000),
  "optimes" : {
  "lastCommittedOpTime" : {
  "ts" : Timestamp(1497939865, 1),
  "t" : NumberLong(6)
  },
  "appliedOpTime" : {
  "ts" : Timestamp(1497939865, 1),
  "t" : NumberLong(6)
  },
  "durableOpTime" : {
  "ts" : Timestamp(1497939865, 1),
  "t" : NumberLong(6)
  }
  },
  "members" : [
  {
  "_id" : 2,
  "name" : "127.0.0.1:27003",
  "health" : 1,
  "state" : 2,
  "stateStr" : "SECONDARY",
  "uptime" : 711,
  "optime" : {
  "ts" : Timestamp(1497939865, 1),
  "t" : NumberLong(6)
  },
  "optimeDurable" : {
  "ts" : Timestamp(1497939865, 1),
  "t" : NumberLong(6)
  },
  "optimeDate" : ISODate("2017-06-20T06:24:25Z"),
  "optimeDurableDate" : ISODate("2017-06-20T06:24:25Z"),
  "lastHeartbeat" : ISODate("2017-06-20T06:24:30.730Z"),
  "lastHeartbeatRecv" : ISODate("2017-06-20T06:24:30.743Z"
),
  "pingMs" : NumberLong(0),
  "syncingTo" : "127.0.0.1:27002",
  "configVersion" : 5
  },
  {
  "_id" : 3,
  "name" : "127.0.0.1:27001",
  "health" : 1,
  "state" : 1,
  "stateStr" : "PRIMARY",
  "uptime" : 714,
  "optime" : {
  "ts" : Timestamp(1497939865, 1),
  "t" : NumberLong(6)
  },
  "optimeDate" : ISODate("2017-06-20T06:24:25Z"),
  "electionTime" : Timestamp(1497939664, 1),
  "electionDate" : ISODate("2017-06-20T06:21:04Z"),
  "configVersion" : 5,
  "self" : true
  },
  {
  "_id" : 4,
  "name" : "127.0.0.1:27002",
  "health" : 1,
  "state" : 2,
  "stateStr" : "SECONDARY",
  "uptime" : 69,
  "optime" : {
  "ts" : Timestamp(1497939865, 1),
  "t" : NumberLong(6)
  },
  "optimeDurable" : {
  "ts" : Timestamp(1497939865, 1),
  "t" : NumberLong(6)
  },
  "optimeDate" : ISODate("2017-06-20T06:24:25Z"),
  "optimeDurableDate" : ISODate("2017-06-20T06:24:25Z"),
  "lastHeartbeat" : ISODate("2017-06-20T06:24:30.740Z"),
  "lastHeartbeatRecv" : ISODate("2017-06-20T06:24:31.754Z"
),
  "pingMs" : NumberLong(0),
  "syncingTo" : "127.0.0.1:27001",
  "configVersion" : 5
  }
  ],
  "ok" : 1
}


更改已有副本集的优先级,从而达到更改主节点的目的
amazon:PRIMARY> cfg=rs.conf()
amazon:PRIMARY> cfg.members[0].priority=5
amazon:PRIMARY> rs.reconfig(cfg)   #重新加载配置文件,强制了副本集进行一次选举,优先级高的成为Primary.在这之间整个集群的所有节点都是secondary





