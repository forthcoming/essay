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


锁
悲观锁(Pessimistic Lock)
每次去拿数据的时候都认为别人会修改,所以每次在拿数据的时候都会上锁,这样别人想拿这个数据就会block直到它拿到锁
传统的关系型数据库里边就用到了很多这种锁机制,比如行锁,表锁等,读锁,写锁等,都是在做操作之前先上锁

乐观锁(Optimistic Lock)
每次去拿数据的时候都认为别人不会修改,所以不会上锁,但是在更新的时候会判断一下在此期间别人有没有去更新这个数据,可以使用版本号等机制

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
即使被读取的行被加了一致性锁定读,如果有另一个一致性非锁定读的操作来读取该行数据是不会阻塞的,读取的是改行的快照版本

MyISAM只支持表锁;InnoDB支持表锁和行锁,行锁是实现在索引上的,如果访问没有命中索引,也无法使用行锁,将退化为表锁
行锁对提高并发帮助很大;事务对数据一致性帮助很大
t_user(uid PK, uname, age, sex) innodb;
update t_user set age=10 where uid=1;            -- 命中索引,行锁
update t_user set age=10 where uid != 1;         -- 未命中索引,表锁(负向查询无法命中索引)
update t_user set age=10 where name='shenjian';  -- 无索引,表锁


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
serializable        N           N                  N            Y  写会加"写锁",读会加"读锁",当出现读写锁冲突的时候,后访问的事务必须等前一个事务执行完成才能继续执行

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

set autocommit=OFF;   # 关闭自动提交功能,当前会话有效
begin;     -- 在存储过程中,mysql会将begin识别为begin···end,所以在存储过程中,只能使用start transaction来表示开始一个事务
update student set score=score+10 where class=1;  # 只对本会话可见
savepoint point1;
update student set score=score-10 where class=2;
commit;    -- 一旦提交事务便结束,须再次开启事务才能使用
rollback;  -- 回滚到事务开始处并结束事务


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


index
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

联合索引(观察key_len和Extra,group by和order by都可以利用联合索引)
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

                                        
processlist 
show full processlist;  # 如果是root帐号,能看到所有用户的当前连接;如果是其他普通帐号,则只能看到自己占用的连接
+----+------+-----------------+------+---------+------+----------+-----------------------+
| Id | User | Host            | db   | Command | Time | State    | Info                  |
+----+------+-----------------+------+---------+------+----------+-----------------------+
|  2 | root | localhost:58448 | NULL | Sleep   |  104 |          | NULL                  |
|  3 | root | localhost:58451 | NULL | Query   |    1 | starting | show full processlist |
+----+------+-----------------+------+---------+------+----------+-----------------------+
id:     用户登录mysql时系统分配的"connection_id",可以使用函数connection_id()查看
user:   显示当前用户
host:   显示这个语句是从哪个ip的哪个端口上发出
db:     显示这个进程目前连接的是哪个数据库
command:显示当前连接的执行的命令,一般取值为sleep,query,connect等
time:   显示这个状态持续的时间,单位是秒
state:  显示使用当前连接的sql语句的状态,一个sql语句以查询为例,可能需要经过copying to tmp table、sorting result、sending data等状态才可以完成
info:   显示这个sql语句
需要注意的状态:
converting HEAP to MyISAM  查询结果太大时把结果放在磁盘(取出的结果或中间结果过大,内存临时表放不下; 服务器配置的临时表内存参数过小tmp_table_size,max_heap_table_size)
create tmp table           创建临时表
Copying to tmp table on disk 把内存临时表复制到磁盘
locked  被其他查询锁住
logging slow query 记录慢查询


