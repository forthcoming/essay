### login

```
mysql.user表具有全局性,控制着用户的登录信息和登录后的权限
mysql_secure_installation  // 设置root密码是否允许远程登录等信息
指定哪些IP可以连入:
update user set host='192.168.8.%' where host='::1';
flush privileges;
创建用户/密码,并赋予该用户可以用192.168.1网段登陆:
GRANT ALL PRIVILEGES ON *.* TO 'avatar'@'192.168.1.%' IDENTIFIED BY 'avatar' WITH GRANT OPTION;
flush privileges;
注意:
以上所有改变都保存在mysql库下的user表中
select host,user,authentication_string from mysql.user;
```

### profiles(分析SQL语句执行的资源消耗情况)

```
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
```

### processlist

```
show full processlist;  # 如果是root帐号,能看到所有用户的当前连接;如果是其他普通帐号,则只能看到自己占用的连接
kill Id;                # 杀死指定Id的sql语句,常用于mysql死锁情况  
select concat('kill ',id,';') from information_schema.processlist where user ='root';  # 批量杀死
+----+------+-----------------+------+---------+------+----------+-----------------------+
| Id | User | Host            | db   | Command | Time | State    | Info                  |
+----+------+-----------------+------+---------+------+----------+-----------------------+
|  2 | root | localhost:58448 | NULL | Sleep   |  104 |          | NULL                  |
|  3 | root | localhost:58451 | NULL | Query   |    1 | starting | show full processlist |
+----+------+-----------------+------+---------+------+----------+-----------------------+
id:     用户登录mysql时系统分配的"connection_id",可以使用函数connection_id()查看
user:   显示当前用户
host:   显示这个语句是从哪个ip:port上发出
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
```

### 导出/导入

```
mysqldump -uroot -p db_name [t_name] -l > db_name.sql // 导出整个数据库或部分表,l代表读锁,防止数据写入
mysql -uroot -p db_name -v -f < db_name.sql  // v查看导入的详细信息,f是遇到错误时skip,继续执行后面语句
use dbname; source db_name.sql;   // 导入数据
```

### 基本数据类型

```
tinyint      //1b,默认为signed
smallint     //2b
mediumint    //3b
int          //4b
bigint       //8b
float(M,D)   //默认为signed,M代表总位数,D代表小数位的个数
char(N)      //定长,N表示字符个数,不表示字节,不够N个长度时在末尾用空格补充,取出时又将尾部的空格省掉(若数据末尾自身含有空格,取出时也将被去掉),相对于变长访问速度更快
varchar(N)   //变长,不够长度时不用空格补齐,但内容前有1之2个字节来标记该列的长度
varbinary(N) //变长,字节最多为N,对于字母数字等没区别,但对于汉字等有区别
date         // YYYY-MM-DD  如:2010-03-14, The supported range is '1000-01-01' to '9999-12-31'.
time         // HH:MM:SS    如:19:26:32
datetime     // YYYY-MM-DD HH:MM:SS 如:2010-03-14 19:26:32, 支持范围从'1000-01-01 00:00:00' 到 '9999-12-31 23:59:59'
json         // column_name->'$.key_name'方式查询json
```

### trigger

```
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
```

### view

```
create view view_name as select * from star where name like '张%' with check option;
作用: 简化查询; 更精细的权限控制(例如隐藏密码字段)
注意:
视图是动态的数据集合,数据随着基表的更新而更新
只有当视图与基表一一对应时才能通过更改视图来更改基表数据
视图在mysql的data目录下只生成xx.frm文件即表结构,不生成表数据文件(myd)与表索引文件(myi)
with check option是对视图里面所有的name首字符必须是以"张"字打头,不管是修改前还是修改后都必须服从此规则
update view_name set name='刘家辉' where name='张家辉'; //Error
update view_name set name='张家界' where name='张家辉'; //OK
1.对于update/insert,有with check option,要保证更新后的数据能被视图查询出来
2.对于delete,有无with check option都一样
```

### unique key & primary key & foreign key

```
unique key和primary key约束的字段不可重复,foreign key是另一表的主键,外键可以重复,可以是空值
创建key的同时会创建索引,primary key = unique +  not null
区别如下:
1. 作为primary key的域/域组不能为null,而unique key可以
2. 在一个表中只能有一个primary key,建议使用递增整形做主键,可以有多个unique key同时存在
```

### null

