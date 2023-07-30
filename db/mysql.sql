sql执行顺序: from > where > group by > having > select > order by > limit

枚举核心id
数据库自增id不要用于业务暴漏给用户(比如用户可以猜昨天的订单量,也不利于分表)
mysql单机支撑到2000QPS容易报警,分库是提高并发
mysql可以读写分离

分表 & partition
数据量太大可考虑分表,例如根据用户id与10取模,将用户信息存储到不同的十张表里面
水平分表:把数据分到不同表
垂直分表:把热点字段和冷门字段分开
create table topic(
    tid int primary key auto_increment,
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

如何不锁表修改表结构
有专门工具,但原理一样,mysql新版本也不用锁表(5.6以后版本,待验证)
1. 表结构的修改在创建的一张新表中执行,这样不需要锁定原表了,也就不会影响mysql提供服务
2. 在原表中创建几个触发器针对uptate、delete 、insert操作都记录下来,方便更新到新建立的临时表中去
3. 对调表名并删除原表

processlist 
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

mysql不建议使用text blob类似这种数据类型
尽量不要使用 text 和 blob 这种可能特别大的字段,会影响表的查询性能,一般情况下用 varchar(2000~4000),还是不够的话一定要用text/blob,单独建表

基本数据类型
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
datetime     // YYYY-MM-DD HH:MM:SS 如:2010-03-14 19:26:32, The supported range is '1000-01-01 00:00:00' to '9999-12-31 23:59:59'.

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
SELECT SLEEP(100);  # 模拟耗时查询
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
select [distinct] * from [tname] where ... and ...; 
select count(1) from (select * from mysql.user) tt;                                                  // from子查询,临时表需要加别名
select * from article where (title,content,uid) = (select title,content,uid from blog where bid=2);  // where子查询
select * from article where (title,content,uid) in (select title,content,uid from blog);             // where子查询,第一处括号不能省
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
alter table t_name add (column_1,column_2);  // 同时新增多列
alter table t_name change 旧列名 新列名 列类型 列参数
rename table old_name to new_name;
(select aid,title from article limit 2) union all (select bid,title from blog limit 2);  //在UNION中如果对SELECT子句做限制,需要对SELECT添加圆括号,ORDER BY类似
# 创建一个从2019-02-22 16:30:00开始到10分钟后结束,每隔1分钟运行pro的事件
create event if not exists test on schedule every 1 minute starts '2019-02-22 16:30:00' ends '2019-02-22 16:30:00'+ interval 10 minute do call pro( );
互联网项目不要使用外键,可通过程序保证数据完整性
一般不需要给create_time索引,应为有自增id索引
ip建议用无符号整型(uint32)存储

# upsert,当唯一索引/主键索引冲突时会执行update操作,否则执行insert操作                                     
insert into test(_id, version, flag) values( 1, '1.0', 1 ) on duplicate key update version = '2.0',flag = 0; 
# 遇到duplicate约束时,ignore会直接跳过这条语句的插入
insert ignore into test(_id, version, flag) values( 1, '1.0', 1 ); 

                                        
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


