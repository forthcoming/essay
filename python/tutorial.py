import binascii
import copy
import ctypes
import dis
import hashlib
import inspect
from loguru import logger
import os
import pickle
import random
import re
import sqlite3
import struct
import sys
import time
from bisect import insort_right, bisect_left, bisect_right
from collections import Counter
from collections.abc import Iterable, Iterator, Generator
from datetime import datetime, timedelta
from functools import lru_cache, wraps
from heapq import heapify, heappop, heappush, nlargest, nsmallest, heappushpop
from subprocess import run, PIPE
from threading import Lock
from playwright.async_api import async_playwright
import pandas as pd
import socket

"""
pip show flask  # 查看库安装信息(路径等)
python -m pip install redis  # 在当前python环境下执行pip
pip -V # 获取当前pip绑定的python, pip 23.3.1 from D:/python/Lib/site-packages/pip (python 3.12)
pip list --format=freeze > requirements.txt 
pip install -r requirements.txt
pip install --proxy=http://127.0.0.1:8118 scrapy==1.4.0
pip install --proxy=socks5://127.0.0.1:1080 scrapy==1.4.0
pip install redis -i http://mirrors.aliyun.com/pypi/simple --trusted-host mirrors.aliyun.com  # -i指定库的安装源
pip uninstall
pip config edit --editor vim  # 手动编辑配置文件

conda list  # 列出当前虚拟环境的所有安装包(包括conda和pip安装的包,这两个命令install作用差不多)
conda create -n scrapy python=3.12 # 创建虚拟环境
conda env list  
conda activate scrapy # 激活,进入到虚拟环境后,如果该环境没有python2,pip等之类包的话会自动识别到base虚拟环境中的包,路径:miniconda3/envs/scrapy
conda deactivate # 退出虚拟环境
conda install -n scrapy python=3.12  # 也可以先进到对应虚拟环境,再conda install python=3.12
conda install /root/Desktop/软件名,如果某些包找不到,可以先切换到对应的虚拟环境,再python -m pip install安装
conda remove -n scrapy --all

uv python list: View available Python versions.
uv run example.py  # 在uv管理的环境中运行命令,无需source .venv/bin/activate, 会根据pyproject.toml文件自动安装缺少的依赖
uv init: Create a new Python project.
uv add: Add a dependency to the project.类似于pip install <package> + 写入pyproject.toml,如果虚拟环境未创建,会先执行uv venv
uv remove: Remove a dependency from the project.
uv sync: Sync the project's dependencies with the environment.根据pyproject.toml安装或更新项目依赖
uv tree: View the dependency tree for the project.
uv build: Build the project into distribution archives.
uv publish: Publish the project to a package index.
uvx [--python 3.8] scrapy version: uvx用于临时运行Python命令行工具（CLI）,而无需永久安装这些工具,等价于uv tool run
pyproject.toml: 项目的元数据和项目依赖,由开发者手动维护.
uv.lock文件作用: 所有直接依赖和它们的子依赖具体版本、下载地址和校验哈希等,保证项目环境的一致性（可复现部署）,自动生成.
.python-version: 控制项目虚拟环境的python版本,但必须满足pyproject.toml.requires-python要求


python运算符优先级如下, 与传统c语言运算符优先级有区别
refer: https://docs.python.org/3/reference/expressions.html?highlight=operator%20precedence
**
+x -x ~x
* @ / // %
+ -
<< >>
&
^
|
in not in is is not <= < > >= == !=
not
and
or


Python运行时不强制执行函数和变量类型注解, 但这些注解可用于类型检查器、IDE、静态检查器等第三方工具,pycharm需要安装mypy插件
常见注解:
list[float], 只能有一个参数
tuple[str, int, bool] tuple[float, ...], tuple是特殊类型,可以有多个参数
dict[str, str | int]
-> None
int | str
value: int = 3
需要在定义类型的时候用到类类型时,在类名两边加双引号即可


compiler是将编程语言翻译成01机器语言的软件
interpreter是将编程语言一行行翻译成01机器语言的软件
python属于解释性语言,_开头的变量名表示不建议用户使用; _结尾的变量名表示避免与关键字冲突
函数名跟普通变量名一样,都可以被赋值,传参,返回等操作,都是pyobject对象
cpython源码,Python: 解释器相关代码; Objects: built-in objects实现(如list,dict); Include: c头文件; Lib: python写的内置库; Modules:c写的内置库
python -u test.py, 其中-u(unbuffered)参数强制其标准输出同标准错误一样不通过缓存直接打印到屏幕


原码 & 补码
原码: 用最高位表示符号位, 1表示负, 0表示正, 其他位存放该数的二进制的绝对值
补码: 正数的补码等于他的原码, 负数的补码等于正数的原码取反加一
计算机存的是补码
-5转化为补码: (0b00000101 ^ 0xff) + 1 = > 0b11111011
0b11111011转化为整数: -((0b11111011 ^ 0xff) + 1) = > -5


and, or, not
x and y和x or y返回的结果是决定表达式结果的值
and: 如果x为真, 则y决定结果, 返回y; 如果x为假, x决定了结果为假, 返回x
not返回表达式结果的相反的值, 如果表达式结果为真则返回false, 如果表达式结果为假则返回true


__str__: 自定义打印类的格式,print打印类实例时被调用
__len__: 自定义类长度,len作用于类实例时被调用
__call__: 类实例被当作函数调用时调用
__name__: 通过"类.__name__"返回字符串类型的类名,类实例无此属性

What kinds of global value mutation are thread-safe?
内部使用GIL来确保Python VM中一次只有一个线程运行,Python只提供字节码指令之间的线程切换
从Python程序的角度来看,每条指令到达的所有C实现代码都是原子,例如以下原子操作(L,L1,L2是列表,D,D1,D2是字典,x,y是对象,i,j是整数):
L.append(x)
L1.extend(L2)
x = L[i]
x = L.pop()
L1[i:j] = L2
L.sort()
x = y
x.field = y
D[x] = y
D1.update(D2)
D.keys()
These aren’t:
i = i+1
L.append(L[-1])
L[i] = L[j]
D[x] = D[x] + 1


ipdb
whatis       Prints the type of the argument.
enter        重复上次命令
set_trace()  在该点打断(from ipdb import set_trace,或者直接在该处使用breakpoint(),不需要使用set_trace()函数)
c(ont(inue))   Continue execution, only stop when a breakpoint is encountered.执行到下个断点处
l(ist) [first [,last]]  List source code for the current file.Without arguments, list 11 lines around the current line or continue the previous listing.
j(ump)   程序跳到指定行
p        打印某个变量
pp       Pretty-print the value of the expression.
n(ext)   让程序运行下一行,如果当前语句有一个函数调用,用n是不会进入被调用的函数体中
s(tep)   跟n相似,但是如果当前有一个函数调用,那么s会进入被调用的函数体中
q        退出调试
r(eturn)  继续执行,直到函数体返回(Continue execution until the current function returns.)
b(reak)  在指定行打断点
ipdb>    后面跟语句,可以直接改变某个变量
h(elp)   打印当前版本Pdb可用的命令,如果要查询某个命令,可以输入h [command],例如:"h l"查看list命令
pinfo2   Provide extra detailed information about an object(值,类型,长度等信息)


模块(module): 
是一个包含Python代码的.py文件
遇到循环导入问题,可以将某个模块放在函数或类内导入,或者将冲突部分单独提出一个模块
如果py文件中使用了相对路径导入,则这个py文件无法作为脚本直接运行,只能作为模块被导入,应为relative import都是先通过module的__package__找到绝对路径
包(package): 
是一个包含多个模块的文件夹,且这个文件夹包含一个名为__init__.py的文件,这使得包内的模块可以被导入到其他Python脚本中
导入包实际是导入了它的__init__.py文件,被导入module中的全局代码, 类静态区都会被执行,同一个module只会被导入一次

from xxx import *时如果定义了__all__,则只会导入其定义的对象
变量sys.path是一个字符串列表, 它为解释器指定了模块的搜索路径,包括 当前程序所在目录、标准库的安装目录、操作系统环境变量PYTHONPATH所包含的目录
vim ~/.bashrc  # vim /etc/profile 全局
export PYTHONPATH=$PYTHONPATH:/root/Desktop/atlas
source ~/.bashrc

import sys
sys.path.append('/root/Desktop')   # 添加python查询路径

CUDA_VISIBLE_DEVICES=0,1,2,3,4 python server.py
GPU设备通常从0开始编号,设置CUDA_VISIBLE_DEVICES环境变量来控制哪些GPU对PyTorch可见,不设置则对所有GPU可见(仅影响可见行,不决定使用gpu还是cpu)
'cuda': 按CUDA_VISIBLE_DEVICES指定顺序使用第一块GPU; 'cuda:2': 按CUDA_VISIBLE_DEVICES指定顺序使用第三块GPU
"""