```
判断空(null)只能用is null/is not null来判断,建表时通常设置默认属性default,使其不为null
1. null的列使用索引,索引统计,值都更加复杂,MySQL更难优化
2. null需要更多的存储空间
```

### sql基础语法

```
sql执行顺序: from > where > group by > having > select > order by > limit
SELECT SLEEP(100);  # 模拟耗时查询
like  %匹配任意字符,_匹配单个字符
limit [offset,] N  offset是偏移量,默认为0; N取出条目
explain sql;     // obtain information about table structure or query execution plans
? data types  //显示所有数据类型
? int     //显示int的具体属性
? show    //显示show的语法
\s        //查看当前用户的信息
mysql -u[username] -p[password] -h[host] -P[port] -D[database] -A 
create database [dname];
create table t_name like t1_name;  // 完全复制表结构(包括主键,分区等)
insert into t_name(...,...,...) select ...,...,... from t1_name;
drop database [dname];
drop table [tname];  
use [dname];
desc [tname];
truncate [tname];  # 速度比delete更快,但truncate删除后不记录mysql日志,不可以恢复数据 
insert into [tname] values(...),(...);
delete from [tname] where .... and...;  
update [tname] set ... , ... where ... and ...;
select [distinct] * from [tname] where ... and ...; # where中不能出现聚集函数(max min avg count sum),但可以包含普通函数(upper等)
select count(*) from (select * from mysql.user) tt;  -- from子查询,临时表需要加别名,count(id<9)不能实现逻辑小于9的效果,count列名时计算的是非null行
select * from article where (title,content,uid) = (select title,content,uid from blog where bid=2);  // where子查询
select * from article where (title,content,uid) in (select title,content,uid from blog);   // where子查询,第一处括号不能省
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
alter table t_name add name varchar(255) not null default avatar; // add之后的列名语法和创建表时的列声明一样
alter table t_name add (column_1,column_2);  // 同时新增多列
alter table t_name change 旧列名 新列名 列类型 列参数
alter table t_name drop column column_name;
rename table old_name to new_name;
(select aid,title from article limit 2) union all (select bid,title from blog limit 2); //在UNION中如果对SELECT子句做限制,需要对SELECT添加圆括号,ORDER BY类似
# 创建一个从2019-02-22 16:30:00开始到10分钟后结束,每隔1分钟运行pro的事件
create event if not exists test on schedule every 1 minute starts '2019-02-22 16:30:00' ends '2019-02-22 16:30:00'+ interval 10 minute do call pro( );
# upsert,当唯一索引/主键索引冲突时会执行update操作,否则执行insert操作                                     
insert into test(_id, version, flag) values( 1, '1.0', 1 ) on duplicate key update version = '2.0',flag = 0; 
insert ignore into test(_id, version, flag) values( 1, '1.0', 1 ); -- 遇到duplicate约束时,ignore会直接跳过这条语句的插入
select name,case class when 1 then 'one' when 2 then 'two' else 'unknown' end gender from student;
select name,if(class=1,'one','two') gender from student;
```

### sql优化
```
insert into tb_name values(),,,();  # 批量插入
start transaction; insert into tb_name values(); insert into tb_name values(); commit;
按主键顺序插入
尽量降低主键长度,应为二级索引都会包含主键,主键太长会浪费存储空间,推荐auto_increment 
order by时根据排序字段建立合适索引,多字段排序时遵循最左前缀法则,尽量使用覆盖索引,排序的升降顺序跟索引保持一致
```

### 存储引擎