profiles
set profiling=on;  # 也可以是off,只针对某个会话有效
show variables like '%profiling%';  # 必须要加引号
+------------------------+-------+
| Variable_name          | Value |
+------------------------+-------+
| have_profiling         | YES   |
| profiling              | ON    |
| profiling_history_size | 15    |
+------------------------+-------+
show profiles;
+----------+------------+-----------------------+
| Query_ID | Duration   | Query                 |
+----------+------------+-----------------------+
|        1 | 0.16313000 | SELECT DATABASE()     |
|        2 | 0.00021675 | select * from student |
+----------+------------+-----------------------+
show profile for query 2;
+----------------------+----------+
| Status               | Duration |
+----------------------+----------+
| starting             | 0.000045 |
| checking permissions | 0.000004 |
| Opening tables       | 0.000014 |
| init                 | 0.000024 |
| System lock          | 0.000005 |
| optimizing           | 0.000003 |
| statistics           | 0.000009 |
| preparing            | 0.000009 |
| executing            | 0.000002 |
| Sending data         | 0.000034 |
| end                  | 0.000003 |
| query end            | 0.000004 |
| closing tables       | 0.000004 |
| freeing items        | 0.000051 |
| cleaning up          | 0.000007 |
+----------------------+----------+


触发器
是一类特殊事务,可监视某种数据操作,并触发相关操作
insert型触发器:new表示将要或者已经更新的数据
update型触发器:old表示将要更新的数据,new表示已经更新的数据
delete型触发器:old表示将要或者已经删除的数据
create trigger trigger_name 
after/before insert/update/delete
on table_name for each row
begin
sql1;
......
sqlN;
end


case & if
select name,case class when 1 then 'one' when 2 then 'two' else 'unknown' end gender from student;
select name,if(class=1,'one','two') gender from student;


where group having order limit顺序不能乱
select class,avg(score) avg_score from student where class<3 group by class having avg_score<100 order by class limit 2;
where中不能出现聚集函数(max min avg count sum)直接作用于原表,但可以包含普通函数(upper)


view
create view view_name as select * from star where name like '张%' with check option;
作用:
1.简化查询
2.更精细的权限控制(例如隐藏密码字段)
注意:
视图是动态的数据集合,数据随着基表的更新而更新
只有当视图与基表一一对应时才能通过更改视图来更改基表数据
视图在mysql的data目录下只生成xx.frm文件即表结构,不生成表数据文件(myd)与表索引文件(myi)
with check option是对视图里面所有的name首字符必须是以"张"字打头,不管是修改前还是修改后都必须服从此规则
update view_name set name='刘家辉' where name='张家辉'; //Error
update view_name set name='张家界' where name='张家辉'; //OK
1.对于update/insert,有with check option,要保证更新后的数据能被视图查询出来
2.对于delete,有无with check option都一样


limit [offset,] N
offset 偏移量,可选,不写则相当于limit 0,N
N  取出条目


count
count(*): 计算表的行数
count(列名): 计算列名x中除null行以外的行数
注意: count(goods_id<30)不能实现逻辑小于30的效果,最终还是转换成count(*)来计算


导出/导入
mysqldump -uroot -p db_name [t_name] -l -F > db_name.sql   // 导出整个数据库或部分表,l代表读锁,防止数据写入,F即flush logs,从此刻开始重新生成新的日志文件
mysql -uroot -p db_name -v -f < db_name.sql   // use dbname;  +  source db_name.sql; v查看导入的详细信息,f是遇到错误时skip,继续执行后面语句
mysqlbinlog binlog-file   // 查看binlog
mysqlbinlog --stop-position='120' binlog-file |mysql -uroot -p db_name   // 用binlog日志恢复数据,stop-position指定结束位置,-d指定只要某个数据库


UNIQUE KEY & PRIMARY KEY
UNIQUE KEY约束的字段中不能包含重复值,PRIMARY KEY不可空不可重复,创建key的同时也会创建索引;表的外键是另一表的主键,外键可以有重复的,可以是空值
primary key = unique +  not null
区别如下:
1. 作为Primary Key的域/域组不能为null,而Unique Key可以
2. 在一个表中只能有一个Primary Key,建议使用递增整形做主键,而多个Unique Key可以同时存在
3. Primary Key一般在逻辑设计中用作记录标识,这也是设置Primary Key的本来用意,而Unique Key只是为了保证域/域组的唯一性


