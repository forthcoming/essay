# PostgreSQL 笔记

---

# 1. PostgreSQL 基础

连接数据库：

```bash
psql -U postgres -h 192.168.1.245 -p 5432 test -W
```

查看所有数据库：

```sql
SELECT datname FROM pg_database;
```

查看当前数据库：

```sql
SELECT current_database();
```

---

# 2. 数据定义（DDL）

删除表：

```sql
DROP TABLE tablename;
```

创建表：

```sql
CREATE TABLE weather (
    city varchar(80),
    temp_lo int,
    prcp real,
    date date
);
```

## 常见数据类型

```
varchar(n) 最大长度限制。
text 无限长度字符串。
int 整数。
real 单精度浮点数。
numeric 精确数字，适合金额。
date 日期。
```

---

# 3. 索引

创建默认索引：

```sql
CREATE INDEX weather_index ON weather(city);
```

等价于：

```sql
CREATE INDEX weather_index ON weather USING BTREE(city);
```

说明： PostgreSQL 默认创建 B-tree 索引。

创建 Hash 索引：

```sql
CREATE INDEX weather_index ON weather USING HASH(city);
```

## PostgreSQL 支持的索引

- B-tree（默认）
- Hash
- GiST
- SP-GiST
- GIN
- BRIN
- bloom（扩展）

### B-tree

适用于：

```sql
=
<
<=
>
>=
BETWEEN
ORDER BY
```

是最常见的索引。

---

# 4. 约束

## PRIMARY KEY

```sql
product_no bigserial PRIMARY KEY
```

bigserial 是8字节自增长的整数  
特点：

- 自动创建唯一 B-tree 索引
- 自动添加 NOT NULL
- 一张表最多只能有一个主键

关系数据库理论上要求每张表都有主键。

---

## UNIQUE

```sql
name text UNIQUE
```

特点：

- 自动创建唯一 B-tree 索引
- 允许多个 NULL

---

## CHECK

```sql
CHECK(price > 0)
```

用于自定义数据校验规则。

---

## DEFAULT

```sql
DEFAULT 9.99
```

未提供值时自动填充。

---

## FOREIGN KEY

```sql
REFERENCES account(id)
```

注意：

外键约束只保证：

> 如果有值，则必须存在于被引用表中。

它本身不要求非空。

是否允许 NULL 由 NOT NULL 决定。

---

# 5. 数据操作（DML）

## INSERT

```sql
INSERT INTO weather VALUES ('San Francisco', 46, 0.25, '1994-11-27');
```

指定字段：

```sql
INSERT INTO weather(date, city) VALUES ('1994-11-29', 'Hayward');
```

---

## UPDATE

```sql
UPDATE weather SET temp_lo = temp_lo - 2 WHERE date > '1994-11-28';
```

---

## DELETE

```sql
DELETE FROM weather WHERE city = 'Hayward';
```

---

# 6. RETURNING

RETURNING 可以直接返回受影响的数据。

## INSERT

返回插入后的行。

```sql
INSERT ...
RETURNING *;
```

## UPDATE

返回修改后的新数据。

```sql
UPDATE products
SET price = price * 1.10
WHERE price <= 99.99
RETURNING name, price AS new_price;
```

## DELETE

返回被删除的数据。

```sql
DELETE ...
RETURNING *;
```

记忆：

| 操作 | RETURNING 返回 |
|--------|--------|
| INSERT | 新插入行 |
| UPDATE | 更新后的行 |
| DELETE | 删除前的行 |

---

# 7. 查询（DQL）

查询全部：

```sql
SELECT * FROM weather;
```

列别名：

```sql
SELECT city, temp_lo / 2 AS temp_avg, date FROM weather;
```

条件查询：

```sql
SELECT *
FROM weather
WHERE city = 'San Francisco'
AND prcp > 0.0
ORDER BY city, date;
```

去重：

```sql
SELECT DISTINCT city FROM weather;
```

---

# 8. 聚集函数

常见聚集函数：

```sql
count(*)
sum()
avg()
min()
max()
```

例如：

```sql
SELECT max(temp_lo) FROM weather;
```

## 聚集函数不能直接出现在 WHERE

错误：

```sql
SELECT *
FROM weather
WHERE max(temp_lo) > 10;
```

原因：

WHERE 执行时聚集结果尚未计算。

正确：

```sql
SELECT city
FROM weather
WHERE temp_lo =
(
    SELECT max(temp_lo)
    FROM weather
);
```

因为子查询会先完成聚集计算。

---

# 9. GROUP BY 与 HAVING

GROUP BY：

```sql
SELECT city,
       count(*),
       max(temp_lo)
FROM weather
GROUP BY city;
```