```
存储引擎就是存储数据,建立索引,更新查询数据等技术的实现方式
InnoDB逻辑存储结构: Tablespace -> Segment -> Extent(1M,一共64个Page) -> Page(16k) -> Row
show engines;
+--------------------+---------+----------------------------------------------------------------+--------------+------+------------+
| Engine             | Support | Comment                                                        | Transactions | XA   | Savepoints |
+--------------------+---------+----------------------------------------------------------------+--------------+------+------------+
| ARCHIVE            | YES     | Archive storage engine                                         | NO           | NO   | NO         |
| BLACKHOLE          | YES     | /dev/null storage engine (anything you write to it disappears) | NO           | NO   | NO         |
| MRG_MYISAM         | YES     | Collection of identical MyISAM tables                          | NO           | NO   | NO         |
| MyISAM             | YES     | MyISAM storage engine                                          | NO           | NO   | NO         |
| PERFORMANCE_SCHEMA | YES     | Performance Schema                                             | NO           | NO   | NO         |
| InnoDB             | DEFAULT | Supports transactions, row-level locking, and foreign keys     | YES          | YES  | YES        |
| MEMORY             | YES     | Hash based, stored in memory, useful for temporary tables      | NO           | NO   | NO         |
| CSV                | YES     | CSV storage engine                                             | NO           | NO   | NO         |
+--------------------+---------+----------------------------------------------------------------+--------------+------+------------+
InnoDB(默认) & Myisam区别:
1. InnoDB支持事务,Myisam不支持
2. InnoDB是聚集索引,支持行锁,Myisam是非聚集索引,支持表锁不支持行锁
3. InnoDB支持外键,而Myisam不支持
4. InnoDB只包含一个*.frm文件,MyISAM数据文件分离,包含*.frm(结构), *.MYD(数据文件),*.MYI(索引文件)
```

### transaction

```
原子性:多步操作逻辑上不可分割,要么都成功,要么都不成功
一致性:操作前后值的变化逻辑上成立
隔离性:事务结束前不会影响到其他会话
持久性:事务一旦提交无法撤回

show variables like '%transaction_isolation%';
+-----------------------+-----------------+
| Variable_name         | Value           |
+-----------------------+-----------------+
| transaction_isolation | REPEATABLE-READ |
+-----------------------+-----------------+
set session transaction isolation level [read uncommitted] | [read committed] | [repeatable read] | [serializable];
隔离级别             脏读可能性    不可重复读可能性     幻读可能性    加锁读   
read uncommitted    Y           Y                  Y            N    
read committed      N           Y                  Y            N
repeatable read     N           N                  Y            N
serializable        N           N                  N            Y  
read uncommitted(读取未提交内容): 所有事务都可以看到其他未提交事务的执行结果,被称为脏读,本隔离级别很少用于实际应用
read committed(读取提交内容): 一个事务只能看见其他已经提交事务所做的改变,会出现在一个事务的两次查询中数据不一致,被称为不可重复读
repeatable read(可重读): 在一个事务中多次查询相同数据结果不变,不受其他事务提交影响,但会出现幻读
serializable(可串行化): 写加写锁,读加读锁,当出现读写锁冲突的时候,后访问的事务必须等前一个事务执行完成才能继续执行(A读B写和A写B读同条数据都会阻塞)
幻读: 在A事务中,第一次查询某条记录没有,接着在B事务中插入了该记录并提交,然后在A事务中更新这条记录时成功,并且再次读取这条记录时能读到

一致性非锁定读: 
要读取的行被加了写锁,这时候读取操作不会等待行上锁的释放,而是会读取行的一个快照数据,每行记录可能有多个版本
在事务隔离级别READ COMMITTED(RC)和REPEATABLE READ(简写RR)下,InnoDB存储引擎使用一致性非锁定读,但是对快照的定义却不相同
在RC下,一致性非锁定读总是读取被锁定行的最新一份快照数据;而在RR级别下,总是读取事务开始时的数据版本

事务的隔离性是由锁来实现,隔离级别的隔离性越低,并发能力就越强,MySQL的默认隔离级别为repeatable read
并发事务中如果在更改同一条数据,那么先改的会成功,后改的会被阻塞,直到先改的事务提交后才能修改成功,可以理解为加了写锁

对于InnoDB,绝大部分sql语句(个别语句如建表等除外)都会自动开启事务,sql执行完事务自动COMMIT,所以不能rollback
show variables like "%autocommit%";  # mysql默认是on
set autocommit=off;   # 关闭自动提交功能,当前会话有效
start transaction;  # 事务内执行第一条sql语句(不包含select connection_id()等非sql语句)时才会真正开启事务
update student set score=score+10 where class=1;  # 只对本会话可见
savepoint point1;
update student set score=score-10 where class=2;
commit;    -- 一旦提交事务便结束,须再次开启事务才能使用
rollback;  -- 回滚到事务开始处并结束事务

SELECT
	trx_id,              # 事务ID,对应performance_schema.data_locks表的ENGINE_TRANSACTION_ID字段
	trx_state,           # 事务执行状态,允许值是RUNNING,LOCK WAIT,ROLLING BACK,COMMITTING,被阻塞的事务状态是LOCK WAIT
	trx_started,         # 事务开启时间
	trx_wait_started,    # 事务开始等待锁定的时间,前提是trx_state=LOCK WAIT;否则NULL
	trx_mysql_thread_id, # 事务所在客户端线程ID,等于connection_id(),与show processlist中的ID值相对应,可通过kill杀死
	trx_query,           # 事务正在执行的SQL语句
	trx_tables_in_use,   # 事务处理当前SQL语句时使用的InnoDB表的数量
	trx_isolation_level  # 当前事务的隔离级别
FROM
	information_schema.innodb_trx; # 当前运行的所有事务
```