def get_ip():
    ip = '127.0.0.1'
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(('8.8.8.8', 53))
        ip = sock.getsockname()[0]
        sock.close()
    except Exception as e:
        print(e)
    return ip


def str_tutorial():
    """
    isalnum: 如果string至少有一个字符并且所有字符都是字母或数字则返回True,否则返回False
    isalpha: 检测字符串是否只由字母组成
    isdigit: 检测字符串是否只由数字组成
    lower/upper: 转换字符串中所有字符为小写/大写
    lstrip: 截掉字符串左边的空格或指定字符
    replace: 把字符串中的旧字符串替换成新字符串,如果指定第三个参数max,则替换不超过max次
    startswith/endswith: 检查字符串是否是以指定子字符串开头/结尾
    """
    string = "Line1-abcdef \nLine2-abc \nLine4-abcd"
    print(string.split())  # ['Line1-abcdef', 'Line2-abc', 'Line4-abcd']
    print(string.split(' ', 1))  # ['Line1-abcdef', '\nLine2-abc \nLine4-abcd']
    print(string.split(' '))  # ['Line1-abcdef', '\nLine2-abc', '\nLine4-abcd']
    # 应用: 去除字符串中空白符content =''.join(content.split())
    assert 'ABCD' < 'bar' < 'bloom'  # 注意关系运算符<,>,=,<=,>=可以连写,前提是不能用括号


def tuple_tutorial():
    # tuple不可变指的是其元素的id不可变
    a = (1, [2])
    print(id(a), id(a[0]), id(a[1]))  # 4566784320 4577922136 4566790656
    a[1].append(3)
    # a[1] = [3]  # error
    print(id(a), id(a[0]), id(a[1]))  # 4566784320 4577922136 4566790656
    b = 1,
    assert type(b) == tuple


def list_tutorial():
    arr = [1, 2, 3, 4, 5]
    print(arr[:2:-1])  # [5, 4],等价于arr[len(arr)-1:2:-1]
    print(arr[::-1])  # [5, 4, 3, 2, 1]
    arr[2:3] = [0, 0]  # 注意这里的用法(区别于a[2] = [0, 0])   [1, 2, 0, 0, 4, 5]
    arr[1:1] = [8, 9]  # [1, 8, 9, 2, 0, 0, 4, 5]
    arr[1:-1] = []  # [1,5] ,等价于del a[1:-1]

    # __add__ & __iadd__
    '''
    += tries to call the __iadd__ special method, and if that isn't available it tries to use __add__ instead.
    + operator tries to call the  __add__ special method returns a new object.
    The __iadd__ special method is for an in-place addition, that is it mutates the object that it acts on.
    For immutable types (where you don't have an __iadd__) a += b and a = a + b are equivalent.
    '''
    a1 = a2 = [1, 2]
    b1 = b2 = [1, 2]
    a1 += [3]  # Uses __iadd__, modifies a1 in-place
    b1 = b1 + [3]  # Uses __add__, creates new list, assigns it to b1
    print(a2)  # [1, 2, 3]   a1 and a2 are still the same list
    print(b2)  # [1, 2]      whereas only b1 was changed

    assert [1, 2, 3] < [1, 4]
    assert [1, 2] < [1, 2, -1]


def set_tutorial():  # 无序不重复, 添加元素用add
    # 区别于位运算符中的& ,| ,^和逻辑运算符 and or not
    set_a = {1, 2, 3, 3}
    set_b = {3, 4, 5, 6, 7}
    print(set_a == set_b)  # False
    print(set_a < set_b)  # False,set_a不是set_b的子集,因为集合无序,比较运算符无法比较元素字典大小,比较的是子集关系
    print(set_a - set_b)  # set([1, 2])
    print(set_b - set_a)  # set([4, 5, 6, 7])
    print(set_a | set_b)  # set([1, 2, 3, 4, 5, 6, 7])
    print(set_a & set_b)  # set([3])
    print(set_a ^ set_b)  # set([1, 2, 4, 5, 6, 7]) , numbers in set_a or in set_b but not both
    assert (set_a | set_b) - (set_a & set_b) == (set_a - set_b) | (set_b - set_a) == set_a ^ set_b


def dict_tutorial():  # 字典有序
    d = {'a': 1, 'b': 2}
    d.update({'a': 3, 'c': 4})  # {'a': 3, 'b': 2, 'c': 4}
    print(d.pop('a', '无a'))  # 类似于get,3
    print(d.setdefault('d'))  # None
    print(d.setdefault('e', 'avatar'))  # avatar
    print(d.setdefault('b', 'akatsuki'))  # 2
    print(d)  # {'b': 2, 'c': 4, 'd': None, 'e': 'avatar'}

    one = {'a': 1, 'b': 2}
    two = {'b': 3, 'c': 4}
    _ = one | two  # {'a': 1, 'b': 3, 'c': 4},合并两个字典
    _ = two | one  # {'b': 2, 'c': 4, 'a': 1},合并两个字典


def dis_tutorial():
    # load_fast 把一个局部变量压入栈中
    # binary_add 弹出栈顶两个元素, 相加后结果入栈
    # return_value 反回栈顶元素
    A = type('A', (), {})
    dis.dis(A)  # 解释器实际执行的byte code是二进制编码

    def f():
        pass

    dis.dis(f)
    dis.dis("2**3")


def is_tutorial():
    # is比较的内存地址; == 比较的是字面值
    x = y = [4, 5, 6]
    z = [4, 5, 6]
    assert x == y == z
    assert x is y
    assert x is not z
    print(id(x), id(y), id(z))  # 1685786989512 1685786989512 1685786991112


def byte_string_tutorial():
    byte_string = b'ab\xffc'  # 字节串类型是bytes,如0b11111111没有对应的字符,所以用\xff表示
    byte_array = bytearray(byte_string)  # bytes和bytearray都可以被遍历,取单个字符时返回的是字符对应的整数值
    assert len(byte_array) == len(byte_string) == 4
    # b'中a'  # error,bytes can only contain ASCII literal characters
    assert "test中".encode() == b'test\xe4\xb8\xad' and b'test\xe4\xb8\xad'.decode() == "test中"

    # big-endian: 低位地址保存高位数字,方便阅读和排序
    # little-endian: 低位地址保存低位数字(比特位从右至左),在变量指针转换的时候地址保持不变,比如int64*转到int32*
    # 目前看来是little-endian成为主流了
    # bool is_big_endian() //如果字节序为big-endian,返回1,反之返回0
    # {
    #   unsigned short test = 0x1122;   // 2字节
    #   if(*( (unsigned char*) &test ) == 0x11)  // 取低位第一个字节的地址
    #     return true;
    #   else
    #     return false;
    # }
    assert b'\xff\x01\x03\x00' == struct.pack(">I", 0b11111111000000010000001100000000)  # >: big-endian, i: int
    assert b'\x00\x03\x01\xff' == struct.pack("<I", 0b11111111000000010000001100000000)
    assert ord('a') == 97 and chr(97) == 'a' and struct.unpack(">B", b'a')[0] == 97


