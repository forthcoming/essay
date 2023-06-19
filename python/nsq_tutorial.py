"""
消息队列用来快速消费队列中的消息,比如日志处理场景,我们需要把不同服务器上的日志合并到一起,这时就需要用到消息队列
任务队列(celery)是用来异步执行一个耗时任务,比如用户在购买的一件物品后,通常需要计算用户的积分以及等级,并把它们保存到数据库,这时就需要用到任务队列
利用消息队列的生长者和消费者的概念,也可以实现任务队列的功能,但是还需要进行额外的开发
任务队列新增了许多任务相关的定制,如重试,任务状态,结果返回,任务执行频率等等,但没有发布订阅的概念

A single nsqd can have many topics and each topic can have many channels,a channel can, and generally does, have multiple clients connected.
To summarize, messages are multicast from topic -> channel (every channel receives a copy of all messages for that topic).
but evenly distributed from channel -> consumers (each consumer or named client receives a portion of the messages for that channel).
当一个客户端以一个新的channel连接上topic时,该topic上的消息会发给客户端,不管之前是否有发给其他客户端
messages are not durable (by default)
--mem-queue-size number of messages to keep in memory (per topic/channel) (default 10000),can be set to 0 to ensure that all incoming messages are persisted to disk.
adjusts the number of messages queued in memory per topic/channel. Messages over that watermark are transparently written to disk, defined by --data-path.
messages received are un-ordered,You cannot rely on the order of messages being delivered to consumers.
启动命令
nsqlookupd
nsqd -lookupd-tcp-address=127.0.0.1:4160 -broadcast-address=127.0.0.1
nsqadmin -lookupd-http-address=127.0.0.1:4161
nsqadmin服务启动后,counter统计的是所有topic下所有channel消费的消息数
重启nsqd会使nsqadmin的counter重新计数,如果topic或channel被删除,相应的counter会减少
nsqd is the daemon that receives, queues, and delivers messages to clients.
nsqlookupd is the daemon that manages topology information and provides an eventually consistent discovery service.
nsqadmin is a web UI to introspect the cluster in realtime (and perform various administrative tasks).
nsq_tail -topic=test -channel=c0 -lookupd-http-address=127.0.0.1:4161
nsq_tail -topic=test -channel=c1 -lookupd-http-address=127.0.0.1:4161
nsq_tail -topic=test -channel=c1 -lookupd-http-address=127.0.0.1:4161
nsq_tail -topic=test -channel=c1 -lookupd-http-address=127.0.0.1:4161
Consumes the specified topic/channel and writes to stdout (in the spirit of tail(1))
相同的channel名会认为是同一个channel的多个consumers,消息会均匀分配到他们之中,但同一条消息会同时分发给c0和c1
nsq_to_http -topic=test -lookupd-http-address=127.0.0.1:4161 -get=http://localhost:8080/select?message=%s
Consumes the specified topic/channel and performs HTTP requests (GET/POST) to the specified endpoints.
创建一个名为nsq_to_http的channel,该命令成功的前提是有提供http://localhost:8080/select服务(可以用flask模拟)
nsq_to_file -topic=test -output-dir=/Users/zgt/Desktop/nsq -lookupd-http-address=127.0.0.1:4161
Consumes the specified topic/channel and writes out to a newline delimited file, optionally rolling and/or compressing the file.
创建一个名为nsq_to_file的channel
to_nsq -topic=test -nsqd-tcp-address=127.0.0.1:4150
Takes a stdin stream and splits on newlines (default) for re-publishing to destination nsqd via TCP.
to_nsq并不是一个channel,他只是往指定的topic上发送消息
"""

import requests

r = requests.get(url='http://127.0.0.1:4151/info')
print(
    r.text)  # {"version":"1.1.0","broadcast_address":"127.0.0.1","hostname":"201810-08571","http_port":4151,"tcp_port":4150,"start_time":1565926763}

