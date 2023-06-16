# -*- coding: utf-8 -*-
import time
from functools import wraps


class FusesPolicyBase:
    def __init__(self, threshold):
        self.threshold = threshold

    def is_open(self, fail_counter, request):
        """是否开启熔断"""
        raise NotImplementedError("Must implement is_open!")

    def is_melting_point(self, fail_counter, requests):
        """是否到熔断的临界点"""
        raise NotImplementedError("Must implement is_melting_point!")


class FusesCountPolicy(FusesPolicyBase):  # 计数法熔断策略
    def __init__(self, threshold):
        super().__init__(threshold)

    def is_melting_point(self, fail_counter, requests):
        if fail_counter >= self.threshold:
            return True
        return False

    def is_open(self, fail_counter, requests):
        return self.is_melting_point(fail_counter, requests)


class FusesPercentPolicy(FusesPolicyBase):
    def __init__(self, threshold):
        super().__init__(threshold)

    def is_melting_point(self, fail_counter, requests):
        if not requests:
            return False
        if sum(requests) <= len(requests) - self.threshold:
            return True
        return False

    def is_open(self, fail_counter, requests):
        if requests[-1] == 0 and self.is_melting_point(fail_counter, requests):
            return True
        return False


class FusesState:
    def __init__(self, fuses, name):
        self._fuses = fuses
        self._name = name

    @property
    def name(self):
        return self._name

    def do_fallback(self):
        raise NotImplementedError("Must implement do_fallback!")

    def success(self):
        raise NotImplementedError("Must implement success!")

    def error(self):
        raise NotImplementedError("Must implement error!")


class FusesClosedState(FusesState):
    """熔断关闭状态"""

    def __init__(self, fuses, name='closed'):
        super().__init__(fuses, name)
        self._fuses.reset_fail_counter()

    def do_fallback(self):
        if self._fuses.is_open():
            self._fuses.open()  # 改为熔断打开状态
            return True
        return False

    def success(self):
        self._fuses.reset_fail_counter()  # self._fail_counter = 0
        self._fuses.append_success_request()  # FusesPercentPolicy用

    def error(self):
        self._fuses.increase_fail_counter()  # self._fail_counter += 1


class FusesOpenState(FusesState):
    """熔断打开状态"""

    def __init__(self, fuses, name='open'):
        super().__init__(fuses, name)
        self.last_time = time.time() + self._fuses.timeout

    def do_fallback(self):
        if time.time() > self.last_time:
            self._fuses.half_open()
            return False
        return True

    def success(self):
        pass

    def error(self):
        pass


class FusesHalfOpenState(FusesState):
    """`熔断半闭合状态`"""

    def __init__(self, fuses, name='half_open'):
        super().__init__(fuses, name)

    def do_fallback(self):
        return False

    def success(self):
        """熔断半闭合状态重试成功
        """
        self._fuses.reset_fail_counter()
        self._fuses.append_success_request()
        if not self._fuses.is_melting_point():
            self._fuses.close()  # 改为熔断关闭状态

    def error(self):
        self._fuses.increase_fail_counter()  # 这一步好像没用
        self._fuses.open()  # 改为熔断打开状态


class Fuses:
    def __init__(self, name, threshold, timeout, policy=0, enable_sms=False):
        """
        :param threshold: 触发熔断阈值
        :param timeout: 二次试探等待时间
        :param policy: 熔断策略 0=计数法 1=滑动窗口
        """
        self._name = name
        self._threshold = threshold
        self._policy = FusesPercentPolicy(threshold) if policy == 1 else FusesCountPolicy(threshold)
        self._fail_counter = 0
        self._request_queue = [1] * 10
        self._cur_state = FusesClosedState(self)  # 此处是循环引用
        self.timeout = timeout
        self.enable_sms = enable_sms

    @property
    def name(self):
        return self._name

    @property
    def cur_state(self):
        return self._cur_state.name

    @property
    def request_queue(self):
        return self._request_queue

    @property
    def threshold(self):
        return self._threshold

    @property
    def fail_counter(self):
        return self._fail_counter

    def reset_fail_counter(self):
        self._fail_counter = 0

    def open(self):
        if self.enable_sms:
            pass
            # send_msg_to_phone()
        self._cur_state = FusesOpenState(self)

    def close(self):
        self._cur_state = FusesClosedState(self)

    def half_open(self):
        self._cur_state = FusesHalfOpenState(self)

    def append_success_request(self):
        self._request_queue.append(1)
        self._request_queue = self._request_queue[-10:]

    def append_fail_request(self):
        self._request_queue.append(0)
        self._request_queue = self._request_queue[-10:]  # 取后10个元素

    def increase_fail_counter(self):
        self._fail_counter += 1
        self.append_fail_request()

    def is_open(self):
        return self._policy.is_open(self._fail_counter, self._request_queue)

    def is_melting_point(self):
        return self._policy.is_melting_point(self._fail_counter, self._request_queue)

    def do_fallback(self):
        return self._cur_state.do_fallback()

    def on_success(self):
        self._cur_state.success()

    def on_error(self):
        self._cur_state.error()


def circuit_breaker(threshold=5, timeout=60, is_member_func=True, default_value=None, fallback=None, policy=0,
                    enable_sms=True):
    '''
    连续失败达到threshold次才会由默认的FusesClosedState态转为FusesOpenState态,前提是熔断函数f可以抛出异常
    FusesOpenState态会维持一段timeout时长,FusesOpenState态下不会再调用熔断函数f,只会调用fall_back
    随后由FusesOpenState态转为FusesHalfOpenState态,调用一次熔断函数f,成功则转为FusesClosedState态,否则转为FusesOpenState态,依次循环下去
    注意: 
    当circuit_breaker装饰类成员函数时,_wrapper入残第一个参数是self,可以写成_wrapper(self,*args, **kwargs)
    此后可通过self调用类的其他属性和方法,f可通过f(self,*args, **kwargs)调用
    '''

    def fall_back(*args, **kwargs):
        ret = default_value
        if callable(fallback):
            if is_member_func:
                args = args[1:]  # 去掉第一个self参数
                ret = fallback(*args, **kwargs)
            else:
                ret = fallback(*args, **kwargs)
        return ret

    def circuit_breaker_decorator(f):
        name = '{}:{}'.format(f.__module__, f.__name__)
        fuse = Fuses(name, threshold, timeout, policy, enable_sms)  # 装饰f时会执行,初始化一次

        @wraps(f)
        def _wrapper(*args, **kwargs):  # 装饰类成员函数时第一个参数是self,此后可通过self调用类的其他属性和方法
            if fuse.do_fallback():
                ret = fall_back(*args, **kwargs)  # 由FusesClosedState态转为FusesOpenState态执行;FusesOpenState态期间执行  
            else:
                try:
                    ret = f(*args, **kwargs)
                    fuse.on_success()
                except Exception as e:
                    fuse.on_error()
                    ret = fall_back(*args, **kwargs)  # FusesClosedState态f抛异常时执行
                    print('{} circuit_breaker error,{}'.format(name, e))
            return ret

        return _wrapper

    return circuit_breaker_decorator


@circuit_breaker(timeout=6)
def test(index):
    print(index)
    1 / 0


if __name__ == '__main__':
    for idx in range(50):
        time.sleep(1)
        test(idx)