def common_tutorial():
    # collections.deque([iterable[, maxlen]])
    """
    Deques support memory efficient appends and pops from either side of the deque with approximately the same O(1) performance in either direction.
    Though list objects support similar operations, they are optimized for fast fixed-length operations and incur O(n) memory movement
    costs for pop(0) and insert(0, v) operations which change both the size and position of the underlying data representation.
    If maxlen is not specified or is None, deques may grow to an arbitrary(任意的) length.
    Otherwise the maxlen is full, when new items are added, a corresponding number of items are discarded from the opposite end.
    deque是链式存储结构, 可以当栈和队列来使用,一般情况下list可以代替stack,但不能代替queue
    """

    # os.walk(top[, topdown=True[, onerror=None[, followlinks=False]]])
    """
    top - - 根目录下的每一个文件夹(包含它自己), 产生3 - 元组(dirpath, dirnames, filenames)[文件夹路径, 文件夹名字, 文件名]
    topdown - -为True或者没有指定, 目录自上而下.如果topdown为False, 目录自下而上
    followlinks - - 设置为true, 则通过软链接访问目录
    """

    int('0x0102', 16)  # 258, 字符串是16进制,并将其转换成10进制
    print("content", end="\t", flush=True)  # flush=True意思是不缓存,有内容则输出
    print(None is None)  # None用is判断,速度更快,还防止__eq__风险,不建议用==
    print(binascii.hexlify(b'ab'))  # b'6162', hexlify将b字符串按字符转换为16进制数字b串
    print(sys.getsizeof([]))  # Return the size of object in bytes.

    a, b, c, d = 255, 98, 16, 1
    ip = f"{a}.{b}.{c}.{d}"
    ip_byte_str = socket.inet_aton(ip)
    assert socket.inet_ntoa(ip_byte_str) == ip
    assert struct.unpack(">I", ip_byte_str)[0] == (a << 24) | (b << 16) | (c << 8) | d

    x = 1
    print(eval('x+1'), x)  # 2, 1  执行字符串形式的表达式,返回执行结果
    result = {}
    exec('x+=10;print(f"in exec x={x}")', locals(), result)  # in exec x=11,执行字符串形式的代码,结果存到result,exec返回None
    print(result, x)  # {'x': 11} 1

    secret = hashlib.md5(b"hello blockchain world, this is yeasy@github")
    print(secret.hexdigest())  # 1ee216d3ef1d217cd2807348f5f7ce19
    '''
    echo -n "hello blockchain world, this is yeasy@github"|md5sum
    注意Linux下要去掉字符串末尾的\n
    '''


def counter_tutorial():
    count = Counter([1, 1, 2, 2, 3, 3, 3, 3, 4, 5])
    print(count)  # Counter({3: 4, 1: 2, 2: 2, 4: 1, 5: 1})
    print(count[3], count['y'])  # 4 0 ,访问不存在的元素返回0
    print(count.most_common(1))  # [(3, 4)]
    print(count.most_common(3))  # [(3, 4), (1, 2), (2, 2)]
    count.update('plus')  # 计数器更新
    count.subtract('minus')  # 计数器更新
    print(count)  # Counter({3: 4, 1: 2, 2: 2, 4: 1, 5: 1, 'l': 1, 'p': 1, 'u': 0, 's': 0, 'i': -1, 'n': -1, 'm': -1})
    print(list(count.elements()))  # [1, 1, 2, 2, 3, 3, 3, 3, 4, 5, 'l', 'p']

    counter_a = Counter([0, 1, 2, 2, 2])  # Counter({2: 3, 0: 1, 1: 1})
    counter_b = Counter([2, 2, 3])  # Counter({2: 2, 3: 1})
    print(counter_a | counter_b)  # Counter({2: 3, 0: 1, 1: 1, 3: 1})
    print(counter_a & counter_b)  # Counter({2: 2})
    print(counter_a + counter_b)  # Counter({2: 5, 0: 1, 1: 1, 3: 1})
    print(counter_a - counter_b)  # Counter({0: 1, 1: 1, 2: 1})
    print(counter_b - counter_a)  # Counter({3: 1})


def zip_tutorial():
    arr_a = ['a', 'b', 'c']
    arr_b = '123'
    print(list(zip(arr_a, arr_b)))  # [('a', '1'), ('b', '2'), ('c', '3')]
    print(dict(zip(arr_a, arr_b)))  # {'a': '1', 'b': '2', 'c': '3'}
    for i, j in zip(arr_a, arr_b):  # 同时遍历两个或更多的序列
        print(i, j)
    # a 1
    # b 2
    # c 3

    matrix = [[1, 2], [3, 4], [5, 6]]
    [list(_) for _ in zip(*matrix)]  # [[1, 3, 5], [2, 4, 6]], 矩阵置换
    print([[matrix[j][i] for j in range(3)] for i in range(2)])  # [[1, 3, 5], [2, 4, 6]]
    print([[row[i] for row in matrix] for i in range(2)])  # [[1, 3, 5], [2, 4, 6]]
    print([row[i] for row in matrix for i in range(2)])  # [1, 2, 3, 4, 5, 6],注意顺序,先for row in matrix,再for i in range(2)
    print([element for row in matrix for element in row])  # [1, 2, 3, 4, 5, 6],列表推导式效率比map, reduce, filter等高阶函数效率更高


def bin_sect_tutorial():
    arr = []
    for idx in [3, 1, 6, 4, 1, 3, 6, 5, 1, 4]:
        insort_right(arr, idx)
    print(arr)  # [1, 1, 1, 3, 3, 4, 4, 5, 6, 6]
    print(bisect_left(arr, 3))  # 3
    print(bisect_right(arr, 3))  # 5
    insort_right(arr, 2)


def slots_tutorial():
    """
    __slots__ are implemented at the class level by creating descriptors for each variable name.
    it really only saves you when you have thousands of instances
    __slots__定义的属性仅对当前类实例起作用,对继承的子类不起作用
    classes defining __slots__ do not support weak references to its instances.
    If weak reference support is needed, then add '__weakref__' to the sequence of strings in the __slots__ declaration.
    实例的__dict__只保存实例变量,不保存类属性(变量和函数)
    """

    class Slots:
        a = 123
        b = []
        c = 'string'
        __slots__ = ['d', 'e']  # 限制实例的属性只能是d跟e, 去掉实例的__dict__,__weakref__ 属性, 能达到更快的属性访问和更少的内存消耗

        def __init__(self):
            self.d = 'd'
            self.e = 123

        def test(self): pass

    print(Slots.__dict__)
    # slots = Slots()
    # print(slots.__dict__)      # error
    # print(slots.__weakref__ )  # error
    # slots.f = []               # error


def variable_tutorial():
    """
    类变量(class variable)是类的属性和方法,它们会被类的所有实例共享.而实例变量(instance variable)是实例对象所特有的数据,不能通过类名访问
    实例访问变量x,先在自身的__dict__中查找是否有x,如果有则返回,否则进入实例所属的类__dict__中进行查找,找不到则抛出异常
    """

    class Test:
        c_var = []

        def __init__(self):
            self.i_var = 2

    v1 = Test()
    v2 = Test()
    v3 = Test()
    print(v1.__dict__)  # {'i_var': 2},只包含实例属性
    print(Test.__dict__)  # {'c_var': [], '__init__': <function Test.__init__>},只包含类属性

    v1.c_var = [5]  # 当且仅当c_var是可变类属性并修改他时才会修改类属性,否则改变的是当前的实例属性
    print(v1.__dict__)  # {'i_var': 2, 'c_var': [5]},新增c_var实例属性
    print(v2.__dict__)  # {'i_var': 2},不包含v1新增的实例属性c_var
    print(Test.__dict__)  # {'c_var': [], '__init__': <function Test.__init__>},此时的c_var = []不变

    # 此时v2,v3,Test都保持原样
    v2.c_var += [4]  # 等价于v2.c_var.append(4)
    assert id(v2.c_var) == id(v3.c_var) == id(Test.c_var) and id(Test.c_var) != id(v1.c_var)
    assert v2.c_var == v3.c_var == Test.c_var == [4]
    print(v2.__dict__)  # {'i_var': 2, 'c_var': [4]}
    print(v3.__dict__)  # {'i_var': 2}
    print(Test.__dict__)  # {'c_var': [4], '__init__': <function Test.__init__>}

    class A:
        a = 10

    obj1 = A()
    obj2 = A()
    obj1.a += 2
    print(id(obj1.a), id(obj2.a), id(A.a))  # 8790824644704 8790824644640 8790824644640
    print(obj1.a, obj2.a, A.a)  # 12 10 10
    print(obj1.__dict__, obj2.__dict__, A.__dict__)  # {'a': 12} {} {'a': 10}


def exception_tutorial():
    try:
        # os._exit(0)   # 会阻止一切语句的执行,包括finally
        1 / 0
    except ValueError as e:  # 至多只有一个except被执行
        print('That was no valid number.', e)
    except (ZeroDivisionError, RuntimeError):
        print('The divisor can not be zero.')
    except:  # 匹配任何类型异常,必须放在最后(default 'except:' must be last)
        print('Handling other exceptions...')
    else:  # 必须放在所有except后面,当没有异常发生时执行
        print('no exception happen')
    finally:  # 定义一些清理工作,异常发生/捕捉与否,是否有return都会执行
        print('Some clean-up actions!')