### lock

```
行级锁(Row-Level Locking)
MySQL对InnoDB表使用行级锁定来支持多个会话同时写入访问,使其适合多用户、高并发和OLTP应用程序
优点: 
当不同会话访问不同行时,锁冲突更少
回滚更改较少 
可以长时间锁定单行
select … for update # 加行级写锁,其他事务不能获取该记录的任何读写锁
select … for share # 加行级读锁(不再是一致性非锁定读),其他事务能够获取该记录的读锁,不能获取该记录的写锁
必须在事物中才会生效,事务提交或回滚后会释放锁

表级锁(Table-Level Locking)
MySQL对MyISAM和MEMORY表使用表级锁定,一次只允许一个会话更新这些表,这种锁定级别更适合只读、主要读取或单用户应用程序
优点: 所需内存相对较少(行锁定锁定的每行都需要内存)
当查询表大部分数据时速度很快,因为只涉及一个锁
经常对大部分数据进行GROUP BY或频繁扫描整个表时速度很快
lock table t1 read; # 加表级读锁,任何客户端可以对该表再次加读锁,但不能加写锁,只允许select,insert/update/delete都将被阻塞
lock table t1 write; # 加表级写锁,只有当前客户端可以再次加读写锁,可以增删改查,其他任何客户端读写锁请求和增删改查都会被阻塞
unlock tables;  # 解锁表级读写锁,在使用lock table之后,unlock之前,当前客户端只能操作加锁的表
MyISAM在执行SELECT前,会自动给涉及的所有表加读锁,在执行insert/update/delete前会自动给涉及的表加写锁

MyISAM只支持表锁
InnoDB支持表锁和行锁,行锁是在索引上实现,如果访问没命中索引无法使用行锁,将退化为表锁

MySQL授予表写锁的方式: 如果表上没有锁,则在其上放置写锁,否则将锁请求放入写锁队列中
MySQL授予表读锁的方式: 如果表上没有写锁,则在其上放置读锁,否则将锁请求放入读锁队列中
表更新优先级高于表检索,因此当锁被释放时,该锁首先可供写锁队列中的请求使用,然后再供读锁队列中的请求使用(写锁优先)

悲观锁(Pessimistic Lock)
每次去拿数据的时候都认为别人会修改,所以每次在拿数据的时候都会上锁,这样别人想拿这个数据就会block直到它拿到锁
传统的关系型数据库里边就用到了很多这种锁机制,比如行锁,表锁,读写锁等,都是在做操作之前先上锁

乐观锁(Optimistic Lock)
每次去拿数据的时候都认为别人不会修改,所以不会上锁,但是在更新的时候会判断一下在此期间别人有没有去更新这个数据,可以使用递增版本号或时间戳等机制(避免ABA问题)
乐观锁适用于写比较少的情况下,即冲突真的很少发生的时候,这样可以省去了锁的开销,加大了系统的整个吞吐量
但如果经常产生冲突,上层应用会不断的进行retry,这样反倒是降低了性能,所以这种情况下用悲观锁就比较合适

SELECT
    ENGINE,                 # 锁所在存储引擎
	ENGINE_LOCK_ID,         # 锁ID
	ENGINE_TRANSACTION_ID,  # 请求锁的事务ID,可以被视为锁的所有者(尽管LOCK_STATUS=WAITING)
	OBJECT_SCHEMA,          # 被锁表所在的schema(数据库名)
	OBJECT_NAME,            # 被锁的表名
	INDEX_NAME,             # 锁定索引的名称
	LOCK_TYPE,              # 锁类型,该值取决于存储引擎,对于InnoDB,行级锁值为RECORD,表级锁值为TABLE
	LOCK_MODE,              # 锁如何被请求,该值取决于存储引擎,对于InnoDB,值为S[,GAP]、X[,GAP]、IS[,GAP]、IX[,GAP]、AUTO_INC和UNKNOWN
	LOCK_STATUS,            # 锁状态,该值取决于存储引擎,对于InnoDB,值为GRANTED(已持有锁)和WAITING(正在等待锁)
	LOCK_DATA               # 锁关联的数据,该值取决于存储引擎,对于InnoDB,如果LOCK_TYPE为RECORD,则显示一个值,否则该值为NULL
FROM
	performance_schema.data_locks;
	
show status like 'innodb_row_lock_%';
Innodb_row_lock_current_waits: 当前等待锁的数量
Innodb_row_lock_time: 系统启动到现在,锁定的总时间长度(单位毫秒,同下)
Innodb_row_lock_time_avg: 每次平均锁定的时间
Innodb_row_lock_time_max: 最长一次锁定时间
Innodb_row_lock_waits: 系统启动到现在总共锁定的次数

死锁案例(为表添加合理索引会大大降低死锁概率)
事物A                                    事务B
update test set name='TA' where _id=1;         
                                         update test set name='TB' where _id=2;   
update test set name='TA' where _id=2;           
                                         update test set name='TB' where _id=1;  
```

