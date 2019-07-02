###      文件夹名称是Tiktok      ###

### config.py
from celery.schedules import crontab
#Celery的配置, 修改配置需要重启celery 和 celery beat
# 消息代理器配置, redis 用例: redis://:password@hostname:port/db_number
broker_url = 'redis://localhost:6379/1'
# 结果储存
result_backend = 'redis://localhost:6379/2'

result_expires=2000

# 超时
broker_transport_options = {'visibility_timeout': 3600}  # 1 hour

# 序列形式
task_serializer = 'json'

enable_utc = True  # 默认为True,当前时间-8=utc时间

# 限制任务的频率,10/m代表这个任务在一分钟内最多只能有10个被执行
# task_annotations = {'celery.add': {'rate_limit': '10/m'}}

# 指定任务队列
# task_routes = {'celery.add': 'low-priority',}

# 定时任务文档 http://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html#crontab-schedules
# 使用前在 http://tool.lu/crontab/ 测试一遍

beat_schedule = {
    'test_celery_beat': {  # 测试celery 定时任务
        'task': 'Tiktok.celery.todo',
        #'schedule': crontab(hour=7, minute=30, day_of_week=1),  Executes every Monday morning at 7:30 a.m.
        'schedule': 10,
        'args': (3,5),
    },
}

#-----------------------------------------------------------------------------------------------------------------------------#

### celery.py
from celery import Celery
import time

app = Celery('task')
app.config_from_object('Tiktok.config')

@app.task(name='tobedone',ignore_result=False)
def todo(x,y):
    print(f'result: {x+y}')
    return x+y # return变量保存数据到redis

@app.task
def test(sec):
    time.sleep(sec)
    print(f'I have waited {sec} seconds')
    return sec

#-----------------------------------------------------------------------------------------------------------------------------#

### 开启服务
celery -A Tiktok worker -l info -B --logfile=/root/Desktop/Tiktok/%n.log    
# -B 开启定时任务,Please note that there must only be one instance of this service.
# -l 显示日志信息
# -c Number of child processes processing the queue. The default is the number of CPUs available on your system.

#-----------------------------------------------------------------------------------------------------------------------------#

### 调用
from Tiktok.celery import * 
result=test.delay(20)
# celery的broker,backend,task,调用task的项目,都可以在不同机器上
# result=app.send_task('tobedone',[3,4],{})  # 任务名错了不报错,字典传param=param型参数,适于远程调用
print(result.get(timeout=4))
print(result.id)
print(result.ready())  # returns whether the task has finished processing or not
# print(result.traceback)
