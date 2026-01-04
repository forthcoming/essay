import datetime
import os
import struct
import threading
import time
from random import SystemRandom

_MAX_COUNTER_VALUE = 0xFFFFFF
_INT_STRUCT = struct.Struct(">I")
_INT_RANDOM_STRUCT = struct.Struct(">I5s")  # 大端序无符号4字节整数 + 5个字节的bytes


class ObjectId:
    __slots__ = ("_id",)
    _inc = SystemRandom().randint(0, _MAX_COUNTER_VALUE)
    _inc_lock = threading.Lock()
    _random_value = os.urandom(5)

    def __init__(self):
        # refer: https://github.com/mongodb/mongo-python-driver/blob/master/bson/objectid.py
        # from bson import objectid
        # mongodb每插入一条语句都会包含if "_id" not in document:document["_id"] = ObjectId()语句

        # ObjectId是一个12字节的唯一标识符,包含: 4字节值表示自Unix纪元以来的秒数; 5字节随机数;3字节以随机值开始的计数器
        # 4字节字段是一个不断增加的值,其范围将持续到2106年1月7日左右
        # 5字节字段由每个进程生成一次的随机值组成,该随机值对于机器和进程来说是唯一
        # 3字节计数器当驱动程序首次激活时,必须初始化为随机值,之后每次创建ObjectID时必须加1,溢出时必须重置为0
        # 计数器使得每秒、每个进程可以有多个ObjectID
        # 由于计数器可能会溢出,因此如果在一台机器的同一进程中每秒创建达到2**24个ObjectID,则可能出现重复ObjectID
        with ObjectId._inc_lock:  # 确保相同进程的同一秒产生的ID也是不同的,前提是相同进程同一秒产生的ID不能超过2^24
            inc = ObjectId._inc  # 好处是可以将self.__id放到锁外,减少锁持有时间
            ObjectId._inc = (inc + 1) & _MAX_COUNTER_VALUE
        # _inc只有3byte长度so高位会被填充成0
        self._id = _INT_RANDOM_STRUCT.pack(int(time.time()), ObjectId._random_value) + _INT_STRUCT.pack(inc)[1:4]

    @property
    def generation_time(self) -> datetime.datetime:
        timestamp = _INT_STRUCT.unpack(self._id[0:4])[0]
        return datetime.datetime.fromtimestamp(timestamp)

    def __str__(self) -> str:
        return self._id.hex()

    def __int__(self) -> int:
        return int.from_bytes(self._id, 'big')

    @staticmethod
    def reinit_after_fork():  # spawn方式子进程重新执行类定义,所有类变量都是新值,无需调用 reinit_after_fork
        ObjectId._inc = SystemRandom().randint(0, _MAX_COUNTER_VALUE)
        ObjectId._inc_lock = threading.Lock()  # 直接创建新锁，无论旧锁什么状态
        ObjectId._random_value = os.urandom(5)


os.register_at_fork(after_in_child=ObjectId.reinit_after_fork)  # fork方式才会触发,fork之后立马执行,不会有多线程冲突

if __name__ == "__main__":
    obj_id = ObjectId()
    print(obj_id)
    print(int(obj_id))