### index

```
show index from table_name;
create index index_name on t_name(... asc,.. desc,..);  # 默认升序
drop index index_name on t_name;
索引优点: 提高数据检索能力,通过索引列对数据进行排序,降低数据排序成本,提高并发能力(锁相关)
索引缺点: 占用额外空间,降低了表更新速度
索引失效情况:
查询条件使用函数或者表达式
查询条件包含类型转换,如score为int类型下where score='98',或者字符串不加''    
or两边都有索引时才会用上索引            
like 'xx%'可以使用索引,like '%xx'不可以使用索引

索引设计原则:
针对数据量大,查询频繁的表建立索引
针对常作为where,order by,group by操作的字段加索引
尽量选选择性高的列做索引,唯一索引和主键索引选择性为1
如果是字符串类型字段且长度较长,可建立前缀索引
尽量使用联合索引,节省空间,且利用覆盖索引机制提高查询效率

BTREE索引: 所有索引和数据都会出现在叶子结点,叶子结点形成有序双向链表,非叶子结点只存储索引;适宜范围查询;左前缀匹配;全值匹配
HASH索引: 只有精确匹配(in,=)索引列的查询才有效,不支持范围查询,innodb,myisam支持自适应哈希索引,根据表使用情况自动生成哈希索引,无法人为指定
FULLTEXT索引: 倒排索引,仅InnoDB和MyISAM存储引擎支持,且仅适用于CHAR、VARCHAR和TEXT列

聚集索引(Clustered index) & 非聚集索引
聚集索引叶子结点存储了真实的数据,在一张表上最多只能创建一个聚集索引,因为真实数据的物理顺序只能有一种
InnoDB一定会建立聚集索引,把实际数据行和相关的键值保存在一起
  1. 有主键时,根据主键自动创建聚集索引
  2. 没有主键时,会用第一个唯一索引列做为主键,成为此表的聚集索引
  3. 如果以上两个都不满足那innodb自己创建一个虚拟的聚集索引
建议使用int的auto_increment作为主键(按主键递增顺序插入)
聚集索引的二级索引叶子节点不会保存引用的行的物理位置,而是保存了行的主键值,减小了移动数据或者数据页面分裂时维护二级索引的开销
通过二级索引查询首先查到是主键值,然后再通过主键索引找到相应的数据块   
非聚集索引叶结点包含索引字段值及指向数据行的磁盘位置(逻辑指针),需通过磁盘位置访问磁盘数据,MyISAM二级索引叶结点和主键索引在存储结构上没有任何区别

覆盖索引(covering index)
一个查询语句只用从索引中就能够取得,避免了查到索引后再返回表操作,减少I/O提高效率,称之为索引覆盖
Explain的时候,输出的Extra信息中如果有Using Index,就表示这条查询使用了覆盖索引(Using Index Condition意思是使用了索引但需要回表查询)
InnoDB二级索引的叶子节点包含了主键值,所以查询字段包含主键时也可以覆盖查询

索引长度 & 索引选择性(Index Selectivity)
索引列中不同值的数量与表中记录数量的比叫索引的选择性,理想值是1,如果索引选择性过低,建议直接全表扫描而不是建立索引
对于字符型列,索引长度越大,区分度越高,但会占用更多的空间,因此需要在两者间做一个权衡
惯用手法:在字符列截取不同长度,测试其区分度,选择一个合适的索引长度
select count(distinct(left(word,4)))/count(*) from tb_name;
create index idx_word on tb_name(word(4));  -- 指定索引长度为4(如果字符集为utf8,key_len大概为4*3=12)
前缀索引兼顾索引大小和查询速度,但缺点是不能用于ORDER BY和GROUP BY操作,也不能用于Covering index

延迟索引关联(仅适用于Myisam)
我们尽量只查有索引的ID,速度非常快,然后再根据查出来的id进行join一次性取具体数据,这就是延迟索引
select * from cnarea order by id limit 700000,10;
可优化为
select cnarea.* from cnarea_2023 join (select id from cnarea limit 700000,10) x on cnarea.id=x.id;

行锁对提高并发帮助很大;事务对数据一致性帮助很大
t_user(uid PK, uname, age, sex) innodb;
update t_user set age=10 where uid=1;            -- 命中索引,行锁
update t_user set age=10 where uid != 1;         -- 未命中索引,表锁(负向查询无法命中索引)
update t_user set age=10 where name='shenjian';  -- 无索引,表锁
```

