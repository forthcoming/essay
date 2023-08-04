import time
from datetime import datetime

import pymysql

slave = pymysql.connect(  # 正式环境
    host='10.1.175.132',
    db='room',
    port=3306,
    user='ktv',
    charset='utf8',
    passwd='D'
)

master = pymysql.connect(  # 正式环境
    host='10.1.208.25',
    db='room',
    port=3306,
    user='ktv',
    passwd='D'
)


# 10月以后的红包数据未同步

def sync(db, month):
    cur = db.cursor(pymysql.cursors.DictCursor)
    data = {}
    for day in ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17',
                '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31']:
        sql = "select user_id,money from ktv_small_red_pack_2019{0} where created_at>='2019-{0}-{1} 00:00:00' and created_at<'2019-{0}-{1} 23:59:59';".format(
            month, day)
        print(sql)
        cur.execute(sql)
        for item in cur:
            user_id = item['user_id']
            if user_id in data:
                data[user_id] += item['money']
            else:
                data[user_id] = item['money']
    cur.close()
    return data


def insert(db, data):
    now = datetime.now()
    cur = db.cursor(pymysql.cursors.DictCursor)
    for idx, user_id in enumerate(data, 1):
        sql = "insert into ktv_grab_coins(user_id,amount,month,create_time) values({},{},'2019-{}-01','{}')".format(
            user_id, data[user_id], month, now)
        cur.execute(sql)
        print(sql)
        if idx % 1000 == 0:
            db.commit()
    db.commit()
    cur.close()


def sync_10(source,
            target):  # 同步当月(10月)的红包数据
    cur = source.cursor(pymysql.cursors.DictCursor)
    data = {}
    for day in ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17',
                '18', '19', '20', '21', '22', '23', '24']:
        sql = "select user_id,money from ktv_small_red_pack where created_at>='2019-10-{0} 00:00:00' and created_at<'2019-10-{0} 23:59:59';".format(
            day)
        print(sql)
        cur.execute(sql)
        for item in cur:
            user_id = item['user_id']
            if user_id in data:
                data[user_id] += item['money']
            else:
                data[user_id] = item['money']
    cur.close()

    now = datetime.now()
    cur = target.cursor(pymysql.cursors.DictCursor)
    for idx, user_id in enumerate(data, 1):
        sql = "insert into ktv_grab_coins(user_id,amount,month,create_time) values({},{},'2019-10-01','{}')".format(
            user_id, data[user_id], now)
        cur.execute(sql)
        print(sql)
        if idx % 1000 == 0:
            target.commit()
    target.commit()
    cur.close()


if __name__ == '__main__':
    for month in ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10']:
        data = sync(slave, month)
        insert(master, data)
        time.sleep(1.5)

        # sync_10(slave,master)

# from sqlalchemy import create_engine
# from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
# from sqlalchemy.pool import NullPool
# from multiprocessing import JoinableQueue, cpu_count
# from multiprocessing.dummy import Process
# import time
#
# engine = create_engine(
#     'mysql+pymysql://root:root@localhost:3306/test?charset=utf8mb4',
#     echo=False,
#     max_overflow=0,
#     pool_timeout=10,
#     pool_size=10,
#     pool_recycle=600,
#     # poolclass = NullPool,  # Disabling pooling using NullPool
# )
# task_queue = JoinableQueue()
#
#
# def scheduler():  # 注意不要使用成员函数(成员函数序列化会有问题)
#     for idx in range(2):
#         process = Process(target=consumer)
#         process.daemon = True
#         process.start()
#
#     sql = '''
#         select sleep(2);
#     '''
#     engine.execute(sql)
#     print(engine.pool.status())
#     with ProcessPoolExecutor(cpu_count()) as executor:  # 整个with代码块会被阻塞,直至进程池完成任务(submit非阻塞)
#         for item in range(10):
#             executor.submit(producer, item)
#     task_queue.join()
#
# def producer(item):
#     task_queue.put(item)
#
#
# def consumer():
#     try:  # avoid defunct process
#         while True:
#             time.sleep(3)
#             print("in",engine.pool.status())
#             task = task_queue.get()  # 默认block=True, timeout=None
#             print(task)
#             task_queue.task_done()
#     except Exception as e:
#         print('error found in,error:{}'.format(e))
#
#
# if __name__ == '__main__':
#     scheduler()


