UNIQUE KEY & PRIMARY KEY
UNIQUE KEY约束的字段中不能包含重复值,PRIMARY KEY不可空不可重复,创建key的同时也会创建索引;表的外键是另一表的主键,外键可以有重复的,可以是空值
primary key = unique +  not null
区别如下:
1. 作为Primary Key的域/域组不能为null,而Unique Key可以
2. 在一个表中只能有一个Primary Key,建议使用递增整形做主键,而多个Unique Key可以同时存在
3. Primary Key一般在逻辑设计中用作记录标识,这也是设置Primary Key的本来用意,而Unique Key只是为了保证域/域组的唯一性


联合索引(观察key_len和Extra,group by和order by都可以利用联合索引)
最左匹配原则在遇到范围查询时,会阻断后续索引
create table idx(
c1 char(1) not null default '',
c2 char(1) not null default '',
c3 char(1) not null default '',
c4 char(1) not null default '',
c5 char(1) not null default '',
key(c1,c2,c3,c4)
)engine innodb charset utf8;
insert into idx values('a','b','c','a','e'),('A','b','c','b','e'),('a','B','c','c','e');

mysql> explain select * from idx where c1='a' and c2='b' and c4>'a' and c3='c'\G
*************************** 1. row ***************************
           id: 1
  select_type: SIMPLE
        table: idx
   partitions: NULL
         type: range # 从最好到最差的连接类型为const、eq_reg、ref(根据索引列直接定位到某些数据行)、range(根据索引做范围查询)、index和all
possible_keys: c1
          key: c1
      key_len: 12
          ref: NULL
         rows: 2
     filtered: 100.00
        Extra: Using index condition
        
mysql> explain select * from idx where c1='a' and c2='b' and c4='a' order by c5\G
*************************** 1. row ***************************
           id: 1
  select_type: SIMPLE
        table: idx
   partitions: NULL
         type: ref
possible_keys: c1
          key: c1
      key_len: 6
          ref: const,const
         rows: 3
     filtered: 33.33
        Extra: Using index condition; Using filesort
                                                                             
mysql> explain select * from idx where c1='a' and c4='a' order by c3\G
*************************** 1. row ***************************
           id: 1
  select_type: SIMPLE
        table: idx
   partitions: NULL
         type: ref
possible_keys: c1
          key: c1
      key_len: 3
          ref: const
         rows: 3
     filtered: 33.33
        Extra: Using index condition; Using filesort  # 如果where字段跟order by字段不能使用联合索引的左前缀,则需要额外排序
                                        
mysql> explain select * from idx where c1='a' and c5='e' order by c2,c3\G
*************************** 1. row ***************************
           id: 1
  select_type: SIMPLE
        table: idx
   partitions: NULL
         type: ref
possible_keys: c1
          key: c1
      key_len: 3
          ref: const
         rows: 3
     filtered: 33.33
        Extra: Using where
        
mysql> explain select * from idx where c1='a' and c5='e' order by c3,c2\G
*************************** 1. row ***************************
           id: 1
  select_type: SIMPLE
        table: idx
   partitions: NULL
         type: ref
possible_keys: c1
          key: c1
      key_len: 3
          ref: const
         rows: 3
     filtered: 33.33
        Extra: Using where; Using filesort
                                                
mysql> explain select * from idx where c1='a' and c2='b' and c5='e' order by c3,c2\G  # 注意排序中的c2是常量
*************************** 1. row ***************************
           id: 1
  select_type: SIMPLE
        table: idx
   partitions: NULL
         type: ref
possible_keys: c1
          key: c1
      key_len: 6
          ref: const,const
         rows: 3
     filtered: 33.33
        Extra: Using index condition; Using where
        

mysql> explain select * from idx where c1='a' and c4='b' group by c2,c3\G
*************************** 1. row ***************************
           id: 1
  select_type: SIMPLE
        table: idx
   partitions: NULL
         type: ref
possible_keys: c1
          key: c1
      key_len: 3
          ref: const
         rows: 3
     filtered: 33.33
        Extra: Using index condition

mysql> explain select * from idx where c1='a' and c4='b' group by c3,c2\G
*************************** 1. row ***************************
           id: 1
  select_type: SIMPLE
        table: idx
   partitions: NULL
         type: ref
possible_keys: c1
          key: c1
      key_len: 3
          ref: const
         rows: 3   # 估计扫描了多少行
     filtered: 33.33
        Extra: Using index condition; Using temporary   # Using filesort & Using temporary:看到这个的时候,查询需要优化了
 