```
枚举核心id
数据库自增id不要用于业务暴漏给用户(比如用户可以猜昨天的订单量,也不利于分表)
mysql单机支撑到2000QPS容易报警,分库是提高并发
mysql可以读写分离
说明: 不建议使用text、blob这种可能特别大字段的数据类型,会影响表查询性能,一般用varchar(2000~4000),还是不够的话单独建表再用text/blob
互联网项目不要使用外键,可通过程序保证数据完整性
一般不需要给create_time索引,应为有自增id索引
ip建议用无符号整型(uint32)存储
utf8mb4是utf8的超集,有存储4字节例如表情符号时使用它

分表 & partition
数据量太大可考虑分表,例如根据用户id与10取模,将用户信息存储到不同的十张表里面
水平分表:把数据分到不同表
垂直分表:把热点字段和冷门字段分开
create table topic(
    tid int primary key auto_increment,  -- there can be only one auto column and it must be defined as a key
    update_time datetime not null default current_timestamp on update current_timestamp comment '消息更新时间', --如果update set没有更新数据时update_time不会被更新
    title char(20) not null default ''
)engine innodb charset utf8   # 不支持myisam
# partition by hash( tid ) partitions 4   # 只能用数字类型,根据tid%4分区(默认名字p0,p1,p2,p3),可通过explain查看查询需要的分区
partition by range(tid)(      # 还支持hash,list等分区
    partition t0 values less than(1000),
    partition t1 values less than(2000),
    partition t2 values less than(maxvalue)
)
ALTER TABLE topic REMOVE PARTITIONING;
ALTER TABLE topic partition by hash(tid) partitions 5;
                              
binlog
使用场景(binlog日志与数据库文件在同目录中)
1. MySQL主从复制: 在master开启binlog,master把它的二进制日志传递给slave来达到数据一致的目的
2. 使用mysqlbinlog工具恢复数据
show master logs;   # 查看所有binlog日志列表
show master status; # 查看最新一个binlog日志的名称及最后一个操作事件的Position
flush logs;         # 刷新日志,自此刻开始产生一个新的binlog日志文件(每当mysqld重启or在mysqldump备份数据时加-F选项都会执行该命令)
reset master;       # 清空所有binlog日志
show binlog events in '201810-08571-bin.000001' from pos limit m,n;  # 日志查询
mysqlbinlog binlog-file   // 查看binlog
mysqlbinlog --stop-position='120' binlog-file |mysql -uroot -p db_name   // 用binlog日志恢复数据,stop-position指定结束位置,-d指定只要某个数据库

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

联合索引
观察key_len和Extra,group by和order by都可以利用联合索引
最左匹配原则在遇到范围查询时,范围查询(>,<)右侧的列索引失效,可以改为>=,<=
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
        Extra: Using where    # 注意此处并没有Using filesort,也是利用索引的最左匹配原则
        
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

MySQL事务是基于UNDO/REDO日志
UNDO日志记录修改前状态,ROLLBACK基于UNDO日志实现; REDO日志记录修改后的状态,COMMIT基于REDO日志实现,执行COMMIT数据才会被写入磁盘
```


