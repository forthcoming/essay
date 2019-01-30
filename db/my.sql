有AA(id,sex,c1,c2),BB(id,age,c1,c2)两张表,其中A.id与B.id关联,现在要求写一条SQL语句,将B中age>50的记录的c1.c2更新到A表中统一记录中的c1.c2字段中.
AA:
create table AA(id int,sex char,c1 int,c2 int);
insert into AA values(1,'m',34,45),(2,'m',4,5),(3,'w',30,4),(4,'m',94,85);
BB:
create table BB(id int,age tinyint,c1 int,c2 int);
insert into BB values(1,59,45,46),(2,29,5,45),(4,56,46,23);

mysql> select * from AA;
+------+------+------+------+
| id   | sex  | c1   | c2   |
+------+------+------+------+
|    1 | m    |   34 |   45 |
|    2 | m    |    4 |    5 |
|    3 | w    |   30 |    4 |
|    4 | m    |   94 |   85 |
+------+------+------+------+
mysql> select * from BB;
+------+------+------+------+
| id   | age  | c1   | c2   |
+------+------+------+------+
|    1 |   59 |   45 |   46 |
|    2 |   29 |    5 |   45 |
|    4 |   56 |   46 |   23 |
+------+------+------+------+

mysql> update (AA join BB on AA.id=BB.id and BB.age>50) set AA.c1=BB.c1,AA.c2=BB.c2;
mysql> select * from AA;
+------+------+------+------+
| id   | sex  | c1   | c2   |
+------+------+------+------+
|    1 | m    |   45 |   46 |
|    2 | m    |    4 |    5 |
|    3 | w    |   30 |    4 |
|    4 | m    |   46 |   23 |
+------+------+------+------+

-------------------------------------------------------------------------------------------------------------------------------------

create table if not exists student (name char(4),class tinyint,score tinyint);
insert into student values('张三',1,54),('下贱',1,22),('王五',3,79),('赵六',3,54),('周扬',3,36),('路遥',2,4),('锚机吧',2,64),('胖三',2,34);
mysql> select * from student;
+--------+-------+-------+
| name   | class | score |
+--------+-------+-------+
| 张三   |     1 |    54 |
| 下贱   |     1 |    22 |
| 王五   |     3 |    79 |
| 赵六   |     3 |    54 |
| 周扬   |     3 |    36 |
| 路遥   |     2 |     4 |
| 锚机吧 |     2 |    64 |
| 胖三   |     2 |    34 |
+--------+-------+-------+

1) 选出每个班级中的学生,按照成绩降序排序
mysql> select * from student order by class,score desc;
+--------+-------+-------+
| name   | class | score |
+--------+-------+-------+
| 张三   |     1 |    54 |
| 下贱   |     1 |    22 |
| 锚机吧 |     2 |    64 |
| 胖三   |     2 |    34 |
| 路遥   |     2 |     4 |
| 王五   |     3 |    79 |
| 赵六   |     3 |    54 |
| 周扬   |     3 |    36 |
+--------+-------+-------+

2) 查出每个班的不及格数和及格数
mysql> select class,sum(score<60) 不及格数,sum(score>=60) 及格数 from student group by class;
+-------+----------+--------+
| class | 不及格数 | 及格数 |
+-------+----------+--------+
|     1 |        2 |      0 |
|     2 |        2 |      1 |
|     3 |        2 |      1 |
+-------+----------+--------+

3) 查出每个班分数最高的学生信息
mysql> select * from student t where score=(select max(score) from student where t.class=student.class);  #注意理解,score=54只会筛选到class=1不会筛选到class=3
mysql> select * from student t where not exists (select 1 from student where t.class=student.class and t.score<student.score);
mysql> select student.* from student join (select class,max(score) max_score from student group by class) t on student.class=t.class and student.score=t.max_score;
+--------+-------+-------+
| name   | class | score |
+--------+-------+-------+
| 张三   |     1 |    54 |
| 王五   |     3 |    79 |
| 锚机吧 |     2 |    64 |
+--------+-------+-------+

4) 查出每个班分数低于该班平均分的学生信息(类似于3的查询)
mysql> select * from student t where score<(select avg(score) from student where t.class=student.class);
+------+-------+-------+
| name | class | score |
+------+-------+-------+
| 下贱 |     1 |    22 |
| 赵六 |     3 |    54 |
| 周扬 |     3 |    36 |
| 路遥 |     2 |     4 |
+------+-------+-------+
Oracle实现如下：
with tmp as (select avg(score) avg_score,class from student group by class) select student.* from student join tmp on student.class=tmp.class and student.score<tmp.avg_score;
with tmp as (select student.*, avg(score) over(partition by class) avg_score from student) select * from tmp where score<avg_score;

