import json
import logging
import os
import threading
import time
from multiprocessing.dummy import Process

import requests

from circuit_breaker import CircuitBreaker, Policy
from tutorial import singleton, get_ip


@singleton
class Apollo:
    """
    refer:
        https://www.apolloconfig.com/#/zh/README
        https://github.com/BruceWW/pyapollo/tree/master
    Namespace是配置项的集合,类似于一个配置文件的概念
    Apollo在创建项目的时候,都会默认创建一个application的Namespace
    Namespace的获取权限分为两种: private & public
    private权限的Namespace,只能被所属的应用获取到,一个应用尝试获取其它应用private的Namespace,Apollo会报404异常
    public权限的Namespace,能被任何应用获取,所以公共的Namespace的名称必须全局唯一
    """

    def __init__(self, app_id, cluster='default', server_url='http://localhost:8080', time_interval=5):
        self.server_url = server_url
        self.app_id = app_id
        self.cluster = cluster
        self.ip = get_ip()
        self._cache = {}
        self._notification_map = {'application': -1}  # -1保证初始化时从apollo拉取最新配置到内存,只有版本号比服务端小才认为是配置有更新
        self.time_interval = time_interval
        self.pid = 0
        self._check_pid()

    def _check_pid(self):
        if self.pid != os.getpid():
            with self._fork_lock:  # 极小概率出现死锁
                if self.pid != os.getpid():
                    self._reset()  # reset the instance for the new process if another thread hasn't already done so

    def _reset(self):
        thread = threading.Thread(target=self._listener, daemon=True)
        thread.start()
        self.pid = os.getpid()

    def get_value(self, key, default_val=None, namespace='application'):
        self._check_pid()
        try:
            return self._cache[namespace][key]  # 绝大多数情况key都存在,此种方式更快
        except KeyError:
            return default_val

    @CircuitBreaker(timeout=60, threshold=10, policy=Policy.COUNTER, fallback=None)
    def _long_poll(self, timeout=60):  # 更新self._cache和self._notification_map
        notifications = [{'namespaceName': k, 'notificationId': v} for k, v in self._notification_map.items()]
        """
        服务端针对传过来的每一个namespace和对应的notificationId,检查notificationId是否是最新的
        如果都是最新的,则保持住请求60秒,如果60秒内没有配置变化,则返回状态码304,如果60秒内有配置变化,则返回最新notificationId,状态码200
        如果传过来的notifications中发现有notificationId比服务端老,则直接返回最新notificationId,状态码200
        客户端判断状态码=304则不操作,200则针对变化的namespace用不带缓存的Http接口从服务端拉取最新配置
        由于服务端会hold住请求60秒,所以请确保客户端访问服务端的超时时间要大于60秒
        """
        r = requests.get(  # 服务端新增的,不在_notification_map内会被告知吗
            url='{}/notifications/v2'.format(self.server_url),
            params={
                'appId': self.app_id,
                'cluster': self.cluster,
                'notifications': json.dumps(notifications, ensure_ascii=False)
            },
            timeout=timeout,
        )
        if r.status_code == 304:
            logging.getLogger(__name__).debug('No change, timeout:{},notifications:{}'.format(timeout, notifications))
        elif r.status_code == 200:
            data = r.json()
            for entry in data:
                namespace = entry['namespaceName']
                notification_id = entry['notificationId']
                logging.getLogger(__name__).info("%s has changes: notificationId=%d", namespace, notification_id)
                self._notification_map[namespace] = notification_id  # 正常来说_notification_map和_cache的key是一一对应
                self._un_cached_http_get(namespace, timeout)
        else:
            logging.getLogger(__name__).debug(f'_long_poll error,status:{r.status_code},notifications:{notifications}')

    def _un_cached_http_get(self, namespace, timeout):
        # 不带缓存的Http接口从Apollo读取配置,如果需要配合配置推送通知实现实时更新配置的话需要调用该接口
        url = f'{self.server_url}/configs/{self.app_id}/{self.cluster}/{namespace}?ip={self.ip}'
        r = requests.get(url, timeout)
        if r.status_code == 200:
            data = r.json()
            self._cache[namespace] = data['configurations']  # dict,包含当前namespace下的所有key-value
        else:
            print('_un_cached_http_get error, status:{}, namespace:{}'.format(r.status_code, namespace))

    def _listener(self):
        while True:
            print('in _listener,pid:{}, time:{}'.format(os.getpid(), time.time()))
            self._long_poll()
            time.sleep(self.time_interval)

    def _cached_http_get(self, key, default_val, namespace, timeout):
        # 该接口会从缓存中获取配置,适合频率较高的配置拉取请求,如简单的每30秒轮询一次配置,缓存最多会有一秒的延时
        url = f'{self.server_url}/configfiles/json/{self.app_id}/{self.cluster}/{namespace}?ip={self.ip}'
        r = requests.get(url, timeout)
        if r.ok:  # ok?
            data = r.json()
            self._cache[namespace] = data
            logging.getLogger(__name__).info('Updated local cache for namespace %s', namespace)
        else:
            data = self._cache[namespace]
        return data.get(key, default_val)


class TestApollo:
    @staticmethod
    def test_concurrency():
        apollo = Apollo(app_id='ktv', server_url='http://10.16.4.194:8080')
        threads = [
            Process(target=lambda apl: print(apl.get_value('test', "default", namespace='config')), args=(apollo,))
            for _ in range(1000)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    @staticmethod
    def test_single():
        apollo = Apollo(app_id='ktv', server_url='http://10.16.4.194:8080')
        conf1 = apollo.get_value('test', 'bb', namespace='config')
        conf2 = apollo.get_value('switch', 'cc')  # apollo返回的数据类型都是str
        print(conf1, conf2, type(conf2))


if __name__ == '__main__':
    TestApollo.test_concurrency()
    # TestApollo.test_single()