def format_tutorial():  # 最新版Python的f字符串可以看作format的简写
    # 'My name is: ansheng, I am 20 years old'
    string = "My name is: {}, I am {} years old".format(*["ansheng", 20])
    # 'My name is: ansheng, I am 20 years old, ansheng Engineer'
    string = "My name is: {0}, I am {1} years old, {0} Engineer".format(*["ansheng", 20, "Python"])
    # 'My name is: ansheng, I am 20 years old'
    string = "My name is: {name}, I am {age} years old".format(**{"name": "ansheng", "age": 20})
    # 'My name is: Ansheng, I am 20 years old, 66666.550000 wage'
    string = "My name is: {:s}, I am {:d} years old, {:f} wage".format("Ansheng", 20, 66666.55)
    # 'numbers: 1111,15.000,15,0xf,F, 1500.000000%'
    string = "numbers: {0:b},{0:.3f},{0:d},{0:#x},{0:X}, {0:%}".format(15)
    # numbers: 1111,15.000000,15,0xf,F, 1500.000000%
    print(f"numbers: {15:b},{15:f},{15:d},{15:#x},{15:X}, {15:%}")


def with_tutorial():
    class Sample:
        def __enter__(self):
            print("In __enter__")
            return 'test'  # 返回值赋给with后面的as变量

        def __exit__(self, _type, value, trace):
            """
            没有异常的情况下整个代码块运行完后触发__exit__,他的三个参数均为None
            当有异常产生时,从异常出现的位置直接触发__exit__
            __exit__运行完毕就代表整个with语句执行完毕
            返回值为True代表吞掉了异常,并且结束代码块运行,但是代码块之外的代码会继续运行,否则代表抛出异常,结束所有代码的运行,包括代码块之外的代码
            """
            print("In __exit__,type: {}, value: {}, trace: {}".format(_type, value, trace))
            return True

        @staticmethod
        def do_something():
            1 / 0

    sample = Sample()
    with sample as f:  # 相当于f = sample.__enter__(),如果不使用with语法,__exit__不会生效
        print(f)  # test
        sample.do_something()
        print('after do something')


def copy_tutorial():
    a = [0, [1, ], (2,)]
    b = a  # 相当于&
    c = a[:]  # 等价于copy.copy(a),相当于部分&
    d = copy.copy(a)
    e = copy.deepcopy(a)  # 此时e跟a无任何关系
    a[0] = 5
    a[1][0] = 4
    print('a:', a)
    print('b:', b, id(b) == id(a), id(b[0]) == id(a[0]), id(b[1]) == id(a[1]), id(b[2]) == id(a[2]))
    print('c:', c, id(c) == id(a), id(c[0]) == id(a[0]), id(c[1]) == id(a[1]), id(c[2]) == id(a[2]))
    print('d:', d, id(d) == id(a), id(d[0]) == id(a[0]), id(d[1]) == id(a[1]), id(d[2]) == id(a[2]))
    print('e:', e, id(e) == id(a), id(e[0]) == id(a[0]), id(e[1]) == id(a[1]), id(e[2]) == id(a[2]))
    # a: [5, [4], (2,)]
    # b: [5, [4], (2,)] True True True True
    # c: [0, [4], (2,)] False False True True
    # d: [0, [4], (2,)] False False True True
    # e: [0, [1], (2,)] False False False True
    shadow_copy = [[1, 2, 3, 4]] * 3
    deep_copy = [[1, 2, 3, 4] for _ in range(3)]