# from sqlalchemy import create_engine
# from sqlalchemy.pool import QueuePool,NullPool
# import time,json
# import requests
#
# requests.get('qqqq')
#
# engine = create_engine('mysql+pymysql://root:root@localhost:3306/test?charset=utf8mb4',
#     max_overflow=1,
#     pool_timeout=30,
#     pool_size=3,
# #     poolclass=NullPool,  # Disabling pooling using NullPool
# )
#
#
# def working_engine(engine):
#     connection = engine.connect()
#     trans = connection.begin()
#     connection.execute("select * from child;")  #
#     trans.commit()
#
# def working_engine1(engine):
#     connection = engine.connect()  # autocommit=False
#     transaction = connection.begin()
#     sql = 'insert into child values(5)'
#     connection.execute(sql)  # not autocommit,有操作(增删改查等)之后数据库才会真正开启事物
#     transaction.commit()
#     transaction = connection.begin()
#     transaction.commit()
#
#
# def main():
#     working_engine1(engine)
#
#
#
# if __name__=='__main__':
#
#     main()


# c1
MYSQL = {
    'host': '10.17.4.61',
    'db': 'db_sing_ktv',
    'port': 3306,
    'user': 'u_sing_ktv',
    'charset': 'utf8',
    'passwd': 'fc72f20306b77d09',
}

con = pymysql.connect(**MYSQL)

# with con.cursor() as cur:
#     try:
#         sql = 'INSERT INTO target(`statistics_id`, `type`, `date_str`, `amount`) VALUES(2, 2, "2019112511",40000) ON DUPLICATE KEY UPDATE `amount` = `amount` + 30000;'
#         cur.execute(sql)
#         print(sql)
#         sql = 'INSERT INTO target(`statistics_id`, `type`, `date_str`, `amount`) VALUES(3, 3, "2019112511",40000) ON DUPLICATE KEY UPDATE `amount` = `amount` + 30000;'
#         cur.execute(sql)
#         print(sql)
#         con.commit()
#         sql = 'INSERT INTO target(`statistics_id`, `type`, `date_str`, `amount`) VALUES(0, 0, "2019112511",40000) ON DUPLICATE KEY UPDATE `amount` = `amount` + 30000;'
#         cur.execute(sql)
#         print(sql)
#         sql='select sleep(10);'
#         cur.execute(sql)
#         print(sql)
#         print(3333333333)
#         # con.commit()
#     except pymysql.err.OperationalError as e:
#         print(e)

# c2
MYSQL = {
    'host': '10.17.4.61',
    'db': 'db_sing_ktv',
    'port': 3306,
    'user': 'u_sing_ktv',
    'charset': 'utf8',
    'passwd': 'fc72f20306b77d09',
}

con = pymysql.connect(**MYSQL)

with con.cursor() as cur:
    sql = 'INSERT INTO target(`statistics_id`, `type`, `date_str`, `amount`) VALUES(0, 0, "2019112511",40000) ON DUPLICATE KEY UPDATE `amount` = `amount` + 10000;'
    cur.execute(sql)
    print(sql)
    sql = 'select sleep(5);'
    cur.execute(sql)
    print(sql)
    sql = 'INSERT INTO target(`statistics_id`, `type`, `date_str`, `amount`) VALUES(0, 0, "2019112511",40000) ON DUPLICATE KEY UPDATE `amount` = `amount` + 20000;'
    cur.execute(sql)
    print(sql)
    con.commit()