基本数据类型
tinyint    //1b,默认为signed
smallint   //2b
mediumint  //3b
int        //4b
bigint     //8b
float(M,D) //默认为signed,M代表总位数,D代表小数位的个数
char(N)    //定长,N表示字符个数,不表示字节,不够N个长度时在末尾用空格补充,取出时又将尾部的空格省掉(若数据末尾自身含有空格,取出时也将被去掉),相对于变长访问速度更快
varchar(N) //变长,不够长度时不用空格补齐,但内容前有1之2个字节来标记该列的长度
date       // YYYY-MM-DD  如:2010-03-14
time       // HH:MM:SS    如:19:26:32
datetime   // YYYY-MM-DD  HH:MM:SS 如:2010-03-14 19:26:32
timestamp  // YYYY-MM-DD  HH:MM:SS 特性:不用赋值,该列会为自己赋当前的具体时间


分表 & partition
数据量太大可考虑分表,例如根据用户id与10取模,将用户信息存储到不同的十张表里面
create table topic(
    tid int primary key auto_increment,
    title char(20) not null default ''
)engine innodb charset utf8   # 不支持myisam
# partition by hash( tid ) partitions 4   # 只能用数字类型,根据tid%4分区(默认名字p0,p1,p2,p3),可通过explain查看查询需要的分区
partition by range(tid)(      # 还支持hash,list等分区
    partition t0 values less than(1000),
    partition t1 values less than(2000),
    partition t2 values less than(maxvalue)
)


Myisam & InnoDB(默认)
区别:
1. InnoDB支持事务,Myisam不支持,对于InnoDB每一条SQL语言都默认封装成事务,自动提交,这样会影响速度,所以最好把多条SQL语言放在begin和commit之间,组成一个事务
2. InnoDB支持外键,而Myisam不支持,对一个包含外键的InnoDB表转为MYISAM会失败
3. InnoDB是聚集索引,必须要有主键,通过主键索引效率很高,但辅助索引需要两次查询,先查询到主键,然后再通过主键查询到数据.因此主键不应该过大,因为主键太大,其他索引也都会很大
   Myisam是非聚集索引,数据文件是分离的,索引保存的是数据文件的指针,主键索引和辅助索引是独立的
4. InnoDB不保存表的具体行数,执行select count(*) from table时需要全表扫描,而MyISAM用一个变量保存了整个表的行数,执行上述语句时只需要读出该变量即可,速度很快
5. InnoDB只包含一个*.frm文件,MyISAM包含*.frm(结构), *.MYD(数据文件),*.MYI(索引)
如何选择:
1. 是否要支持事务,如果要请选择innodb,如果不需要可以考虑Myisam
2. 如果表中绝大多数都只是读查询,可以考虑Myisam,如果既有读写也挺频繁,请使用InnoDB


Oracle批量删除和查询表数据
select 'truncate table '||table_name||';' from user_tables;
select 'select * from '||table_name||';' from user_tables;

                                        
                                        login
mysql.user表具有全局性,控制着用户的登录信息和登录后的权限
mysql_secure_installation  // 设置root密码是否允许远程登录等信息
指定哪些IP可以连入:
update user set host='192.168.8.%' where host='::1';
flush privileges;
验证(当同一台服务器启动了多个mysqld,用mysql命令登录时需要明确指定-h[ip],不能是localhost,否则登录的都是默认的3306端口):
mysql -h192.168.9.6 -uroot -p
创建用户/密码,并赋予该用户可以用192.168.1网段登陆:
GRANT ALL PRIVILEGES ON *.* TO 'avatar'@'192.168.1.%' IDENTIFIED BY 'avatar' WITH GRANT OPTION;
flush privileges;
注意:
以上所有改变都保存在mysql库下的user表中
select host,user,authentication_string from mysql.user;