5) 查出每个班分数最高的前两名学生信息
mysql> select a.*,count(1) num from student a join student b on a.class=b.class and a.score<=b.score group by a.class,a.score having num<=2;
+--------+-------+-------+----------+
| name   | class | score | count(1) |
+--------+-------+-------+----------+
| 下贱   |     1 |    22 |        2 |
| 张三   |     1 |    54 |        1 |
| 胖三   |     2 |    34 |        2 |
| 锚机吧 |     2 |    64 |        1 |
| 赵六   |     3 |    54 |        2 |
| 王五   |     3 |    79 |        1 |
+--------+-------+-------+----------

-------------------------------------------------------------------------------------------------------------------------------------

取出同一个户编号但户口所在地不在同一个地方的数据
eg:
户编号0001,共计三个,户口所在地分别为云南省,贵州,则取出
户编号0002,共计三人,户口所在地都是云南省,则不用取出
DROP TABLE IF EXISTS `population`;
CREATE TABLE `population` (
  `id` tinyint(4) unsigned PRIMARY KEY AUTO_INCREMENT,
  `num` varchar(10),
  `nickname` varchar(10),
  `name` varchar(10),
  `addr` varchar(10)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8;

INSERT INTO population VALUES ('1', '0001', '户主', '李小龙', '云南省');
INSERT INTO population VALUES ('2', '0001', '妻子', '张仙花', '云南省');
INSERT INTO population VALUES ('3', '0001', '长子', '李青', '贵州');
INSERT INTO population VALUES ('4', '0002', '户主', '赵明', '云南省');
INSERT INTO population VALUES ('5', '0002', '妻子', '张兰', '云南省');
INSERT INTO population VALUES ('6', '0002', '长子', '赵阳', '云南省');
INSERT INTO population VALUES ('7', '0003', '户主', '钱老大', '云南省');
INSERT INTO population VALUES ('8', '0003', '妻子', '金玉', '云南省');
INSERT INTO population VALUES ('9', '0004', '户主', '许仙', '浙江省');
INSERT INTO population VALUES ('10', '0004', '妻子', '白素贞', '广东省');
INSERT INTO population VALUES ('11', '0004', '长女', '许珍珍', '浙江省');
INSERT INTO population VALUES ('12', '0004', '长子', '许士林', '浙江省');
INSERT INTO population VALUES ('13', '0004', '次女', '许美美', '浙江省');
INSERT INTO population VALUES ('14', '0009', '户主', '黄飞鸿', '湖南省');
INSERT INTO population VALUES ('15', '0009', '妻子', '十三姨', '广东省');

mysql> select * from population;
+----+------+----------+--------+--------+
| id | num  | nickname | name   | addr   |
+----+------+----------+--------+--------+
|  1 | 0001 | 户主     | 李小龙 | 云南省 |
|  2 | 0001 | 妻子     | 张仙花 | 云南省 |
|  3 | 0001 | 长子     | 李青   | 贵州   |
|  4 | 0002 | 户主     | 赵明   | 云南省 |
|  5 | 0002 | 妻子     | 张兰   | 云南省 |
|  6 | 0002 | 长子     | 赵阳   | 云南省 |
|  7 | 0003 | 户主     | 钱老大 | 云南省 |
|  8 | 0003 | 妻子     | 金玉   | 云南省 |
|  9 | 0004 | 户主     | 许仙   | 浙江省 |
| 10 | 0004 | 妻子     | 白素贞 | 广东省 |
| 11 | 0004 | 长女     | 许珍珍 | 浙江省 |
| 12 | 0004 | 长子     | 许士林 | 浙江省 |
| 13 | 0004 | 次女     | 许美美 | 浙江省 |
| 14 | 0009 | 户主     | 黄飞鸿 | 湖南省 |
| 15 | 0009 | 妻子     | 十三姨 | 广东省 |
+----+------+----------+--------+--------+

-------------------------------------------------------------------------------------------------------------------------------------

查询每个员工姓名及员工的上级姓名(自连接)
create table emp(empno number(4),ename varchar2(10),mgr number(4));
insert into emp values(7369,'smith',7902);
insert into emp values(7499,'allen',7698);
insert into emp values(7521,'ward',7698);
insert into emp values(7566,'jones',7839);
insert into emp values(7654,'martin',7698);
insert into emp values(7698,'blake',7839);
insert into emp values(7782,'clark',7839);
insert into emp values(7788,'scott',7566);
insert into emp values(7839,'king',null);
insert into emp values(7844,'turner',7698);
insert into emp values(7876,'adams',7788);
insert into emp values(7900,'james',7698);
insert into emp values(7902,'ford',7566);
insert into emp values(7934,'miller',7782);
insert into emp values(9999,'shunping',7782);
update emp set ename=upper(substr(ename,1,1))||lower(substr(ename,2,length(ename)-1));
update emp set ename=initcap(ename);    --等价与上一条语句
SQL> select * from emp;
     EMPNO ENAME             MGR
---------- ---------- ----------
      7369 Smith            7902
      7499 Allen            7698
      7521 Ward             7698
      7566 Jones            7839
      7654 Martin           7698
      7698 Blake            7839
      7782 Clark            7839
      7788 Scott            7566
      7839 King
      7844 Turner           7698
      7876 Adams            7788
      7900 James            7698
      7902 Ford             7566
      7934 Miller           7782
      9999 Shunping         7782

Answer:(这里的where不能用and和having代替,但是在MySQL中可以用having代替)
SQL> select worker.ename,boss.ename from emp worker left join emp boss on worker.mgr=boss.empno  where worker.ename='ford';
ENAME      ENAME
---------- ----------
Ford       Jones

-------------------------------------------------------------------------------------------------------------------------------------

删除重复行
create table tb_test(name varchar2(10),age number(3));
insert into tb_test values('张三',29);
insert into tb_test values('李四',29);
insert into tb_test values('张三',40);
insert into tb_test values('李四',29);
insert into tb_test values('张三',29);
SQL> select * from tb_test;
NAME              AGE
---------- ----------
张三               29
李四               29
张三               40
李四               29
张三               29

方法一:
delete from tb_test where rowid in (select distinct a.rowid from tb_test a join tb_test b on a.name=b.name and a.age=b.age where a.rowid>b.rowid);
方法二:
delete from tb_test a where rowid not in (select max(b.rowid) from tb_test b where a.name=b.name and a.age=b.age);
方法三:
create table tb_tmp as select distinct name,age from tb_test;
truncate table tb_test;
insert into tb_test select * from tb_tmp;

-------------------------------------------------------------------------------------------------------------------------------------

删除108号员工所在部门中工资最低的那个员工
1). 查询 108 员工所在的部门 id
select department_id from employees  where employee_id = 108;