mysql> explain select * from idx where c1>'a' order by c1,c2\G
*************************** 1. row ***************************
           id: 1
  select_type: SIMPLE
        table: idx
   partitions: NULL
         type: range
possible_keys: c1
          key: c1
      key_len: 3
          ref: NULL
         rows: 1
     filtered: 100.00
        Extra: Using index condition

mysql> explain select * from idx where c1>'a' order by c2,c3\G
*************************** 1. row ***************************
           id: 1
  select_type: SIMPLE
        table: idx
   partitions: NULL
         type: range
possible_keys: c1
          key: c1
      key_len: 3
          ref: NULL
         rows: 1
     filtered: 100.00
        Extra: Using index condition; Using filesort

mysql> explain select * from idx where c1='a' order by c2,c3\G
*************************** 1. row ***************************
           id: 1
  select_type: SIMPLE
        table: idx
   partitions: NULL
         type: ref
possible_keys: c1
          key: c1
      key_len: 3
          ref: const
         rows: 3
     filtered: 100.00
        Extra: NULL


索引长度 & 区分(Index Selectivity)
The ratio of the number of distinct values in the indexed column / columns to the number of records in the table represents the selectivity of an index. The ideal selectivity is 1
lf an index on a table of 100'000 records had only 500 distinct values, then the index's selectivity is 500 / 100'000 = 0.005 and in this case a query which uses the limitation of such an index will retum 100'000 / 500 = 200 records for each distinct value. 
It is evident that a full table scan is more efficient as using such an index where much more I/O is needed to scan repeatedly the index and the table. 

对于字符型列,索引长度越大,区分度越高,但会占用更多的空间,因此需要在两者间做一个权衡
惯用手法:在字符列截取不同长度,测试其区分度,选择一个合适的索引长度
select count(distinct(left(word,4)))/count(1) from tb_name;
alter table tb_name add index word(word(4));  -- 指定索引长度为4(如果指定字符集为utf8,key_len大概为4*3=12),联合索引也能这么建
前缀索引兼顾索引大小和查询速度,但是其缺点是不能用于ORDER BY和GROUP BY操作,也不能用于Covering index(不包含被截取列的情况下任然可以)
对于左前缀不易区分的列如网址,有两种解决方案
1. 把列内容倒过来存储
2. 增加哈希列,即同时把列的哈希存进来,并对哈希列建索引


聚簇索引 & 非聚簇索引
聚簇索引叶子结点存储了真实的数据,在一张表上最多只能创建一个聚簇索引,因为真实数据的物理顺序只能有一种
InnoDB一定会建立聚簇索引,把实际数据行和相关的键值保存在一起
  1. 有主键时,根据主键自动创建聚簇索引;
  2. 没有主键时,会用一个唯一且不为空的索引列做为主键,成为此表的聚簇索引;
  3. 如果以上两个都不满足那innodb自己创建一个虚拟的聚集索引.
优点: 对于范围查询的效率很高,因为其数据是按照大小排列,找到索引也就找到了数据
建议使用int的auto_increment作为主键(按主键递增顺序插入)
聚簇索引的二级索引叶子节点不会保存引用的行的物理位置,而是保存了行的主键值,减小了移动数据或者数据页面分裂时维护二级索引的开销
通过二级索引查询首先查到是主键值,然后InnoDB再通过主键索引找到相应的数据块        
非聚簇索引叶结点包含索引字段值及指向数据页数据行的逻辑指针,并不是数据本身,MyISAM二级索引叶结点和主键索引在存储结构上没有任何区别
MYISAM引擎的索引文件.MYI和数据文件.MYD相互独立,索引和数据没放在一块,索引对应的是磁盘位置,不得不通过磁盘位置访问磁盘数据


show index from table_name;
create index index_name on t_name(..,..,..);
drop index index_name on t_name;
btree索引: 适宜范围查询;左前缀匹配;全值匹配
hash索引: 理论寻址O(1);无法排序优化;必须回行;不能前缀索引;不适宜范围查询
innodb,myisam支持自适应哈希索引,根据表的使用情况自动为表生成哈希索引,无法人为指定
查询条件中的列使用函数或者表达式,则无法使用索引
查询条件如果包含类型转换(如score为int类型下where score='98'),则无法使用索引                                        
like匹配某列的前缀字符串可以使用索引
Only the InnoDB and MyISAM storage engines support FULLTEXT indexes and only for CHAR, VARCHAR, and TEXT columns
alter table test add fulltext(title,content)
InnoDB用户无法手动创建哈希索引,这一层上说InnoDB确实不支持哈希索引
InnoDB会自调优(self-tuning),如果判定建立自适应哈希索引(Adaptive Hash Index, AHI),能够提升查询效率,InnoDB自己会建立相关哈希索引,这一层上说InnoDB又是支持哈希索引


