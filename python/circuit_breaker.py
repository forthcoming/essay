from enum import Enum
from functools import wraps
import time
from collections import deque


class State(Enum):
    CLOSE = 0
    HALF_OPEN = 1
    OPEN = 2


class Policy(Enum):
    COUNTER = 0
    QUEUE = 1


class CircuitBreaker:
    """
    有限状态自动机转移表
    state|alphabet  request
    close           close|open
    open            half_open|open
    half_open       close|open
    默认CLOSE态,执行func函数连续失败(前提是可以抛出异常)达到threshold次后,会转为OPEN态
    OPEN态会维持timeout时长,期间不再执行func函数,超出timeout时长后会转为HALF_OPEN态
    HALF_OPEN态下会执行一次func函数,成功则转为CLOSE态,失败则转为OPEN态
    """

    def __init__(self, timeout=60, threshold=10, policy=Policy.COUNTER, fallback=None):
        self.initial_state = State.CLOSE  # q0
        self.fail_counter = 0
        self.request_queue = deque(maxlen=100)
        self.deadline = 0
        self.__timeout = timeout
        self.__threshold = threshold
        self.__policy = policy
        self.__fallback = fallback

    def send_message(self):  # 异步发送短信告警
        pass

    def check(self):
        if self.__policy == Policy.COUNTER:
            return self.fail_counter >= self.__threshold
        else:
            return sum(self.request_queue) >= self.__threshold

    def switch_to_close(self):
        self.initial_state = State.CLOSE
        self.fail_counter = 0
        self.request_queue.append(0)

    def switch_to_open(self):
        self.initial_state = State.OPEN
        self.deadline = time.time() + self.__timeout
        self.send_message()

    def switch_to_half_open(self):
        self.initial_state = State.HALF_OPEN
        # self.fail_counter = 0   # 可以不处理
        self.request_queue.clear()

    def __call__(self, func):  # 针对每个被装饰函数(如接口函数)都会有一个CircuitBreaker实例
        @wraps(func)
        def wrapper(*args, **kwargs):  # 装饰类成员函数时第一个参数是self,此后可通过self调用类的其他属性和方法
            ret = None
            if self.initial_state == State.OPEN:
                ret = "in open state"
                if time.time() >= self.deadline:
                    self.switch_to_half_open()
            else:
                try:
                    ret = func(*args, **kwargs)
                    self.switch_to_close()
                except Exception as e:
                    self.fail_counter += 1
                    self.request_queue.append(1)
                    if self.initial_state == State.CLOSE:
                        if self.check():
                            self.switch_to_open()
                    else:
                        self.switch_to_open()
                    if callable(self.__fallback):  # func必须与fallback拥有完全相同的入参,若其一是成员函数,另一个也必须是同一个类的成员函数
                        ret = self.__fallback(*args, **kwargs)
                    print(f'{func.__module__}:{func.__name__} circuit_breaker error,{e}')
            return ret

        return wrapper


@CircuitBreaker(timeout=6, threshold=3, policy=Policy.QUEUE)
def test_circuit_breaker(index):
    print(index)
    1 / 0


if __name__ == '__main__':
    for idx in range(100):
        test_circuit_breaker(idx)
        time.sleep(1)