2). 查询 1) 部门中的最低工资:
select min(salary) from employees where department_id =
(
     select department_id
     from employees
     where employee_id = 108
)

3). 删除 1) 部门中工资为 2) 的员工信息:
delete from employees e
     where department_id =
     (
          select department_id
          from employees e
          where employee_id = 108
     )
     and salary =
     (
          select min(salary)
          from employees
          where department_id = e.department_id
     );

-------------------------------------------------------------------------------------------------------------------------------------

更改108员工的信息:使其工资变为所在部门中的最高工资,job变为公司中平均工资最低的job
1). 搭建骨架
update employees set salary = (), job_id = () where employee_id = 108;

2). 所在部门中的最高工资  
select max(salary) from employees where department_id =
(
     select department_id
     from employees
     where employee_id = 108
)

3). 公司中平均工资最低的job
select job_id from employees group by job_id having avg(salary) =
(
     select min(avg(salary))
     from employees
     group by job_id
)

4). 填充
update employees e set salary = (
     select max(salary)
     from employees
     where department_id = e.department_id
), job_id = (
     select job_id
     from employees
     group by job_id
     having avg(salary) =  (
          select min(avg(salary))
          from employees
          group by job_id
     )
) where employee_id = 108;

-------------------------------------------------------------------------------------------------------------------------------------

在emp表中按部门分组,取出每个部门工资最高的前两名
with tmp as (select emp.*,row_number() over(partition by department_id order by salary desc) RANK from emp)
select * from tmp where RANK < 3;

-------------------------------------------------------------------------------------------------------------------------------------

造数
drop procedure if exists item;
create procedure item()
begin
  declare i int default 0;
  while i < 10 do
    insert into test values(concat('项目1-栏目1-测试',i),concat('项目1-栏目2-测试',i));
    set i = i + 1;
  end while;
end
call item();

-------------------------------------------------------------------------------------------------------------------------------------

行列互换
create table t1(
    num int,
    subject varchar(10),
    grade int 
);