def divide_tutorial():
    # 地板除(不管操作数为何种数值类型, 总是会舍去小数部分, 返回数字序列中比真正的商小的最接近的数字)
    print(5 // 2)  # 2
    print(5 // 2.0)  # 2.0
    print(5 // -2)  # -3


def subprocess_tutorial():
    # !/root/miniconda3/bin/python
    # 如果指定编译器,则可通过./test来执行，否则只能通过python test来执行
    # run(['mkdir','-p','11'])
    ret = run('ps -ef|grep python', shell=True, stdout=PIPE, stderr=PIPE)  # 当前进程的子进程运行命令
    print(f'pid: {os.getpid()}, args: {ret.args}, returncode: {ret.returncode}, stderr: {ret.stderr}')
    for line in ret.stdout.strip().split(b'\n'):
        print(line)


def open_tutorial():
    """
    r: read, default
    w: write
    b: binary
    a: append
    r +: 从头开始读, 从头开始往后覆盖
    w +: 读写, 注意其w特性
    a +: 从头读, 追加写
    """
    # 读取非UTF-8文件,要给open传入encoding参数,例如读取GBK文件
    # 遇到编码不规范的文件,会提示UnicodeDecodeError,errors参数表示如果遇到编码错误后如何处理,最简单的方式是直接忽略
    with open('/Users/michael/test.txt', 'r', encoding='gbk', errors='ignore') as file:
        for line in file:  # 无需各种read()函数
            print(line)

    with open('log1') as file1, open('log2') as file2:  # 同时打开多个
        # read: 按指定大小读取文件内容,以字符串形式返回
        # readline: 一次读取一行,以字符串形式返回
        # readlines: 将文件的所有行读取为一个列表,每一行作为列表中的一个元素
        print(list(file1))  # 等价于file1.readlines()
        file2.seek(33)
        print(file2.tell())
        print(file2.readline())


def unpack_tutorial():  # 解包
    arg0, (arg1, arg2), arg3 = [1, (2, 3), 4]  # 1 2 3 4
    arg4, *arg5, arg6 = [1, 2, 3, 4, 5]  # 1 [2, 3, 4] 5
    arg7 = [*range(5)]


def arguments_tutorial():
    def test_keywords(name, age, gender):  # 关键字参数/解包参数调用函数(可通过keyword=value形式调用函数,参数顺序无所谓)
        print('name:', name, 'age:', age, 'gender:', gender)

    test_keywords('Jack', 20, 'man')
    test_keywords(*['Jack', 20, 'man'])
    test_keywords(gender='man', name='Jack', age=20)
    # test_keywords(**{'Gender': 'man', 'name': 'Jack', 'age': 20})  # Error,键必须与参数名相同
    test_keywords(*{'gender': 'man', 'name': 'Jack', 'age': 20})  # name: gender age: name gender: age
    test_keywords(**{'gender': 'man', 'name': 'Jack', 'age': 20})  # 解包字典,会得到一系列key=value,本质上是使用关键字参数调用函数

    def test_variable(first_key, *args, **kwargs):  # 在形参前加一个*或**来指定函数可以接收任意数量的实参,位置参数必须在关键字参数之前
        print(first_key, type(args), args, type(kwargs), kwargs)

    test_variable(1, *[2, 3], c=4, d=5, **{'e': 6})  # 1 <class 'tuple'> (2, 3) <class 'dict'> {'c': 4, 'd': 5, 'e': 6}

    number = 5

    def test_default(element, num=number, /, *, arr=[], arr1=None):
        """
        positional only argument(/): 前面的参数必须是位置参数
        keyword only argument(*): 后面的参数必须是关键字参数
        默认值在函数定义时已被确定,如果默认值是一个可变对象如列表,字典,大多类对象时,函数在随后调用中会累积参数值
        """
        arr.append(element)
        if arr1 is None:  # 防止默认值在不同子调用间被共享
            arr1 = []
        arr1.append(element)
        print(num, arr, arr1)

    number = 6
    test_default(1)  # 5 [1] [1]
    test_default(2)  # 5 [1, 2] [2]

    def read_items(*, item_id: int = 12, q: str):  # 如果希望默认值参数后面接非默认值参数,第一个参数需要是*
        print({"item_id": item_id, 'q': q})


def delayed_binding_tutorial():
    # 延迟绑定出现在闭包问题和lambda表达式中, 特点是变量在调用时才会去检测是否存在, 如果存在则使用现有值, 如果不存在, 直接报错
    # 对于lambda表达式来说y不是局部变量,it is accessed when the lambda is called — not when it is defined
    squares = [lambda: x ** 2 for x in range(3)]  # 会立马执行for循环
    for square in squares:
        print(square())  # 4 4 4

    squares = (lambda: x ** 2 for x in range(3))  # generator,并不会立马执行for循环
    for square in squares:
        print(square())  # 0 1 4

    squares = [lambda y=x: y ** 2 for x in range(3)]  # lambda参数也可以有默认值
    for square in squares:
        print(square())  # 0 1 4


def datetime_tutorial():
    print(datetime.now())  # 获取的是本地时间
    print(datetime.now().date())
    print(datetime.now().time())
    print(datetime.now().weekday())
    print(datetime.now().year)
    print(datetime.now().month)
    print(datetime.now().strftime('%Y-%m-%d'))  # <class 'str'>
    print(datetime.now() - timedelta(days=2))  # weeks,minutes
    print(datetime.strptime('2016-9-9 18:19:59', '%Y-%m-%d %H:%M:%S'))  # <class 'datetime.datetime'>
    print(datetime.fromtimestamp(time.time()))  # 2020-08-12 15:48:21.636170
    _ = datetime(2020, 10, 9, 11, 12, 13)  # 2020-10-09 11:12:13, time.time受系统时间影响

    time.monotonic()  # 不区分线程进程,按调用顺序递增,以小数秒为单位,时钟不受系统时钟更新的影响,只有两次调用结果之间的差值才有效


def heap_tutorial():
    heap = [3, 54, 64, 4, 34, 24, 2, 4, 24, 33]
    heapify(heap)  # 小顶堆,没有大顶堆
    print(heap)
    print([heappop(heap) for _ in range(len(heap))])  # 此时heap为空

    h = []
    heappush(h, (3, 'create tests'))
    heappush(h, (5, 'write code'))
    heappush(h, (7, 'release product'))
    heappush(h, (1, 'write spec'))
    print(h)
    print(nsmallest(3, h))
    print(nlargest(2, h))
    print(heappushpop(h, (4, 'for tests')))
    print(h[0])  # 查看堆中最小值，不弹出
    print(heappop(h), h)


def sort_tutorial():
    """
    if you don’t need the original list, list.sort is slightly more efficient than sorted.
    By default, the sort and the sorted built-in function notices that the items are tuples, so it sorts on the first element first and on the second element second.
    """
    items = [(1, 'B'), (1, 'A'), (2, 'A'), (0, 'B'), (0, 'a')]
    sorted(items)  # [(0, 'B'), (0, 'a'), (1, 'A'), (1, 'B'), (2, 'A')]
    sorted(items, key=lambda x: (x[0], x[1].lower()))  # [(0, 'a'), (0, 'B'), (1, 'A'), (1, 'B'), (2, 'A')]
    peeps = [
        {'name': 'Bill', 'salary': 1000},
        {'name': 'Bill', 'salary': 500},
        {'name': 'Ted', 'salary': 500}
    ]
    # [{'salary': 500, 'name': 'Bill'}, {'salary': 1000, 'name': 'Bill'}, {'salary': 500, 'name': 'Ted'}]
    sorted(peeps, key=lambda x: (x['name'], x['salary']))
    # [{'salary': 1000, 'name': 'Bill'}, {'salary': 500, 'name': 'Bill'}, {'salary': 500, 'name': 'Ted'}]
    sorted(peeps, key=lambda x: (x['name'], -x['salary']))


def sum_tutorial():
    arr = [[1, 2], [3, 4], [5, 6]]
    _ = sum(arr, [])  # [1, 2, 3, 4, 5, 6]  sum第二个参数默认为0
    sum(_)  # 21


def isinstance_tutorial():
    # isinstance(object,class)    判断对象object是不是类class或其派生类的实例
    # issubclass(class ,baseclass) 判断一个类是否是另一个类的子类
    class Person: pass

    class Student(Person): pass

    person = Person()
    student = Student()
    assert isinstance(person, Person)
    assert not isinstance(person, Student)
    assert isinstance(student, (Student, Person))
    assert issubclass(Student, Person)


def cache_tutorial():
    """
    maxsize代表能缓存几个函数执行结果,当超过限制时会删除最久一次未使用的元素
    typed代表参数类型改变时是否重新缓存
    记忆确定性的函数,因为它总是会为相同的参数返回相同的结果
    """

    @lru_cache(maxsize=100, typed=True)
    def fib(number: int) -> int:
        print(number, end='\t')
        if number < 2:
            return number
        return fib(number - 1) + fib(number - 2)

    print(fib.cache_info())  # CacheInfo(hits=0, misses=0, maxsize=100, currsize=0)
    print(f'answer: {fib(10)}')  # 10   9   8   7   6   5   4   3   2   1   0   answer: 55
    print(fib.cache_info())  # CacheInfo(hits=8, misses=11, maxsize=100, currsize=11) hits表示缓存命中次数
    print(f'answer: {fib(10)}')  # answer: 55
    print(fib.cache_info())  # CacheInfo(hits=9, misses=11, maxsize=100, currsize=11)
    fib.cache_clear()
    print(fib.cache_info())  # CacheInfo(hits=0, misses=0, maxsize=100, currsize=0)


def random_tutorial():
    # random是伪随机, 默认随机数生成种子是从 /dev/urandom或系统时间戳获取, 所以种子肯定不会是一样的
    print(random.random())  # 随机生成一个[0,1)范围内实数
    print(random.randrange(1, 10, 2))  # 从range(start, stop[, step])范围内选取一个值并返回(不包含stop)
    arr = [1, 2, 3, 4, 5, 6, 6, 6, 6]
    print(random.choice(arr))  # 返回一个列表,元组或字符串的随机项
    print(random.sample(arr, 3))  # 返回列表指定长度个不重复位置的元素
    random.shuffle(arr)  # 方法将序列的所有元素随机排序
    print(arr)


var = 0


def scope_tutorial():
    # 变量引用顺序: 当前作用域局部变量->外层作用域变量->当前模块中的全局变量->python内置变量
    # global: 在局部作用域中修改全局变量
    # nonlocal: 在局部作用域中修改外层非全局变量
    def make_counter():
        count = 0

        def counter():
            nonlocal count
            count += 1
            return count

        return counter

    mc = make_counter()
    print(mc(), mc(), mc())  # 1,2,3

    def outer():
        var = 1

        def inner():
            # nonlocal var # inner: 9 outer: 9 global: 0
            # global var   # inner: 9 outer: 1 global: 9
            var = 2
            var += 7
            print("inner:", var, end='\t')

        inner()
        print("outer:", var)

    outer()  # inner: 9	outer: 1
    print("global:", var)  # global: 0
    print(locals())  # {'make_counter': make_counter at 0x1>, 'mc': <function at 0x2>, 'outer': <function at 0x3>}
    # {'__name__': '__main__', '__file__': '11.py', 'var': 0, 'scope_tutorial': <function scope_tutorial at 0x1>}
    print(globals())


def property_tutorial():
    class C:
        def __init__(self):
            self.__x = None

        def get_x(self):
            print('get_x')
            return self.__x

        def set_x(self, value):
            print('set_x')
            self.__x = value

        def del_x(self):
            print('del_x')
            del self.__x

        x = property(get_x, set_x, del_x, "I'm the 'x' property.")  # 把类中的方法当作属性来访问

    c = C()
    c.x = 20  # 相当于c.set_x(20)
    print(c.x)  # 相当于c.get_x()
    del c.x  # 相当于c.del_x()


def regular_tutorial():
    """
    search: 最多只匹配一个, 可指定起始位置跟结束位置
    findall: 匹配所有, 可指定起始位置跟结束位置
    sub: 替换每一个匹配的子串, 返回替换后的字符串.若找不到匹配, 则返回原字符串,可以指定最多替换次数
    subn: 同sub, 返回(sub函数返回值, 替换次数)
    split: 将字符串以匹配的字符做切分

    * 匹配前一个字符0或无限次
    + 匹配前一个字符1或无限次
    ? 匹配前一个字符0次或1次
    {m} 匹配前一个字符m次
    {m,n} 匹配前一个字符m次至n次,若省略m代表m=0,若省略n代表n=∞
    . 匹配任意除换行符\n外的字符
    \ 转意字符,使后一个字符变为普通字符
    [] 匹配所包含的任意一个字符,特殊字符(除[,],^,-)都会变为普通字符,第一个字符如果是^则表示取反,-出现在字符串中间表示字符范围,如[^a-c]表示不是abc的其他字符
    ^ 如果出现在首位则表示匹配字符串开头,多行模式中匹配每一行的开头
    $ 如果出现在末尾则表示匹配字符串末尾,多行模式中匹配每一行的末尾
    | 字符串从左到右开始遍历,一旦匹配到左右表达式中的一个则停止,如果|没有被包括在()中, 则它的范围是整个正则表达式
    () 被括起来的表达式将作为分组,作为一个整体可以后接数量词
    \number 引用编号为number的分组匹配到的字符串,默认从1开始
    (?:...) (...)的不分组版本,用于使用|或后接数量词
    (?=...) 之后的字符串需要匹配表达式才能成功匹配,不消化字符串内容
    (?!...) 之后的字符串需要不匹配表达式才能成功匹配,不消化字符串内容
    (?<=...) 之前的字符串需要匹配表达式才能成功匹配,不消化字符串内容
    (?<!...) 之前的字符串需要不匹配表达式才能成功匹配,不消化字符串内容

    注意:
    使用*?,+?,??,{m,n}?后会由贪婪模式变为非贪婪模式
    慎用\w,\d,\s,\W,\D,\S之类的特殊字符
    r'^[a-zA-Z0-9]+$'  # 匹配全部由数字字母组成的字符串
    正则串建议使用r串
    compile内部也会有缓存,因此少量正则匹配不需要compile,refer: https://github.com/python/cpython/blob/main/Lib/re/__init__.py#L262
    [\u4e00 -\u9fa5] 匹配中文
    """
    s = 'avatar cao nihao'
    regex = r'(ava[a-z]+) cao (nihao)'
    print(re.search(regex, s).group())  # avatar cao nihao, group默认是group(0),返回全部
    print(re.search(regex, s).groups())  # ('avatar', 'nihao'), groups是以tuple类型返回括号内所有内容
    s = 'avatar cao avast cao'
    print(re.findall(r'(ava[a-z]+) cao', s))  # ['avatar', 'avast']
    print(re.findall(r'ava[a-z]+ cao', s))  # ['avatar cao', 'avast cao']
    print(re.sub(r"like", r"love", "I like you, do you like me?"))  # I love you, do you love me?
    print(re.subn(r'([a-z]+) ([a-z]+)', r'\2 \1', 'i say, hello world!'))  # ('say i, world hello!', 2)
    print(re.split(r'[ ,;]+', 'a,b;; c d'))  # ['a', 'b', 'c', 'd']

    s = '[q\w1'  # r串的使用
    re.findall(r'\[q\\w1', s)  # ['[q\\w1']
    re.findall('\[q\\w1', s)  # [],匹配不到的原因是python字符串也用\转义特殊字符,\[被理解成[
    re.findall('\\[q\\\w1', s)  # ['[q\\w1']

    print(re.findall(r'ab(?:.|\n)+bc', 'ab\nbc'))  # ['ab\nbc'], ?:意思是让findall,search等函数'看不见'括号
    print(re.findall(r'(?:[0-9]{1,3}\.){3}[0-9]{1,3}', '192.168.1.33'))  # ['192.168.1.33']
    print(re.findall(r'\w+\.(?=c.m)', 'www.com https.org'))  # ['www.']
    print(re.findall(r'\w+\.(?!com)\w+', 'www.com https.org'))  # ['https.org']
    print(re.findall(r'(?<=\w{5})\.\w+', 'www.com https.org'))  # ['.org']
    print(re.findall(r'\w+(?<!www)\.\w+', 'www.com https.org'))  # ['https.org']

    print(re.findall(r"ab.+bc", "ab\nbc"))  # []
    print(re.findall(r"Ab.+bc", "ab\nbc", re.S | re.I))  # ['ab\nbc'], re.S可以使.匹配换行符\n,re.I忽略大小写
    print(re.findall(r"^[a-z]+", "ab\nbc"))  # ['ab']
    print(re.findall(r"^[a-z]+", "ab\nbc", re.M))  # ['ab', 'bc'], re.M：可以使^$标志将会匹配每一行,默认^和$只会匹配第一行
    print(re.findall(r"[a-z]+", "ab\nbc"))  # ['ab', 'bc'], 如果没有^标志,是无需re.M


def method_tutorial():
    """
    静态方法和类方法都可以用类或者类实例调用,都可以被继承,不能访问实例属性,可以访问类属性
    类方法第一个参数必须是cls,它是一个object that holds class itself,不是类实例,静态方法可以没有参数
    """

    class Date:
        def __init__(self, day=0, month=0, year=0):
            self.day = day
            self.month = month
            self.year = year

        @classmethod
        def from_string(cls, date_as_string):
            day, month, year = map(int, date_as_string.split('-'))
            return cls(day, month, year)

        '''
        The same can be done with @staticmethod as is shown in the code below
        the Factory process is hard-coded to create Date objects.
        What this means is that even if the Date class is subclassed, 
        the subclasses will still create plain Date object (without any property of the subclass).
        '''

        @staticmethod
        def s_from_string(date_as_string):
            day, month, year = map(int, date_as_string.split('-'))
            return Date(day, month, year)

        '''
        We have a date string that we want to validate somehow. 
        This task is also logically bound to Date class we've used so far, but still doesn't require instantiation of it.
        Often there is some functionality that relates to the class, but does not need the class or any instance(s) to do some work.
        Perhaps something like setting environmental variables, changing an attribute in another class, etc.
        In these situation we can also use a function, however doing so also spreads the interrelated code which can cause maintenance issues later.
        '''

        @staticmethod
        def is_date_valid(date_as_string):
            day, month, year = map(int, date_as_string.split('-'))
            return day <= 31 and month <= 12 and year <= 3999

    _ = Date.from_string('11-09-2012')
    print(Date.is_date_valid('11-09-2012'))


def decorator_tutorial():  # 装饰器,被装饰对象都可以是函数或者类
    def non_parameter_decorator(func):
        count = 0  # 计数

        def decorator(*args, **kwargs):
            nonlocal count  # 注意这里要用nonlocal
            count += 1
            print(f"第{count}次调用,", end="")
            ret = func(*args, **kwargs)
            print(f"result: {ret}")
            return ret  # 内嵌包装函数的形参和返回值与原函数相同

        return decorator  # 装饰函数返回内嵌包装函数对象

    @non_parameter_decorator  # 相当于non_parameter_test=non_parameter_decorator(non_parameter_test)
    def non_parameter_test(a, b):
        return a + b

    non_parameter_test(4, 5)  # 第1次调用,result: 9
    non_parameter_test(6, 7)  # 第2次调用,result: 13

    ###################################################################################################
    def parameter_decorator(text):  # 带参数装饰器相比于不带参数装饰器,在最外层多了一层包装
        def outer(func):
            @wraps(func)
            def inner(*args, **kwargs):
                print(f'text: {text}, function name: {func.__name__}')
                return func(*args, **kwargs)

            return inner

        return outer

    @parameter_decorator('test')  # 相当于today=parameter_decorator('test')(today)
    def today(): pass

    today()  # text: test, function name: today
    print(today.__name__)  # today,如果不用wraps装饰则会返回inner

    ###################################################################################################
    # using classes as decoration mechanisms instead of functions,In addition, it's more powerful.
    # which basically means it must be callable. Thus, any classes we use as decorators must implement __call__.
    class NonParameterDecorator:
        def __init__(self, func):
            self.func = func

        def __call__(self, *args, **kwargs):
            print("function name: ", self.func.__name__)
            ret = self.func(*args, **kwargs)
            return ret

    @NonParameterDecorator  # 等价于class_non_parameter_test=NonParameterDecorator(class_non_parameter_test)
    def class_non_parameter_test(): pass

    class_non_parameter_test()
    print(type(class_non_parameter_test))  # <class '__main__.decorator_tutorial.<locals>.NonParameterDecorator'>

    ###################################################################################################
    # 如果有装饰器参数,构造函数不再接收被装饰函数,而是捕获装饰器参数,__call__不能再用作装饰函数调用,必须改为使用__call__来执行装饰
    class ParameterDecorator:
        def __init__(self, parameter):
            self.parameter = parameter

        def __call__(self, func):  # 它只有一个参数，即函数对象
            print("in __call__")

            def wrapper(*args, **kwargs):
                print("decorator parameter: ", self.parameter)
                ret = func(*args, **kwargs)
                return ret

            return wrapper

    @ParameterDecorator("hi")  # in __call__, 等价于class_parameter_test=ParameterDecorator("hi")(class_parameter_test)
    def class_parameter_test(): pass

    class_parameter_test()

    ###################################################################################################
    def decorator_a(func):
        print('start in decorator_a')

        def inner_a(*args, **kwargs):
            print('start in inner_a')
            func(*args, **kwargs)
            print('end in inner_a')

        print('end in decorator_a')
        return inner_a

    def decorator_b(func):
        print('start in decorator_b')

        def inner_b(*args, **kwargs):
            print('start in inner_b')
            func(*args, **kwargs)
            print('end in inner_b')

        print('end in decorator_b')
        return inner_b

    @decorator_b
    @decorator_a
    def decorator_order_test():
        print('start in decorator_order_test')

    decorator_order_test()
    # start in decorator_a           装饰时打印
    # end in decorator_a             装饰时打印
    # start in decorator_b           装饰时打印
    # end in decorator_b             装饰时打印
    # start in inner_b               调用时打印
    # start in inner_a               调用时打印
    # start in decorator_order_test  调用时打印
    # end in inner_a                 调用时打印
    # end in inner_b                 调用时打印


def iterable_tutorial():
    """
    定义了__iter__方法的对象是Iterable类型,可作为iter的入参
    定义了__next__方法的Iterable类型,或iter(Iterable)方式生成的对象是Iterator类型,可作为next的入参,终止时抛出StopIteration异常
    包含yield关键字的函数实例或括号列表推导式产生的对象是Generator类型
    Generator是Iterator子集,Iterator是Iterable子集
    Iterator执行完next()后,该方法的上下文(变量)环境消失;Generator执行完next()后,代码会执行到yield处,并将yield后的值返回,同时该方法的上下文(挂起位置,变量等)会被保留
    """

    for _ in [1, 2, 3, 4, 5]:  # for本质
        pass
    # 等价于
    it = iter([1, 2, 3, 4, 5])
    while True:
        try:
            _ = next(it)  # 获得下一个值
        except StopIteration:
            break

    class SelfIterator:
        def __init__(self, data):
            self.data = data
            self.index = len(data)

        def __iter__(self):  # 保证iter(Iterator)如for循环等操作返回其自身
            return self

        def __next__(self):
            if self.index:
                self.index -= 1
                return self.data[self.index]
            raise StopIteration

    iterator = SelfIterator('maps')
    for it in iterator:
        print(it, end='')  # spam
    print()

    def fibonacci_sequence():
        a, b = 0, 1
        print("start")
        while True:
            a, b = b, a + b
            print("before-yield")
            yield a
            print("after-yield")

    generator_f = fibonacci_sequence()  # <class 'generator'>,协程预激活,未执行任何fibonacci_sequence代码
    for gen in generator_f:
        print(gen)
        if gen >= 2:
            break
    """
    start before-yield 1
    after-yield before-yield 1
    after-yield before-yield 2
    """
    assert not isinstance(100, Iterable)

    assert isinstance([], Iterable)
    assert not isinstance([], Iterator)
    assert isinstance(iter([]), Iterable)
    assert isinstance(iter([]), Iterator)

    assert isinstance(generator_f, Iterable)
    assert isinstance(generator_f, Iterator)
    assert isinstance(generator_f, Generator)
    assert isinstance((_ for _ in range(5)), Generator)


def log_tutorial():
    # logger是全局对象,配置一次全局生效,最好是放在主程序最开始的位置,尤其要在任何日志输出语句之前调用logger.add()
    # 默认情况下日志打印到屏幕,日志级别为WARNING
    # 日志级别：CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET
    logger.add(
        sink="loguru.log",  # 日志写入文件,默认还会输出到控制台
        rotation="500 MB",  # 当日志文件达到一定大小、时间或者满足特定条件时,自动分割日志文件
        level="INFO",  # 只记录INFO及以上级别的日志
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {module} | {function}:{line} | PID={process.id} | {message}",
        filter=lambda record: "特殊字符" in record["message"],
        # 只记录日志中包含"特殊字符"这四个字的日志, 这里record是个字典,为了方便观察,可设置serialize=True,record就是每行日志的["record"]值
        serialize=True,  # 将每行日志转换为json格式,包含了日志对应的进程id信息
        enqueue=True,  # 所有添加到日志记录器的接收器默认都是线程安全,它们并非多进程安全,但您可以将消息入队列以确保日志的完整性和异步写入
    )
    logger.info("That's it, beautiful and simple logging!")
    logger.info("特殊字符,That's it, beautiful and simple logging!")
    another_logger = logger.bind(name="支付模块")  # 相当于record["extra"]["name"] = 支付模块,并不改变日志的文本输出和控制台输出逻辑
    another_logger.warning("特殊字符,That's it, beautiful and simple logging!")


class PickleTutorial:
    def __reduce__(self):
        return run, (("ls", "-lh"),)  # pickle预留,允许用户自定义反序列化复杂object的方法,反序列化用户不用导入subprocess,危险


def pickle_tutorial():
    # 除个别外(如不能序列化lambda表达式,线程锁), pickle.dumps可以序列化任何数据类型成b字符串,并保留原有的数据(比如生成好的树,图结构)
    # pickle.loads反序列化后的对象与原对象是等值的副本对象, 类似与deepcopy
    # pickle模块并不安全,你只应该对你信任的数据进行unpickle操作
    # dill完全兼容pickle,dumps,loads用法一样,但能序列化更多的python对象(如lambda表达式)
    with open("data", "wb") as f:
        f.write(pickle.dumps(tuple_tutorial))
    with open("data", "rb") as f:
        func = pickle.loads(f.read())
        func()

    pickle_obj_byte = pickle.dumps(PickleTutorial())
    _ = pickle.loads(pickle_obj_byte)


def inherit_tutorial():
    # MRO全称Method Resolution Order,用来定义继承方法的调用顺序
    # super是一个类,第一个参数决定从它后面第一个类开始找,而不是父类的方法(还有可能代理其兄弟类),第二个参数决定使用哪个类的mro
    # 在继承中一旦定义了子类的构造函数,则需要在第一行显示调用基类的构造函数super().__init__()
    class A:  # 模拟object类
        def __init__(self):
            print('init A')

    class B(A):
        def __init__(self):
            # 如果实例化B,等价于A.__init__(self),self是B的实例;如果实例化D,等价于C.__init__(self),self是D的实例
            super().__init__()  # 等价于super(B,self).__init__()
            print('init B')

        def hello(self):
            print("hello B")

    class C(A):
        aa, __bb = [1, 3]  # 私有变量__bb不会被继承和覆盖,编译的时候已经改名(name mangling)

        def __init__(self):
            super().__init__()
            print('init C')

        def hello(self):
            print("hello C")

        def print(self):
            print("print C", self, self.aa, self.__bb)  # self.__bb会被解释称self._C__bb

    class D(B, C):
        aa, __bb = [2, 4]

        def __init__(self):
            super().__init__()
            print('init D')

        def print(self):
            super().print()
            print("print D", self, self.aa, self.__bb)

    # [<class '__main__.D'>, <class '__main__.B'>, <class '__main__.C'>, <class '__main__.A'>, <class 'object'>]
    print(D.mro())
    print(B.mro())  # [<class '__main__.B'>, <class '__main__.A'>, <class 'object'>]
    print(A.mro())  # [<class '__main__.A'>, <class 'object'>]
    D().hello()  # 按照mro顺序,找到第一个hello函数执行,寻找变量也是相同逻辑
    # init A
    # init C
    # init B
    # init D
    # hello B
    D().print()
    # print C <__main__.D object at 0x10c5dc190> 2 3
    # print D <__main__.D object at 0x10c5dc190> 2 4
    B()
    # init A
    # init B


def frame_tutorial():
    def parent(a=1):
        b = [2]
        son()

    def son():
        # 每个函数编译期间会编译出一个code object, 每次调用时会产生一个新的frame
        frame = inspect.currentframe()
        print(frame.f_code.co_name)  # son,当前函数名
        print(frame.f_back.f_code.co_name)  # parent,父函数名
        print(frame.f_back.f_locals)  # {'a': 1, 'b': [2], 'son': <function son>},父函数局部变量
        whereis = f"{frame.f_back.f_code.co_filename} at line {frame.f_back.f_lineno}"
        print(whereis)  # 调用该函数的文件路径名 + 代码在该文件在行,方便调试,还可以递归打印二叉树路径

    parent()


def float_tutorial():
    """
    c语言中浮点数在内存分布如下:
    float    符号位1比特    指数位8比特    尾数位23比特
    double   符号位1比特    指数位11比特   尾数位52比特
    整数转换成补码再写入内存,浮点数直接写入内存
    浮点数被存储之前,先转换为a*(2**n)的二进制形式,其中1<=a<2,n是指数
    浮点数的精度由尾数位长度决定,float精度为6~7位有效数字(2**23=8388608),double精度为15~16位有效数字(2**52=4503599627370496)
    float取值范围(-2**128 ~ 2**128),double取值范围(-2**1024 ~ 2**1024),此处的128由255-127得到
    例如float类型19.625 = 10011.101 = 1.0011101 * 2**4, 对应a=1.0011101, n=4
    二进制小数部分(0011101)放入内存中的尾数位,当小数过长时,多出的位数会被直接截去
    二进制整数部分都是1,无需在内存中体现出来,所以直接截去,只把指数4+127=131=0b10000011放入内存中的指数位,加127是应为指数可能为负
    二进制符号位为正,所以把0放入内存符号部分
    综上所述,float类型19.625在内存以0 10000011 00111010000000000000000
    """
    wanted_value = 0b01000001100111010000000000000000
    test_float = ctypes.c_float(19.625)
    assert struct.unpack("<I", test_float)[0] == wanted_value  # 说明整数在c语言中以小端模式存储
    assert struct.unpack(">I", struct.pack(">f", test_float.value))[0] == wanted_value  # 保证pack和unpack模式顺序一致即可

    wanted_value = 0b11000011000000000001100111011011
    test_float = ctypes.c_float(-128.101)  # 对应二进制小数为(-1)*1.00000000001100111011011001000101101*2**7
    assert struct.unpack("<I", test_float)[0] == wanted_value  # 说明多出的小数部分被截去


def metaclass_tutorial():
    # class B: pass 等价于 B = type('B', (), {})
    class M(type):
        def __new__(cls, name, bases, _dict):
            # in M's new <class '__main__.M'> A () {'__module__': '__main__', '__qualname__': 'A'}
            print("in M's new", cls, name, bases, _dict)  # 也可以放在init里面,但这里执行更高效
            for key in _dict:
                if key.startswith("test_"):
                    raise ValueError()
            return type.__new__(cls, name, bases, _dict)

        def __init__(cls, name, bases, _dict):
            # in M's init <class '__main__.A'> A () {'__module__': '__main__', '__qualname__': 'A'}
            print("in M's init", cls, name, bases, _dict)
            cls.random_id = random.randrange(0, 10, 1)
            type.__init__(cls, name, bases, _dict)

        def __call__(cls, *args, **kwargs):  # 可实现单例功能
            print("in M's call", cls, args, kwargs)  # in M's call <class '__main__.A'> (1,) {'b': 2}
            return type.__call__(cls, *args, **kwargs)

    class A(metaclass=M):  # 等价于A=M('A',(),{}),会先调用M的new函数,此时A已经是M的一个实例,再调用init函数
        def __init__(self, a, b):
            self.a = a
            self.b = b

        # def test_new(self): pass  # error

    print(A.random_id)
    test = A(1, b=2)  # 调用元类M的call函数
    print(test.random_id, test.a, test.b)


class Singleton(type):
    _instance = None
    _instance_lock = Lock()

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._instance_lock:  # 线程安全单例模式
                if cls._instance is None:
                    cls._instance = type.__call__(cls, *args, **kwargs)
        return cls._instance


def singleton(cls):
    _instance_pool = {}
    _instance_lock = Lock()

    def _singleton(*args, **kwargs):
        _kwargs = {_key: kwargs[_key] for _key in sorted(kwargs)}
        hash_key = f"{args}:{_kwargs}"
        if hash_key not in _instance_pool:
            with _instance_lock:  # 线程安全单例池
                if hash_key not in _instance_pool:
                    _instance_pool[hash_key] = cls(*args, **kwargs)
        return _instance_pool[hash_key]

    return _singleton


def singleton_tutorial():
    class TestSingleton(metaclass=Singleton):  # 继承了元类的_instance和_instance_lock
        def __init__(self):
            print("init TestSingleton instance")

    @singleton
    class TestSingleTonPool:
        def __init__(self, *args, **kwargs):
            print(f"args:{args},kwargs:{kwargs},init TestSingleTonPool instance")

    assert TestSingleton() is TestSingleton()
    assert TestSingleTonPool(1, "2", c=2.4, d="d") is TestSingleTonPool(1, "2", c=2.4, d="d")
    assert TestSingleTonPool() is TestSingleTonPool()


def sqlite_tutorial():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    # sql = "select name from sqlite_master where type='table' order by name"  # 查看表名
    # sql = f"SELECT sql FROM sqlite_master WHERE type='table' AND name='user'" # 查看建表语句
    sql = "select * from user"
    cursor.execute(sql)
    result = cursor.fetchall()
    pd.DataFrame(result)


def match_tutorial():
    # _ 是默认分支
    status = 404
    match status:
        case 200:
            print("OK")
        case 404:
            print("Not Found")
        case _:
            print("Unknown")

    # 这里point按顺序依次与每个case比较,匹配成功后执行对应代码,不需要break
    point = (0, 0)
    match point:
        case (x, 0):
            print(f"On X-axis at {x}")
        case (0, 0):
            print("Origin")
        case (0, y):
            print(f"On Y-axis at {y}")
        case _:
            print("Error")

    lst = [1, 2]
    match lst:
        case []:
            print("空列表")
        case [x]:
            print(f"只有一个元素: {x}")
        case [x, y]:
            print(f"两个元素: {x}, {y}")
        case [x, *rest]:
            print(f"第一个元素是 {x}，其余是 {rest}")


async def playwright_tutorial():
    async def handle_request(request):
        print("handle_request", request.url, request.method)

    async def handle_response(response):
        print("handle_response", response.url, response.status)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-infobars',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--start-maximized'
            ]
            # channel='chrome',  # 使用本机安装的Chrome,而不是内置的Chromium
        )
        context = await browser.new_context()  # 相当于一个新窗口,有独立的cookies、localStorage等
        page = await context.new_page()
        page.on("request", handle_request)  # 每次浏览器发起网络请求时触发,用于监听请求
        page.on("response", handle_response)  # 每次浏览器收到响应时触发,用于监听响应
        await page.goto("http://i.qq.com/")
        content = await page.content()
        cookies = await context.cookies()  # 获取当前context中的所有cookies(必须时可以按domain过滤cookie)
        # cookies = await page.context.cookies() # 获取当前context中的所有cookies,仅在没有context对象时使用
        await page.screenshot(path='3658.png')  # 还支持录视频
        frame = page.frame(name="login_frame")  # 切换到iframe
        await frame.click('#switcher_plogin')
        await frame.fill('#u', '212956')
        await frame.fill('#p', 'pass')
        await frame.click('#login_button')
        await page.wait_for_timeout(2000)  # 等待2s内容加载
        # 滚动页面到最底部，然后再滚回顶部
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")  # 整个页面即document上执行JS
        await page.evaluate("window.scrollTo(0, 0);")
        # 在页面中找到某个元素,然后在这个元素上运行一段js代码,并返回结果
        qrcode = await page.eval_on_selector("#animate_qrcode_container img", "el => el.src")
        await page.close()
        await browser.close()


if __name__ == "__main__":  # import到其他脚本中不会执行以下代码,此时__name__为不含后缀的脚本名,spawn方式的多进程也需要
    # frame_tutorial()
    # arguments_tutorial()
    # list_tutorial()
    # is_tutorial()
    # str_tutorial()
    # subprocess_tutorial()
    # dict_tutorial()
    # iterable_tutorial()
    # common_tutorial()
    # inherit_tutorial()
    # metaclass_tutorial()
    # pickle_tutorial()
    # singleton_tutorial()
    # isinstance_tutorial()
    # with_tutorial()
    # variable_tutorial()
    # float_tutorial()
    # match_tutorial()
    exception_tutorial()
