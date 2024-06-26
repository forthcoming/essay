from contextlib import contextmanager
from threading import get_ident

from sqlalchemy import Column, Integer, String
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool

# https://docs.sqlalchemy.org/en/14/tutorial/dbapi_transactions.html
'''
flask项目中db = SQLAlchemy(app),则db.engine相当于engine,db.session相当于session,如db.engine.pool.status()
pool_size和max_overflow会受到mysql配置文件: max_connections服务器最多可以建立的连接数(会保留一个root登陆的连接);max_user_connections同一个用户最多可建立的连接数影响
engine线程安全,但不是进程安全,连接池不应该在进程间传递,应为子进程中连接池会带有部分主进程的连接资源,子进程池新加入的连接资源不会影响到主进程,推荐做法是子进程重新申请engine或者子进程最开始处调用engine.dispose()释放连接池中的资源
惰性连接,并没有连接数据库,until the first time a method like Engine.execute() or Engine.connect() is called
the pool begins with no connections; once this number of connections is requested, that number of connections will remain.
The pool_pre_ping feature will normally emit SQL equivalent to “SELECT 1” each time a connection is checked out from the pool;
if an error is raised that is detected as a disconnect situation, the connection will be immediately recycled, and all other pooled connections older than the current time are invalidated.
'''
engine = create_engine(
    "mysql+pymysql://root:root@127.0.0.1:3306/test?charset=utf8mb4",
    echo=False,  # 是否记录日志,True我们会看到所有生成的SQL
    max_overflow=1,  # 超过连接池大小外最多创建的连接(即最大连接数=max_overflow+pool_size),对应QueuePool的max_overflow构造参数
    pool_timeout=30,
    # 对应QueuePool的timeout构造参数,Queue的self.get的超时时间,The number of seconds to wait before giving up on returning a connection.
    pool_size=3,
    # 连接池大小,对应QueuePool的pool_size构造参数,Queue的self.maxsize;With QueuePool, a pool_size setting of 0 indicates no limit; to disable pooling, set poolclass to NullPool instead.
    pool_recycle=4,
    # MySQL有关闭(连续wait_timeout时间内未操作过)闲置一段时间连接行为,默认8小时,为避免出现此问题,pool_recycle可确保在池中连续存在固定秒数的连接在下次取出时将被丢弃并替换为新的连接(惰性检测,将pool_recycle改小,pool_use_lifo=False,然后show processlist观察id很好验证)
    pool_pre_ping=True,
    poolclass=QueuePool,  # Disabling pooling using NullPool
    pool_use_lifo=False,
    # lifo mode allows excess connections to remain idle in the pool, allowing server-side timeout schemes to close these connections out.
    future=True,
)


def working_pool(index):
    with engine.connect() as conn:  # 每调用一次,按engine的连接池配置规则取出一条连接资源,块结束才会归还该资源,默认autocommit=True(每条语句都包含一个事务的开始与结束)
        # The connection is retrieved from the connection pool at the point at which Connection is created.
        # the context manager provided for a database connection and also framed the operation inside of a transaction
        # The default behavior of the Python DBAPI includes that a transaction is always in progress;
        # when the scope of the connection is released, a ROLLBACK is emitted to end the transaction. The transaction is not committed automatically;
        # when we want to commit data we normally need to call Connection.commit()
        # the Connection.close() method is automatically invoked at the end of the block,the referenced DBAPI connection is released to the connection pool.
        conn.execute(text("create table if not exists test(id int auto_increment primary key,name char(9));"))
        conn.execute(text("select sleep(1);"))
        conn.execute(text("insert into test(name) values('avatar');"))  # non-auto-committing,有操作(增删改查表数据等)之后数据库才会真正开启事物
        print('index: {}\t'.format(index), engine.pool.status())
        conn.commit()  # 即使退出语句快,也不会提交,需要手动调用,连接不会进连接池
        print('index: {}\t'.format(index), engine.pool.status())

        # when using textual SQL, a Python literal value, even non-strings like integers or dates, should never be stringified into SQL string directly;
        # a parameter should always be used. This is most famously known as how to avoid SQL injection attacks when the data is untrusted.
        # However it also allows the SQLAlchemy dialects and/or DBAPI to correctly handle the incoming input for the backend.
        result_cursor = conn.execute(text("select * from test where id>:id;"), {'id': 2})  # cursor对象
        # result_cursor=conn.execute(text(f"select * from test where id>{4};"))  # cursor对象,不推荐
        print(result_cursor.fetchone())  # 取出游标第一条数据
        for result in result_cursor:  # 遍历剩余游标,如果想多次使用结果,需要使用results=result_cursor.all(),此时游标再无数据
            print(result.id, result.name)  # 属性与表列名一致,否则会报错
        print(result_cursor.rowcount)  # 影响的数据行数,不会随遍历游标而改变,乐观锁会用到该属性


