import binascii
import datetime
import os
import struct
import threading
import time
from random import SystemRandom

'''
refer: https://github.com/mongodb/mongo-python-driver/blob/master/bson/objectid.py
from bson import objectid
mongodb每插入一条语句都会包含if "_id" not in document:document["_id"] = ObjectId()语句
'''
_MAX_COUNTER_VALUE = 0xFFFFFF


class ObjectId:
    # 此处的代码会在类加载时执行一次,类实例化时不再执行
    _pid = os.getpid()
    _inc = SystemRandom().randint(0, _MAX_COUNTER_VALUE)
    _inc_lock = threading.Lock()
    __random = os.urandom(5)
    __slots__ = ("__id",)

    def __init__(self):
        """
        ObjectId是一个12字节的唯一标识符,包含: 4字节值表示自Unix纪元以来的秒数; 5字节随机数;3字节以随机值开始的计数器
        4字节字段是一个不断增加的值,其范围将持续到2106年1月7日左右
        5字节字段由每个进程生成一次的随机值组成,该随机值对于机器和进程来说是唯一
        3字节计数器当驱动程序首次激活时,必须初始化为随机值,之后每次创建ObjectID时必须加1,溢出时必须重置为0
        计数器使得每秒、每个进程可以有多个ObjectID
        由于计数器可能会溢出,因此如果在一台机器的同一进程中每秒创建达到2**24个ObjectID,则可能出现重复ObjectID
        Timestamp和Counter是big endian,因为我们可以使用memcmp对ObjectID排序,并且我们希望确保递增顺序
        """
        # 4 bytes current time
        oid = struct.pack(">I", int(time.time()))  # >: big-endian   i: int

        # 5 bytes random
        oid += ObjectId._random()

        # 3 bytes inc
        with ObjectId._inc_lock:  # 确保相同进程的同一秒产生的ID也是不同的,前提是相同进程同一秒产生的ID不能超过2^24
            oid += struct.pack(">I", ObjectId._inc)[1:4]  # _inc只有3byte长度so高位会被填充成0
            ObjectId._inc = (ObjectId._inc + 1) & _MAX_COUNTER_VALUE

        self.__id = oid

    @classmethod
    def _random(cls) -> bytes:  # Generate a 5-byte random number once per process
        pid = os.getpid()
        if pid != cls._pid: 
            cls._pid = pid
            cls._inc_lock = threading.Lock()
            cls.__random = os.urandom(5)
        return cls.__random

    @property
    def binary(self) -> bytes:  # 12-byte binary representation of this ObjectId
        return self.__id

    @property
    def generation_time(self):
        timestamp = struct.unpack(">i", self.__id[0:4])[0]
        return datetime.datetime.fromtimestamp(timestamp)

    def __str__(self):
        return binascii.hexlify(self.__id).decode()


if __name__ == "__main__":
    obj_id = ObjectId()
    print(obj_id)