HAVING：

```sql
SELECT city,
       count(*),
       max(temp_lo)
FROM weather
GROUP BY city
HAVING max(temp_lo) < 40;
```

## SQL 执行顺序

```text
FROM
 ↓
WHERE
 ↓
GROUP BY
 ↓
HAVING
 ↓
SELECT
 ↓
ORDER BY
```

### WHERE

发生在聚集之前。

作用：

```text
过滤行
```

### HAVING

发生在聚集之后。

作用：

```text
过滤组
```

记忆口诀：

```text
WHERE 过滤行
HAVING 过滤组
```

---

# 10. 事务

PostgreSQL 实际上将每条 SQL 都作为事务执行。

例如：

```sql
SELECT * FROM weather;
```

逻辑上相当于：

```sql
BEGIN;

SELECT * FROM weather;

COMMIT;
```

如果没有显式 BEGIN，PostgreSQL 会自动开启并提交事务。

---

## 显式事务

```sql
BEGIN;

UPDATE account
SET balance = balance - 100
WHERE id = 1;

UPDATE account
SET balance = balance + 100
WHERE id = 2;

COMMIT;
```

回滚：

```sql
ROLLBACK;
```

BEGIN 与 COMMIT 包围的一组语句称为：

```text
Transaction Block
事务块
```

---

# 11. MVCC

MVCC：

```text
Multi-Version Concurrency Control
多版本并发控制
```

PostgreSQL 的核心并发机制。

特点：

- 读写几乎不互相阻塞
- 查询通常无需加读锁
- 基于快照可见性判断数据版本
- 高并发性能优秀

PostgreSQL 相比部分数据库更依赖 MVCC，而不是大量锁。

---

# 12. 并发问题

## 脏读

读取未提交数据。

## 不可重复读

同一事务读取同一行两次。

结果不同。

原因：

另一事务修改了该行。

## 幻读

两次执行相同条件查询。

返回记录数变化。

原因：

其他事务插入或删除了符合条件的数据。

## 序列化异常

假设：

```text
value = 10
```

事务A：

```text
读取10
value = value + 10
结果20
```

事务B：

```text
读取10
value = value * 2
结果20
```

并发执行结果：

```text
20
```

串行执行：

```text
A → B = 40
B → A = 30
```

都不等于 20。

说明并发结果不等价于任何串行顺序。

这就是：

```text
Serialization Anomaly
序列化异常
```

在 Serializable 隔离级别下，PostgreSQL 会检测这种冲突，并回滚其中一个事务。

---

# 13. 隔离级别

| 隔离级别 | 脏读 | 不可重复读 | 幻读 | 序列化异常 |
|----------|----------|----------|----------|----------|
| Read Committed | ❌ | ✅ | ✅ | ✅ |
| Repeatable Read | ❌ | ❌ | ❌* | ⚠️ |
| Serializable | ❌ | ❌ | ❌ | ❌ |

说明：

### Read Committed（默认）

防止脏读。

但可能出现：

- 不可重复读
- 幻读
- 序列化异常

### Repeatable Read

防止：

- 脏读
- 不可重复读

PostgreSQL 的实现基于 MVCC 快照。

虽然 SQL 标准允许幻读，

但 PostgreSQL 的 Repeatable Read 实际上也避免了传统意义上的幻读。

### Serializable

最严格。

保证结果等价于某种串行执行顺序。

---

# 14. 实际项目中的选择

银行系统：

```sql
SERIALIZABLE
```

原因：

一致性优先于性能。

互联网系统：

```sql
READ COMMITTED
```

原因：

高并发优先。

支付、库存扣减等场景通常结合：

- 乐观锁
- 悲观锁
- 分布式锁

而不是单纯提高隔离级别。

---

# 15. 字符串类型选择

## text

推荐。

```sql
name text
```

## varchar(n)

需要长度限制时使用。

```sql
name varchar(100)
```

## char(n)

固定长度。

```sql
name char(10)
```

实际会补空格。

容易产生问题。

通常不推荐。

---

## text 与 varchar(n)

在 PostgreSQL 中：

```text
text ≈ varchar(n)
```

性能与存储基本没有本质差异。

区别主要是：

```text
varchar(n)
有长度约束

text
无长度约束
```

推荐：

```text
需要长度限制 -> varchar(n)

不关心长度 -> text

尽量避免 char(n)
```

---

# 16. psql 元命令

查看所有表：

```sql
\dt+
```

查看表结构：

```sql
\d+ session_info
```

可查看：

- 字段
- 类型
- 默认值
- 索引
- 约束
- 存储信息