'''
The scoped_session.remove() method, as always, removes the current Session associated with the thread, if any.
However, one advantage of the threading.local() object is that if the application thread itself ends, the “storage” for that thread is also garbage collected.
So it is in fact “safe” to use thread local scope with an application that spawns and tears down threads, without the need to call scoped_session.remove(). 
However, the scope of transactions themselves, i.e. ending them via Session.commit() or Session.rollback(), will usually still be something that must be explicitly arranged for at the appropriate time, 
unless the application actually ties the lifespan of a thread to the lifespan of a transaction.    
'''
Session = sessionmaker(
    bind=engine,
    autocommit=False,  # default
    autoflush=True,
    # flush意思就是将当前session存在的变更发给数据库执行,如果想真正存在于数据库,还需要commit操作. When True, all query operations will issue a flush call to this Session before proceeding, session.execute查询不受此参数影响
    future=True,
)
# 线程安全的session,只需要全局定义一次,给出scopefunc则线程的session会存到一个名为register的字典中
session = scoped_session(Session, scopefunc=get_ident)

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    password = Column(String(12))


# Base.metadata.create_all(engine) # 在数据库建表


@contextmanager
def session_scope():
    print('session start')
    session = Session()  # 非线程安全,需要在每个线程中单独定义
    try:
        yield session  # If this session were created with autocommit=False, a new transaction is immediately begun.  Note that this new transaction does not use any connection resources until they are first needed.
        print('session commit')
        session.commit()  # 提交事务(更新到数据库),释放连接到连接池, If this session were created with autocommit=False, commit之后会立马开启一个新事务, but note that the newly begun transaction does *not* use any connection resources until the first SQL is actually emitted.
    except:
        print('session rollback')
        # session.invalidate() # 释放连接到连接池,但连接已与mysql断开(可通过show status like 'Threads%';的Threads_connected验证)
        session.rollback()  # 代码层事务回滚(数据库层事务会自动回滚),否则后续操作会报错,释放连接到连接池,Rollback the current transaction in progress.This method rolls back the current transaction or nested transaction regardless of subtransactions being in effect.
        raise
    finally:
        print('session close')
        session.close()  # 非必须(暂未发现必须使用的场景),释放连接到连接池,结束(非提交)当前事务,This clears all items and ends any transaction in progress.


def working_session(index):
    # with session_scope() as session: # 块语句正常结束,调用session.commit和session.close,异常结束调用session.rollback和session.close
    #     session.execute('truncate table test;')  # 第一次有数据库操作的时候,会从连接池取出一个连接or新建一个连接
    #     session.execute("insert into test values ({}, 3,1);".format(index))  # not autocommit,会开启事务
    #     print('index: {}\t'.format(index), engine.pool.status())
    #     session.execute("select sleep(10);")  # not autocommit

    try:
        user = User(id='qq', name=2, password='123456')
        # 调用session方法如add或者execute等操作之后才会针对当前线程产生一个属于自己的session,相当于调用session.registry.__call__返回当前线程的一个Session实例,再调用add或execute
        session.add(user)
        session.commit()
    except Exception as e:
        print(e)
        session.rollback()  # 必须
    user = User(id=index + 1, name='avatar', password='123456')
    session.add(user)  # 仅仅缓存到session,数据库方未做任何操作
    print(session.query(User).filter_by(
        id=index + 1).first())  # 产生事务,如果sessionmaker的autoflush=True,则会查到数据,当并未真正写到数据库(对其他事务仍不可见)
    # session.delete(user)  # 删除数据
    # session.flush()  # Regardless of the autoflush setting, a flush can always be forced by issuing flush()
    session.commit()  # 如果不及时归还连接到连接池,当牵出连接达最大值,则程序将被阻塞(池中无连接且无法申请新连接)
    session.remove()  # scoped_session尤其是自定义了scopefunc函数的dict型,一定要记得释放,应为每个新的线程都会新建一个session,可通过session.registry.registry查看


def main():
    working_pool(4)
    # threadings = [Process(target=working_session, args=(idx,)) for idx in range(7)]
    # for thread in threadings:
    #     thread.start()
    # for thread in threadings:
    #     thread.join()


if __name__ == '__main__':
    main()