覆盖索引(covering index)
一个查询语句只用从索引中就能够取得,不必从数据表中读取,也可以称之为实现了索引覆盖,这样避免了查到索引后再返回表操作,减少I/O提高效率
Explain的时候,输出的Extra信息中如果有"Using Index",就表示这条查询使用了覆盖索引
InnoDB二级索引的叶子节点包含了主键值,所以查询字段包含主键时也可以覆盖查询


索引延迟关联
我们尽量只查有索引的ID,速度非常快,然后再根据查出来的id进行join一次性取具体数据,这就是延迟索引
CREATE TABLE `profiles` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sex` tinyint(4) NOT NULL DEFAULT '0',
  `rating` smallint(6) NOT NULL DEFAULT '0',
  `name` varchar(10) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=MyISAM
select sql_no_cache * from profiles limit 200000,10000;
mysql> explain select sql_no_cache * from profiles limit 200000,10000\G
*************************** 1. row ***************************
           id: 1
  select_type: SIMPLE
        table: profiles
   partitions: NULL
         type: ALL
possible_keys: NULL
          key: NULL
      key_len: NULL
          ref: NULL
         rows: 241000
     filtered: 100.00
        Extra: NULL
select sql_no_cache profiles.* from profiles join (select id from profiles limit 200000,10000) x on profiles.id=x.id; # 0.077
mysql> explain select sql_no_cache profiles.* from profiles join (select id from profiles limit 200000,10000) x on profiles.id=x.id\G
*************************** 1. row ***************************
           id: 1
  select_type: PRIMARY
        table: <derived2>
   partitions: NULL
         type: ALL
possible_keys: NULL
          key: NULL
      key_len: NULL
          ref: NULL
         rows: 210000
     filtered: 100.00
        Extra: NULL
*************************** 2. row ***************************
           id: 1
  select_type: PRIMARY
        table: profiles
   partitions: NULL
         type: eq_ref
possible_keys: PRIMARY
          key: PRIMARY
      key_len: 4
          ref: x.id
         rows: 1
     filtered: 100.00
        Extra: NULL
*************************** 3. row ***************************
           id: 2
  select_type: DERIVED
        table: profiles
   partitions: NULL
         type: index
possible_keys: NULL
          key: PRIMARY
      key_len: 4
          ref: NULL
         rows: 241000
     filtered: 100.00
        Extra: Using index
注意: 如果把存储引擎换成innodb,两者速度一样快


悲观锁(Pessimistic Lock)
每次去拿数据的时候都认为别人会修改,所以每次在拿数据的时候都会上锁,这样别人想拿这个数据就会block直到它拿到锁
传统的关系型数据库里边就用到了很多这种锁机制,比如行锁,表锁等,读锁,写锁等,都是在做操作之前先上锁

乐观锁(Optimistic Lock)
每次去拿数据的时候都认为别人不会修改,所以不会上锁,但是在更新的时候会判断一下在此期间别人有没有去更新这个数据,可以使用递增版本号或时间戳等机制(避免ABA问题)
注意mysql在更新操作时会对数据行加锁,保证了version的正确性
乐观锁适用于写比较少的情况下,即冲突真的很少发生的时候,这样可以省去了锁的开销,加大了系统的整个吞吐量
但如果经常产生冲突,上层应用会不断的进行retry,这样反倒是降低了性能,所以这种情况下用悲观锁就比较合适

读锁
lock table t1 read # 所有客户端都只能读,insert/update/delete都将被阻塞,一旦数据表被加上读锁,其他请求可以对该表再次增加读锁,但是不能增加写锁
写锁
lock table t1 write # 只有本人可以增删改查,其他人增删改查都不行,一旦数据表被加上写锁,其他请求无法在对该表增加读锁和写锁

在使用lock table之后,解锁之前,当前会话不能操作未加锁的表
MyISAM在执行查询语句(SELECT)前,会自动给涉及的所有表加读锁,在执行更新操(UPDATE/DELETE/INSERT)前会自动给涉及的表加写锁

SELECT … FOR UPDATE   # 显式地给一条记录加写锁(行锁),因此其他事务不能获取该记录的任何锁
SELECT … LOCK IN SHARE MODE  # 显式地给记录加读锁(行锁),因此其他事务能够获取该记录的读锁而不能获取该记录的写锁
当一个事务提交了,锁就释放了,因此在使用上述两个SELECT锁定语句时必须开启事务
即使被读取的行被加了一致性锁定读,如果有另一个一致性非锁定读的操作来读取该行数据是不会阻塞的,读取的是该行的快照版本

MyISAM只支持表锁;InnoDB支持表锁和行锁,行锁是实现在索引上的,如果访问没有命中索引,也无法使用行锁,将退化为表锁
行锁对提高并发帮助很大;事务对数据一致性帮助很大
t_user(uid PK, uname, age, sex) innodb;
update t_user set age=10 where uid=1;            -- 命中索引,行锁
update t_user set age=10 where uid != 1;         -- 未命中索引,表锁(负向查询无法命中索引)
update t_user set age=10 where name='shenjian';  -- 无索引,表锁


死锁成因(为表添加合理索引会大大降低死锁概率)
事物A                                    事务B
update test set name='TA' where _id=1;         
                                         update test set name='TB' where _id=2;   
update test set name='TA' where _id=2;           
                                         update test set name='TB' where _id=1;           
解决死锁方法:
1. 设置最大等待时间
2. wait-for graph原理,检测有向图是否出现环路,出现环路就是死锁


Row-Level Locking
MySQL uses row-level locking for InnoDB tables to support simultaneous write access by multiple sessions, making them suitable for multi-user, highly concurrent, and OLTP applications.
Advantages of row-level locking:
Fewer lock conflicts when different sessions access different rows.
Fewer changes for rollbacks.
Possible to lock a single row for a long time.
Table-Level Locking
MySQL uses table-level locking for MyISAM, MEMORY, and MERGE tables, permitting only one session to update those tables at a time. 
This locking level makes these storage engines more suitable for read-only, read-mostly, or single-user applications.
Advantages of table-level locking:
Relatively little memory required (row locking requires memory per row or group of rows locked)
Fast when used on a large part of the table because only a single lock is involved.
Fast if you often do GROUP BY operations on a large part of the data or must scan the entire table frequently.

MySQL grants table write locks as follows:
If there are no locks on the table, put a write lock on it.
Otherwise, put the lock request in the write lock queue.
MySQL grants table read locks as follows:
If there are no write locks on the table, put a read lock on it.
Otherwise, put the lock request in the read lock queue.
Table updates are given higher priority than table retrievals. Therefore, when a lock is released, the lock is made available to the requests in the write lock queue and then to the requests in the read lock queue. 
This ensures that updates to a table are not “starved” even when there is heavy SELECT activity for the table. However, if there are many updates for a table, SELECT statements wait until there are no more updates.


Transaction
原子性:多步操作逻辑上不可分割,要么都成功,要么都不成功
一致性:操作前后值的变化逻辑上成立
隔离性:事务结束前不会影响到其他会话
持久性:事务一旦提交无法撤回

mysql> show variables like '%isolation%';
+-----------------------+-----------------+
| Variable_name         | Value           |
+-----------------------+-----------------+
| transaction_isolation | REPEATABLE-READ |
+-----------------------+-----------------+
set session transaction isolation level [read uncommitted] | [read committed] | [repeatable read] | [serializable];
read uncommitted(读取未提交内容): 所有事务都可以看到其他未提交事务的执行结果,本隔离级别很少用于实际应用,也被称之为脏读
read committed(读取提交内容): 一个事务只能看见其他已经提交事务所做的改变,支持所谓的不可重复读(在一个事务的两次查询之中数据不一致)
repeatable read(可重读): 在同一个事务中多次读取同样记录的结果是一致的,不受其他事务提交的影响
隔离级别             脏读可能性    不可重复读可能性     幻读可能性    加锁读   
read uncommitted    Y           Y                  Y            N    
read committed      N           Y                  Y            N
repeatable read     N           N                  Y            N
serializable        N           N                  N            Y  写会加"写锁",读会加"读锁",当出现读写锁冲突的时候,后访问的事务必须等前一个事务执行完成才能继续执行(A读B写和A写B读通条数据都会阻塞)

一致性非锁定读: 
要读取的行被加了排他锁(写锁),这时候读取操作不会等待行上锁的释放,而是会读取行的一个快照数据,每行记录可能有多个版本
在事务隔离级别READ COMMITTED(RC)和REPEATABLE READ(简写RR)下,InnoDB存储引擎使用一致性非锁定读,但是对快照的定义却不相同
在RC下,一致性非锁定读总是读取被锁定行的最新一份快照数据;而在RR级别下,总是读取事务开始时的数据版本

并发事务中如果在更改同一条数据,那么先改的会成功,后改的会被阻塞,直到先改的事务提交后才能修改成功,可以理解为加了写锁
幻读: 在一个事务中,第一次查询某条记录没有,但试图更新这条记录时竟然能成功,并且再次读取同一条记录,它就神奇地出现了(应为在另一个事务中插入了该记录并已提交)

事务的隔离性是由锁来实现,隔离级别的隔离性越低,并发能力就越强,MySQL的默认隔离级别为repeatable read
MySQL默认开启一个事务,自动提交,每成功执行一个SQL,一个事务就会马上COMMIT,所以不能Rollback
MySQL事务是基于UNDO/REDO日志
UNDO日志记录修改前状态,ROLLBACK基于UNDO日志实现; REDO日志记录修改后的状态,COMMIT基于REDO日志实现,执行COMMIT数据才会被写入磁盘

show variables like "%autocommit%";  # mysql默认是on,可通过set autocommit=off;关闭
set autocommit=off;   # 关闭自动提交功能,当前会话有效,绝大部分sql语句都会自动开启事(个别语句如建表等除外),即begin可以省略
begin;     -- 在存储过程中,mysql会将begin识别为begin···end,所以在存储过程中,只能使用start transaction来表示开始一个事务
update student set score=score+10 where class=1;  # 只对本会话可见
savepoint point1;
update student set score=score-10 where class=2;
commit;    -- 一旦提交事务便结束,须再次开启事务才能使用
rollback;  -- 回滚到事务开始处并结束事务

                                        
show full processlist;         # 显示连接数(有上限)
show status like 'Threads%';   # 显示连接数(Threads_connected)
netstat -anp|grep '10.1.208.25:3306'
                                       
show status like 'innodb_row_lock_%';
Innodb_row_lock_current_waits: 当前等待锁的数量
Innodb_row_lock_time: 系统启动到现在,锁定的总时间长度(单位毫秒,同下)
Innodb_row_lock_time_avg: 每次平均锁定的时间
Innodb_row_lock_time_max: 最长一次锁定时间
Innodb_row_lock_waits: 系统启动到现在总共锁定的次数

select * from information_schema.innodb_trx;  # 当前运行的所有事务
select trx_id from information_schema.innodb_trx where trx_mysql_thread_id = connection_id();  # 查看当前绘话开启的事务id
trx_state: 事务执行状态,允许值是RUNNING,LOCK WAIT,ROLLING BACK,COMMITTING,被阻塞的事务状态是LOCK WAIT
trx_wait_started: 事务开始等待锁定的时间,前提是trx_state=LOCK WAIT;否则NULL
trx_mysql_thread_id: MySQL线程ID,与show processlist中的ID值相对应,可通过kill杀死
trx_query: 事务正在执行的SQL语句
trx_tables_in_use: The number of InnoDB tables used while processing the current SQL statement of this transaction.
trx_isolation_level: 当前事务的隔离级别

select * from performance_schema.data_locks;
ENGINE: The storage engine that holds or requested the lock.
ENGINE_TRANSACTION_ID: The storage engine internal ID of the transaction that requested the lock. This can be considered the owner of the lock, although the lock might still be pending, not actually granted yet (LOCK_STATUS='WAITING').
OBJECT_SCHEMA: The schema that contains the locked table.
OBJECT_NAME: The name of the locked table.
INDEX_NAME: The name of the locked index, if any; NULL otherwise.
LOCK_TYPE: The type of lock.The value is storage engine dependent. For InnoDB, permitted values are RECORD for a row-level lock, TABLE for a table-level lock.
LOCK_MODE: How the lock is requested.The value is storage engine dependent. For InnoDB, permitted values are S[,GAP], X[,GAP], IS[,GAP], IX[,GAP], AUTO_INC, and UNKNOWN. 
LOCK_STATUS: The status of the lock request.The value is storage engine dependent. For InnoDB, permitted values are GRANTED (lock is held) and WAITING (lock is being waited for).
LOCK_DATA: The data associated with the lock, if any. The value is storage engine dependent. For InnoDB, a value is shown if the LOCK_TYPE is RECORD, otherwise the value is NULL. 

select * from performance_schema.data_lock_waits;


