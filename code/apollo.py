import json
import logging
import os
import threading
import time

import requests

from circuit_breaker import CircuitBreaker, Policy


class Apollo:  # 进程安全
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
        self.appId = app_id
        self.cluster = cluster
        self.timeout = timeout
        self.ip = ip or '127.0.0.1'
        self.reset()

        # this lock is acquired when the process id changes, such as after a fork. during this time, multiple threads in the child process could attempt to acquire this lock.
        # the first thread to acquire the lock will reset the data structures and lock object of this pool.
        # subsequent threads acquiring this lock will notice the first thread already did the work and simply release the lock.
        self._fork_lock = threading.Lock()

    def reset(self):
        self.lock = threading.Lock()
        self._cache = {}
        self._notification_map = {'application': -2}  # -2保证初始化时从apollo拉取最新配置到内存,只有版本号比服务端小才认为是配置有更新
        self.init_status = True

        # this must be the last operation in this method. while reset() is called when holding _fork_lock,
        # other threads in this process can call _checkpid() which compares self.pid and os.getpid() without holding any lock (for performance reasons).
        # keeping this assignment as the last operation ensures that those other threads will also notice a pid difference and block waiting for the first thread to release _fork_lock.
        # when each of these threads eventually acquire _fork_lock, they will notice that another thread already called reset() and they will immediately release _fork_lock and continue on.
        self.pid = os.getpid()

    def _checkpid(self):
        # _checkpid() attempts to keep ConnectionPool fork-safe on modern systems. this is called by all ConnectionPool methods that manipulate the pool's state such as get_connection() and release().
        # when the process ids differ, _checkpid() assumes that the process has forked and that we're now running in the child process. the child process cannot use the parent's file descriptors (e.g., sockets).
        # therefore, when _checkpid() sees the process id change, it calls reset() in order to reinitialize the child's ConnectionPool. this will cause the child to make all new connection objects.
        # _checkpid() is protected by self._fork_lock to ensure that multiple threads in the child process do not call reset() multiple times.
        # there is an extremely small chance this could fail in the following scenario:
        #   1. process A calls _checkpid() for the first time and acquires self._fork_lock.
        #   2. while holding self._fork_lock, process A forks (the fork() could happen in a different thread owned by process A)
        #   3. process B (the forked child process) inherits the ConnectionPool's state from the parent. that state includes a locked _fork_lock.
        #      process B will not be notified when process A releases the _fork_lock and will thus never be able to acquire the _fork_lock.
        if self.pid != os.getpid():
            with self._fork_lock:  # 极小概率出现死锁
                if self.pid != os.getpid():
                    self.reset()  # reset() the instance for the new process if another thread hasn't already done so

    def get_value(self, key, default_val=None, namespace='application', auto_fetch_on_cache_miss=False):
        self._checkpid()
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
            self._long_poll(2)  # 防止阻塞主进程,用于更新self._cache和self._notification_map

        if key in self._cache[namespace]:
            return self._cache[namespace][key]
        else:
            if auto_fetch_on_cache_miss:
                return self._cached_http_get(key, default_val, namespace)
            else:
                return default_val

    @CircuitBreaker(timeout=60, threshold=10, policy=Policy.COUNTER, fallback=None)
    def _long_poll(self, timeout=None):
        timeout = timeout or self.timeout
        url = '{}/notifications/v2'.format(self.config_server_url)
        notifications = []
        for key in list(self._notification_map.keys()):  # 加list是为了兼容py3,keys是防止遍历字典的时候结构被get_value变更
            notifications.append({'namespaceName': key, 'notificationId': self._notification_map[key]})
        r = requests.get(  # 如果检测到服务器的notificationId与本次提交一致,则最多等待30s,在这之间只要是服务器配置更新了,请求会立马返回
            url=url,
            params={'appId': self.appId, 'cluster': self.cluster,
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
                self._uncached_http_get(ns)
                self._notification_map[ns] = nid
        else:
            logging.getLogger(__name__).debug(
                '_long_poll error, timeout:{}, status:{}, notifications:{}'.format(timeout, r.status_code,
                                                                                   notifications))
            time.sleep(timeout)

    # 该接口会从缓存中获取配置,适合频率较高的配置拉取请求,如简单的每30秒轮询一次配置,缓存最多会有一秒的延时
    # ip参数可选,应用部署的机器ip,用来实现灰度发布
    def _cached_http_get(self, key, default_val, namespace='application'):
        url = '{}/configfiles/json/{}/{}/{}?ip={}'.format(self.config_server_url, self.appId, self.cluster, namespace,
                                                          self.ip)
        r = requests.get(url)
        if r.ok:  # ok?
            data = r.json()
            self._cache[namespace] = data
            logging.getLogger(__name__).info('Updated local cache for namespace %s', namespace)
        else:
            data = self._cache[namespace]
        return data.get(key, default_val)

    # 不带缓存的Http接口从Apollo读取配置,如果需要配合配置推送通知实现实时更新配置的话需要调用该接口
    def _uncached_http_get(self, namespace='application'):
        url = '{}/configs/{}/{}/{}?ip={}'.format(self.config_server_url, self.appId, self.cluster, namespace, self.ip)
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            self._cache[namespace] = data['configurations']  # dict,包含当前namespace下的所有key-value
        else:
            print('_uncached_http_get error, status:{}, namespace:{}'.format(r.status_code, namespace))

    def _listener(self):
        while True:
            print('in _listener,pid:{}, time:{}'.format(os.getpid(), time.time()))
            self._long_poll()


def test_concurrency():
    from multiprocessing.dummy import Process

    def work(apollo):
        print(apollo.get_value('risk_serverkey', 'not exists', namespace='KTV.resources_config'))

    apollo = Apollo(app_id='ccktv', config_server_url='http://10.16.4.194:8080')
    # apollo = ApolloClient(app_id='ccktv', config_server_url='http://metayz.fxapollo.kgidc.cn')  # 正式环境
    ps = [Process(target=work, args=(apollo,)) for _ in range(1000)]
    for p in ps:
        p.start()

    for p in ps:
        p.join()


def test_single():
    apollo = Apollo(app_id='ccktv', config_server_url='http://10.16.4.194:8080')  # 测试环境
    # apollo = ApolloClient(app_id='ccktv', config_server_url='http://metayz.fxapollo.kgidc.cn')  # 正式环境
    conf1 = apollo.get_value('risk_serverkey', 'bb', namespace='KTV.resources_config')
    conf2 = apollo.get_value('switch_rcmd_type', 'not_exists')  # apollo返回的数据类型都是str
    print(conf1, conf2, type(conf2))


if __name__ == '__main__':
    test_concurrency()
    # test_single()