common
like  %匹配任意字符,_匹配单个字符
explain sql;     // obtain information about table structure or query execution plans
auto_increment:there can be only one auto column and it must be defined as a key
判断空(null)只能用is null/is not null来判断,建表时通常设置默认属性default,使其不为null
1. null的列使用索引,索引统计,值都更加复杂,MySQL更难优化
2. null需要更多的存储空间
utf8mb4是utf8的超集,有存储4字节例如表情符号时使用它
? data types  //显示所有数据类型
? int     //显示int的具体属性
? show    //显示show的语法
\s        //查看当前用户的信息
mysql -u[username] -p[password] -h[host] -P[port]
create database [dname];
create table t_name as select * from t1_name;  // 不完全复制表结构(只包含基本的字段信息),并插入数据
create table t_name like t1_name;  // 完全复制表结构(包括主键,分区等)
drop database [dname];
drop table [tname];  
use [dname];
desc [tname];
truncate [tname];     
insert into [tname] values(...),(...);
insert into t_name(...,...,...) select ...,...,... from t1_name;
delete from [tname] where .... and...;
update [tname] set ... , ... where ... and ...;
select [distinct] * from [tname] where ... and ...; 
select count(1) from (select * from mysql.user) tt;                                                  // from子查询,临时表需要加别名
select * from article where (title,content,uid) = (select title,content,uid from blog where bid=2);  // where子查询
select * from article where (title,content,uid) in (select title,content,uid from blog);             // where子查询
show variables;  //显示各种变量(配置文件参数)
show triggers;
show tables;
show databases;
show procedure status;
show create procedure create_ktv_requested_song_by_month;
show events;  // 查看定时任务
show create table t_name;
show create database db_name;	
select now(),SUBDATE(now(),INTERVAL 1 MINUTE),SUBDATE(now(),INTERVAL -1 MINUTE) from dual; -- 2019-07-29 18:00:59 | 2019-07-29 17:59:59 | 2019-07-29 18:01:59
alter table t_name add name varchar(255) not null default avatar after created_time; //加在列created_time后面,add之后的旧列名之后的语法和创建表时的列声明一样
alter table t_name change 旧列名 新列名 列类型 列参数
rename table old_name to new_name;
(select aid,title from article limit 2) union all (select bid,title from blog limit 2);  //在UNION中如果对SELECT子句做限制,需要对SELECT添加圆括号,ORDER BY类似
insert into test ( _id, version, flag ) values( 1, '1.0', 1 ) on duplicate key update version = '2.0',flag = 0; # upsert,当主键_id冲突时会执行后面的update操作
# 创建一个从2019-02-22 16:30:00开始到10分钟后结束,每隔1分钟运行pro的事件
create event if not exists test on schedule every 1 minute starts '2019-02-22 16:30:00' ends '2019-02-22 16:30:00'+ interval 10 minute do call pro( );


binlog
使用场景(binlog日志与数据库文件在同目录中)
1. MySQL主从复制: 在master开启binlog,master把它的二进制日志传递给slave来达到数据一致的目的
2. 使用mysqlbinlog工具恢复数据
show master logs;   # 查看所有binlog日志列表
show master status; # 查看最新一个binlog日志的名称及最后一个操作事件的Position
flush logs;         # 刷新日志,自此刻开始产生一个新的binlog日志文件(每当mysqld重启or在mysqldump备份数据时加-F选项都会执行该命令)
reset master;       # 清空所有binlog日志
show binlog events in '201810-08571-bin.000001' from pos limit m,n;  # 日志查询


主从复制(slave执行查询操作,降低master访问压力,实时性要求高的数据仍需要从master查询)
1. 主开启binlog
2. 主从设置唯一的server_id
3. 主创建主从复制用户(repl)并授权
# delete from mysql.user where user='repl';
create user 'repl'@'localhost' identified by 'repl';
grant replication slave on *.* to 'repl'@'localhost';  # *.*代表所有数据库的所有表
# select * from mysql.user;
# reset master;
show master status;
4.从使用主创建的用户(repl),授权之前要登录一下授权账号repl,why?
# reset slave;
stop slave;
change master to 
master_host = 'localhost',
master_user = 'repl',
master_port = 3306,
master_password = 'repl',
master_log_file = 'binlog.000001',  # replacing the option values with the actual values relevant to your system
master_log_pos = 155;
start slave;
5. 检查主从状态
show slave status;     # 以下两项都为Yes才说明主从创建成功
Slave_IO_Running:Yes   读主服务器binlog日志,并写入从服务器的中继日志中
Slave_SQL_Running:Yes  执行中继日志


