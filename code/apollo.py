import json
import logging
import os
import threading
import time
from multiprocessing.dummy import Process

import requests

from circuit_breaker import CircuitBreaker, Policy


class Apollo:  # 进程安全,单进程的读写问题待验证
    """
    refer:
        https://github.com/andymccurdy/redis-py/blob/master/redis/connection.py
        https://github.com/filamoon/pyapollo/blob/master/pyapollo/apollo_client.py
    Namespace是配置项的集合,类似于一个配置文件的概念
    Apollo在创建项目的时候,都会默认创建一个application的Namespace
    Namespace的获取权限分为两种: private & public
    private权限的Namespace,只能被所属的应用获取到,一个应用尝试获取其它应用private的Namespace,Apollo会报404异常
    public权限的Namespace,能被任何应用获取,所以公共的Namespace的名称必须全局唯一
    """

    def __init__(self, app_id, cluster='default', config_server_url='http://localhost:8080', timeout=35, ip=None):
        self.config_server_url = config_server_url
        self.app_id = app_id
        self.cluster = cluster
        self.timeout = timeout
        self.ip = ip or '127.0.0.1'
        self.reset()
        self._fork_lock = threading.Lock()

    def reset(self):
        self.lock = threading.Lock()
        self._cache = {}
        self._notification_map = {'application': -2}  # -2保证初始化时从apollo拉取最新配置到内存,只有版本号比服务端小才认为是配置有更新
        self.init_status = True
        self.pid = os.getpid()

    def _check_pid(self):
        if self.pid != os.getpid():
            with self._fork_lock:  # 极小概率出现死锁
                if self.pid != os.getpid():
                    self.reset()  # reset() the instance for the new process if another thread hasn't already done so

    def get_value(self, key, default_val=None, namespace='application', auto_fetch=False):
        self._check_pid()
        if self.init_status:
            with self.lock:
                if self.init_status:
                    self.init_status = False
                    t = threading.Thread(target=self._listener, daemon=True)
                    t.start()

        # 以下涉及到多线程同时操作self._cache,self._notification_map,可以考虑加线程锁
        if namespace not in self._notification_map:
            self._notification_map[namespace] = -2

        if namespace not in self._cache:
            logging.getLogger(__name__).info("Add namespace '%s' to local cache", namespace)
            # This is a new namespace, need to do a blocking fetch to populate the local cache
            self._long_poll(2)  # 防止阻塞主进程(还需要加个max_retry_times),用于更新self._cache和self._notification_map

        if key in self._cache[namespace]:  # key不存在怎么办
            return self._cache[namespace][key]
        else:
            if auto_fetch:
                return self._cached_http_get(key, default_val, namespace)
            else:
                return default_val

    @CircuitBreaker(timeout=60, threshold=10, policy=Policy.COUNTER, fallback=None)
    def _long_poll(self, timeout=None):
        timeout = timeout or self.timeout
        url = '{}/notifications/v2'.format(self.config_server_url)
        notifications = []
        for key in self._notification_map.keys():  # keys是防止遍历字典的时候结构被get_value变更
            notifications.append({'namespaceName': key, 'notificationId': self._notification_map[key]})
        r = requests.get(  # 如果检测到服务器的notificationId与本次提交一致,则最多等待30s,在这之间只要是服务器配置更新了,请求会立马返回
            url=url,
            params={'appId': self.app_id, 'cluster': self.cluster,
                    'notifications': json.dumps(notifications, ensure_ascii=False)},
            timeout=timeout
        )
        if r.status_code == 304:
            logging.getLogger(__name__).debug('No change, timeout:{},notifications:{}'.format(timeout, notifications))
        elif r.status_code == 200:
            data = r.json()
            for entry in data:
                ns = entry['namespaceName']
                nid = entry['notificationId']
                logging.getLogger(__name__).info("%s has changes: notificationId=%d", ns, nid)
                self._un_cached_http_get(ns)
                self._notification_map[ns] = nid
        else:
            logging.getLogger(__name__).debug(
                '_long_poll error, timeout:{}, status:{}, notifications:{}'.format(timeout, r.status_code,
                                                                                   notifications))
            time.sleep(timeout)

    # 该接口会从缓存中获取配置,适合频率较高的配置拉取请求,如简单的每30秒轮询一次配置,缓存最多会有一秒的延时
    # ip参数可选,应用部署的机器ip,用来实现灰度发布
    def _cached_http_get(self, key, default_val, namespace='application'):
        url = f'{self.config_server_url}/configfiles/json/{self.app_id}/{self.cluster}/{namespace}?ip={self.ip}'
        r = requests.get(url)
        if r.ok:  # ok?
            data = r.json()
            self._cache[namespace] = data
            logging.getLogger(__name__).info('Updated local cache for namespace %s', namespace)
        else:
            data = self._cache[namespace]  # 一定有吗
        return data.get(key, default_val)

    # 不带缓存的Http接口从Apollo读取配置,如果需要配合配置推送通知实现实时更新配置的话需要调用该接口
    def _un_cached_http_get(self, namespace='application'):
        url = '{}/configs/{}/{}/{}?ip={}'.format(self.config_server_url, self.app_id, self.cluster, namespace, self.ip)
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            self._cache[namespace] = data['configurations']  # dict,包含当前namespace下的所有key-value
        else:
            print('_un_cached_http_get error, status:{}, namespace:{}'.format(r.status_code, namespace))

    def _listener(self):
        while True:
            print('in _listener,pid:{}, time:{}'.format(os.getpid(), time.time()))
            self._long_poll()


class TestApollo:
    @staticmethod
    def test_concurrency():
        apollo = Apollo(app_id='ktv', config_server_url='http://10.16.4.194:8080')
        threads = [Process(target=lambda apl: print(apl.get_value('test', "", namespace='config')), args=(apollo,)) for
                   _ in range(1000)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    @staticmethod
    def test_single():
        apollo = Apollo(app_id='ktv', config_server_url='http://10.16.4.194:8080')
        conf1 = apollo.get_value('test', 'bb', namespace='config')
        conf2 = apollo.get_value('switch', '')  # apollo返回的数据类型都是str
        print(conf1, conf2, type(conf2))


if __name__ == '__main__':
    TestApollo.test_concurrency()
    # TestApollo.test_single()