'''
format - (optional) `text` or `json` (default = `text`)
topic - (optional) filter to topic
channel - (optional) filter to channel
'''
# r=requests.get(url='http://127.0.0.1:4151/stats?format=json&topic=test&channel=name')  
r = requests.get(url='http://127.0.0.1:4151/stats')
print(r.text)

'''
defer - the time in ms to delay message delivery (optional)
如果topic不存在则被创建,生产数据只能生产到topic
'''
r = requests.post(
    url='http://127.0.0.1:4151/pub?topic=test&defer=3000',
    data='你好'.encode('utf-8'),
    # json={'name':'伟大的QQ',score:10},
)
print(r.text)

# by default /mpub expects messages to be delimited by \n, 如果mpub改为pub,则data会认为是一条数据
r = requests.post(
    url='http://127.0.0.1:4151/mpub?topic=test',
    data='message\n中国\nmessage'.encode('utf-8'),
)
print(r.text)

requests.post('http://127.0.0.1:4151/topic/create?topic=T2')
requests.post('http://127.0.0.1:4151/topic/delete?topic=T1')
requests.post('http://127.0.0.1:4151/channel/create?topic=test&channel=name')
requests.post('http://127.0.0.1:4151/channel/delete?topic=test&channel=name')

# Empty all the queued messages (in-memory and disk) for an existing channel
r = requests.post('http://127.0.0.1:4151/channel/empty?topic=test&channel=nsq_to_file')
print(r.status_code)

# Empty all the queued messages (in-memory and disk) for an existing topic
r = requests.post('http://127.0.0.1:4151/topic/empty?topic=test')
print(r.status_code)

# Pause message flow to all channels on an existing topic (messages will queue at topic)
r = requests.post('http://127.0.0.1:4151/topic/pause?topic=test')
print(r.status_code)

# Resume message flow to channels of an existing, paused, topic
r = requests.post('http://127.0.0.1:4151/topic/unpause?topic=test')
print(r.status_code)

# Pause message flow to consumers of an existing channel (messages will queue at channel)
requests.post('http://127.0.0.1:4151/channel/pause?topic=name&channel=name')

# Resume message flow to consumers of an existing, paused, channel
requests.post('http://127.0.0.1:4151/channel/unpause?topic=name&channel=name')

############################################################################################################################


# Returns a list of producers for a topic
r = requests.get('http://127.0.0.1:4161/lookup?topic=test')
print(
    r.text)  # {"channels":["name","nsq_to_file"],"producers":[{"remote_address":"127.0.0.1:54246","hostname":"macbook.local","broadcast_address":"127.0.0.1","tcp_port":4150,"http_port":4151,"version":"1.1.0"}]}

# Returns a list of all known channels of a topic
r = requests.get('http://127.0.0.1:4161/channels?topic=test')
print(r.text)  # {"channels":["nsq_to_file","name"]}

# Returns a list of all known topics
r = requests.get('http://127.0.0.1:4161/topics')
print(r.text)  # {"topics":["T2","test"]}

# Returns a list of all known nsqd
r = requests.get('http://127.0.0.1:4161/nodes')
print(
    r.text)  # {"producers":[{"remote_address":"127.0.0.1:54246","hostname":"macbook.local","broadcast_address":"127.0.0.1","tcp_port":4150,"http_port":4151,"version":"1.1.0","tombstones":[false,false],"topics":["test","T2"]}]}

############################################################################################################################

import nsq

buf = []


def handler(message):  # 同步
    print(message.body)
    return True


def process_message(message):  # 异步
    global buf
    message.enable_async()
    buf.append(message)  # cache the message for later processing
    if len(buf) >= 3:
        for msg in buf:
            print(msg.body)
            msg.finish()
        buf = []
    else:
        print('deferring processing')


nsq.Reader(
    topic='one',
    channel='test',
    message_handler=handler,
    lookupd_http_addresses=['http://127.0.0.1:4161'],
    max_in_flight=9
)

nsq.Reader(
    topic='two',
    channel='another_test',
    message_handler=process_message,
    lookupd_http_addresses=['http://127.0.0.1:4161'],
    max_in_flight=9
)
nsq.run()