insert into t1 values(1,'语文',80);
insert into t1 values(1,'数学',82);
insert into t1 values(1,'英语',84);
insert into t1 values(2,'语文',70);
insert into t1 values(2,'数学',74);
insert into t1 values(2,'英语',76);
insert into t1 values(3,'语文',90);
insert into t1 values(3,'数学',93);
insert into t1 values(3,'英语',94);

select
     num,
     sum(decode(subject , '语文', grade)) '语文',
     sum(case subject
          when '数学' then grade
         end
        ) '数学',
     sum(case
           when subject = '英语' then grade
         end
        ) '英语'
from t1 group by num;

num   语    数    英
1    80    82    84
2    70    74    76
3    90    93    94

-------------------------------------------------------------------------------------------------------------------------------------

分析函数之rank
Rank,ense_rank,ow_number函数为每条记录产生一个从1开始至N的自然数,的值可能小于等于记录的总数
Row_number返回一个唯一的值,碰到相同数据时,名按照记录集中记录的顺序依次递增
Dense_rank返回一个唯一的值,碰到相同数据时,时所有相同数据的排名都是一样的 
Rank返回一个唯一的值,到相同的数据时,时所有相同数据的排名是一样的,时会在最后一条相同记录和下一条不同记录的排名之间空出排名
空值null在排序时默认无限大,决办法是在order by加上nulls last

create sequence sq_test;
create table test(id number primary key,name varchar2(10),sal number);
insert into test values(sq_test.nextval,'Jone',1000);
insert into test values(sq_test.nextval,'Jone',100);
insert into test values(sq_test.nextval,'Avatar',1000);
insert into test values(sq_test.nextval,'Edison',null);
insert into test values(sq_test.nextval,'Joker',1500);
select id,name,sal,
rank() over(order by name desc) RANK1,
rank() over(partition by name order by sal desc) RANK2,
rank() over(order by sal desc nulls last) RANK3,
dense_rank() over(order by sal desc nulls last) DENSE_RANK,
row_number() over(order by sal desc nulls last) ROW_NUMBER,
sum(sal) over(order by sal desc nulls last) SUM
from test;

-------------------------------------------------------------------------------------------------------------------------------------

按"火箭   2:0    红牛  2006-06-11"样式打印比赛结果
create table m(
    id int,
    zid int,
    kid int,
    res varchar(10),
    mtime date
) charset utf8;
insert into m values(1,1,2,'2:0','2006-05-21'),(2,3,2,'2:1','2006-06-21'),(3,1,3,'2:2','2006-06-11'),(4,2,1,'2:4','2006-07-01');
create table t(
    tid int,
    tname varchar(10)
) charset utf8;
insert into t values(1,'申花'),(2,'红牛'),(3,'火箭');

mysql> select * from m;
+------+------+------+------+------------+
| id   | zid  | kid  | res  | mtime      |
+------+------+------+------+------------+
|    1 |    1 |    2 | 2:0  | 2006-05-21 |
|    2 |    3 |    2 | 2:1  | 2006-06-21 |
|    3 |    1 |    3 | 2:2  | 2006-06-11 |
|    4 |    2 |    1 | 2:4  | 2006-07-01 |
+------+------+------+------+------------+

mysql> select * from t;
+------+-------+
| tid  | tname |
+------+-------+
|    1 | 申花  |
|    2 | 红牛  |
|    3 | 火箭  |
+------+-------+

mysql> select t.tname,m.res,t1.tname,m.mtime from m join t on m.zid=t.tid join t t1 on m.kid=t1.tid;
+-------+------+-------+------------+
| tname | res  | tname | mtime      |
+-------+------+-------+------------+
| 红牛  | 2:4  | 申花  | 2006-07-01 |
| 申花  | 2:0  | 红牛  | 2006-05-21 |
| 火箭  | 2:1  | 红牛  | 2006-06-21 |
| 申花  | 2:2  | 火箭  | 2006-06-11 |
+-------+------+-------+------------+

-------------------------------------------------------------------------------------------------------------------------------------

树状数据结构如何建表
create table tree(
    id int(10) not null auto_increment,
    name varchar(32) not null default '',
    url varchar(100) not null default '',
    level tinyint(1) not null default 0, 
    -- scene_id bit(20) not null comment '情景值ID,前8位是appId',  
    parent_id int(10) not null default 0 comment '指向父id',
    created_time datetime not null,
    updated_time timestamp not null default current_timestamp on update current_timestamp,
    primary key(id)
) engine = innodb auto_increment = 1 default charset = utf8mb4 comment = '商品品类目录表';
