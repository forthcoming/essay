"""
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


Python运行时不强制执行函数和变量类型注解, 但这些注解可用于类型检查器、IDE、静态检查器等第三方工具
常见注解:
list[float]
dict[str, str | int]
-> None
tuple[str, int, bool]
tuple[float, ...]
int | str
value: int = 3


compiler是将编程语言翻译成01机器语言的软件
interpreter是将编程语言一行行翻译成01机器语言的软件
python属于解释性语言


__init__.py
主要作用是将文件夹变为一个Python模块, 我们在python中导入一个包时, 实际上是导入了它的__init__.py文件
被导入的文件中的全局代码, 类静态区都会被执行

变量sys.path是一个字符串列表, 它为解释器指定了模块的搜索路径,包括 当前程序所在目录、标准库的安装目录、操作系统环境变量PYTHONPATH所包含的目录
vim ~/.bashrc  # vim /etc/profile 全局
export PYTHONPATH=$PYTHONPATH:/root/Desktop/atlas
source ~/.bashrc

import sys
sys.path.append('/root/Desktop')   # 添加python查询路径


原码 & 补码
原码: 用最高位表示符号位, 1表示负, 0表示正, 其他位存放该数的二进制的绝对值
补码: 正数的补码等于他的原码, 负数的补码等于正数的原码取反加一
计算机存的是补码
-5转化为补码: (0b00000101 ^ 0xff) + 1 = > 0b11111011
0b11111011转化为整数: -((0b11111011 ^ 0xff) + 1) = > -5


and, or, not
x and y返回的结果是决定表达式结果的值
如果x为真, 则y决定结果, 返回y; 如果x为假, x决定了结果为假, 返回x
x or y返回的结果是决定表达式结果的值
not 返回表达式结果的相反的值, 如果表达式结果为真则返回false, 如果表达式结果为假则返回true

关系运算符
以下为True
(1, 2, 3) < (1, 2, 4))
[1, 2, 3] < [1, 2, 4]
'ABCD' < 'bar' < 'bloom'
(1, 2, 3, 4) < (1, 2, 4)
(1, 2) < (1, 2, -1)
(1, 2, ('aa', 'ab')) < (1, 2, ('abc', 'a'), 4)
以下为False
{1} < {2}
{2} < {1}


is和==区别
x = y = [4, 5, 6]
z = [4, 5, 6]
x == y  # True
x == z  # True
x is y  # True
x is z  # False
print(id(x), id(y), id(z))  # 1685786989512 1685786989512 1685786991112
is比较的内存地址; ==比较的是字面值
元组的值会随引用的可变对象的变化而变, 元组中不可变的是元素的标识(id)


__str__: 自定义打印类的格式,print打印类实例时被调用
__len__: 自定义类长度,len作用于类实例时被调用
__call__: 类实例被当作函数调用时调用


class Person:
    def __init__(self, name):
        self.name = name

    def __call__(self, friend):
        print('My name is {},My friend is {}.'.format(self.name, friend))


p = Person('Bob')
p('Tim')  # My name is Bob,My friend is Tim.
"""

from functools import lru_cache
from datetime import datetime, timedelta
import time
from random import randrange, choice, sample, shuffle, random
from heapq import heapify, heappop, heappush, nlargest, nsmallest, heappushpop
from collections import Counter
from bisect import insort_right, bisect_left, bisect_right
from collections import deque
import re
import pandas as pd
import win32api
import win32con
import copy


def str_tutorial():
    # split
    string = "Line1-abcdef \nLine2-abc \nLine4-abcd"
    print(string.split())  # ['Line1-abcdef', 'Line2-abc', 'Line4-abcd']
    print(string.split(' ', 1))  # ['Line1-abcdef', '\nLine2-abc \nLine4-abcd']
    print(string.split(' '))  # ['Line1-abcdef', '\nLine2-abc', '\nLine4-abcd']
    # 应用: 去除字符串中空白符content =''.join(content.split())


def list_tutorial():
    # 列表切片赋值
    arr = [1, 2, 3, 4, 5]
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


def set_tutorial():  # 无序不重复, 添加元素用add
    # 区别于位运算符中的& ,| ,^和逻辑运算符 and or not
    set_a = {1, 2, 3, 3}
    set_b = {3, 4, 5, 6, 7}
    print(set_a == set_b)  # False
    print(set_a < set_b)  # False,set_a不是set_b的子集
    print(set_a | set_b)  # set([1, 2, 3, 4, 5, 6, 7])
    print(set_a & set_b)  # set([3])
    print(set_a - set_b)  # set([1, 2])
    print(set_b - set_a)  # set([4, 5, 6, 7])
    # (set_a ^ set_b) == ((set_a - set_b) | (set_b - set_a)),numbers in set_a or in set_b but not both
    print(set_a ^ set_b)  # set([1, 2, 4, 5, 6, 7])


def dict_tutorial():  # 字典有序
    d = {'a': 1, 'b': 2}
    d.update({'a': 3, 'c': 4})  # {'a': 3, 'b': 2, 'c': 4}
    print(d.pop('a', '无a'))  # 类似于get,3
    print(d.setdefault('d'))  # None
    print(d.setdefault('e', 'avatar'))  # avatar
    print(d.setdefault('b', 'akatsuki'))  # 2
    print(d)  # {'b': 2, 'c': 4, 'd': None, 'e': 'avatar'}

    one = {'a': 1, 'b': 2}
    two = {'a': 3, 'c': 2}
    _ = one | two  # {'a': 3, 'b': 2, 'c': 2},合并两个字典


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


def copy_tutorial():
    a = [0, [1, ], (2,), 'str']
    b = a  # 相当于&
    c = a[:]  # 等价于copy.copy(a),相当于部分&
    d = copy.copy(a)
    e = copy.deepcopy(a)  # 此时e跟a无任何关系
    a[0] = 5
    a[1][0] = 4
    print('a:', a)
    print('b:', id(b) == id(a), id(b[0]) == id(a[0]), id(b[1]) == id(a[1]), id(b[2]) == id(a[2]), id(b[3]) == id(a[3]),
          b)
    print('c:', id(c) == id(a), id(c[0]) == id(a[0]), id(c[1]) == id(a[1]), id(c[2]) == id(a[2]), id(c[3]) == id(a[3]),
          c)
    print('d:', id(d) == id(a), id(d[0]) == id(a[0]), id(d[1]) == id(a[1]), id(d[2]) == id(a[2]), id(d[3]) == id(a[3]),
          d)
    print('e:', id(e) == id(a), id(e[0]) == id(a[0]), id(e[1]) == id(a[1]), id(e[2]) == id(a[2]), id(e[3]) == id(a[3]),
          e)
    # a: [5, [4], (2,), 'str']
    # b: True True True True True [5, [4], (2,), 'str']
    # c: False False True True True [0, [4], (2,), 'str']
    # d: False False True True True [0, [4], (2,), 'str']
    # e: False False False True True [0, [1], (2,), 'str']
    shadow_copy = [[1, 2, 3, 4]] * 3
    deep_copy = [[1, 2, 3, 4] for _ in range(3)]


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
        print(list(file1))  # 等价于file1.readlines()
        file2.seek(33)
        print(file2.tell())
        print(file2.readline())


def args_tutorial():
    def test_keywords(name, age, gender):  # 关键字参数/解包参数调用函数(可通过keyword=value形式调用函数,参数顺序无所谓)
        print('name:', name, 'age:', age, 'gender:', gender)

    test_keywords('Jack', 20, 'man')
    test_keywords(*['Jack', 20, 'man'])
    test_keywords(gender='man', name='Jack', age=20)
    # test_keywords(**{'Gender': 'man', 'name': 'Jack', 'age': 20})  # Error,键必须与参数名相同
    test_keywords(*{'gender': 'man', 'name': 'Jack', 'age': 20})  # name: gender age: name gender: age
    test_keywords(**{'gender': 'man', 'name': 'Jack', 'age': 20})  # 解包字典,会得到一系列key=value,本质上是使用关键字参数调用函数

    def test_variable(first_key, *args, **kwargs):  # 在形参前加一个*或**来指定函数可以接收任意数量的实参,关键字参数必须跟随在位置参数后面
        print(first_key, type(args), args, type(kwargs), kwargs)

    test_variable(1, *[2, 3], c=4, d=5, **{'e': 6})  # 1 <class 'tuple'> (2, 3) <class 'dict'> {'c': 4, 'd': 5, 'e': 6}

    number = 5

    def test_default(element, num=number, arr=[], arr1=None):  # 如果默认值是一个可变对象如列表,字典,大多类对象时,函数在随后调用中会累积参数值
        arr.append(element)
        if arr1 is None:  # if u don't want the default to be shared between subsequent calls ,u can write the function like this instead.
            arr1 = []
        arr1.append(element)
        print(num, arr, arr1)

    number = 6
    test_default(1)  # 5 [1] [1]
    test_default(2)  # 5 [1, 2] [2]
    print(test_default.__defaults__)  # (5, [1, 2], None), 默认值在函数定义时已被确定


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
    _ = datetime(2020, 10, 9, 11, 12, 13)  # 2020-10-09 11:12:13


def heap_tutorial():
    heap = [3, 54, 64, 4, 34, 24, 2, 4, 24, 33]
    heapify(heap)  # 小顶堆
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


def instance_tutorial():
    # isinstance(object,class )    判断对象object是不是类class或其派生类的实例
    # issubclass(class ,baseclass) 判断一个类是否是另一个类的子类
    class Person: pass

    class Student(Person): pass

    person = Person()
    student = Student()
    print(isinstance(person, Person), isinstance(person, Student))  # True False
    print(isinstance(student, Person), isinstance(student, Student))  # True True
    print(issubclass(Student, Person))  # True


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


def read_excel_tutorial():  # 读excel表格
    df = pd.read_excel('map.xlsx',
                       sheet_name='Sheet2',
                       header=1,  # header指定开始读取的行号
                       usercols=[2, 4, 6, 7],
                       dtype={'name': str, 'id': int},
                       names=['name', 'id', 'score']
                       )
    for row in range(df.shape[0]):
        if pd.isna(df.loc[row]['name']):
            pass


def random_tutorial():
    # random是伪随机, 默认随机数生成种子是从 /dev/urandom或系统时间戳获取, 所以种子肯定不会是一样的
    print(random())  # 随机生成一个[0,1)范围内实数
    print(randrange(1, 10, 2))  # 从range(start, stop[, step])范围内选取一个值并返回(不包含stop)
    arr = [1, 2, 3, 4, 5, 6, 6, 6, 6]
    print(choice(arr))  # 返回一个列表,元组或字符串的随机项
    print(sample(arr, 3))  # 返回列表指定长度个不重复位置的元素
    shuffle(arr)  # 方法将序列的所有元素随机排序
    print(arr)


def win32_tutorial():
    x, y = 120, 240
    win32api.SetCursorPos((x, y))  # 鼠标定位,不同的屏幕分辨率请用百分比换算
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)  # 鼠标左键按下
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)  # 鼠标左键弹起


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
        print("outer:", var, end='\t')

    outer()  # inner: 9 outer: 1
    print("global:", var)  # global: 0


def dec2bin(string, precision=10):  # 方便理解c语言浮点数的内存表示, dec2bin('19.625') => 10011.101
    result = deque()
    integer, decimal = re.match(r'(\d*)(\.?\d*)', string).groups()
    integer, decimal = int(integer or 0), float(decimal or 0)
    while integer:
        result.appendleft(str(integer & 1))
        integer >>= 1
    if decimal:
        result.append('.')
    while precision and decimal:
        decimal *= 2
        if decimal >= 1:
            result.append('1')
            decimal -= 1
        else:
            result.append('0')
        precision -= 1
    return ''.join(result)


# memoryview
# It allows you to share memory between data-structures (things like PIL images, SQLlite data-bases, NumPy arrays, etc.) without first copying. 
# This is very important for large data sets.With it you can do things like memory-map to a very large file, slice a piece of that file and do calculations on that piece
# A memoryview supports slicing and indexing to expose its data. One-dimensional slicing will result in a subview
# 当memoryview实例mm跨进程传递时,相当于子进程拷贝了一份数据,mm重新指向了子进程的数据,指针对象ctypes.pointer也是一样
# ctypes.memset(dst, c, count)
# Same as the standard C memset library function: fills the memory block at address dst with count bytes of value c. dst must be an integer specifying an address, or a ctypes instance.

# from_buffer(source[, offset])
# This method returns a ctypes instance that shares the buffer of the source object. The source object must support the writeable buffer interface.
# The optional offset parameter specifies an offset into the source buffer in bytes; the default is zero. If the source buffer is not large enough a ValueError is raised.


def work(data):
    data[0] = 65


def main():
    t0 = time.time()
    data = bytearray(b'a' * 900000)
    _data = memoryview(data)
    # print(_data.tobytes())
    for idx in range(1, 900000):
        # work(data)         # .07s
        # work(data[:idx])   # 13s,拷贝了一份传给了work函数
        work(_data[:idx])  # .16s,相当于指针传给了work函数
    print(data[0], f'cost {time.time() - t0} seconds')


if __name__ == '__main__':
    main()

##################################################################################################################################

# mmap
import os, time, mmap, re, ctypes


def test0():
    mm = mmap.mmap(fileno=-1, length=256,
                   access=mmap.ACCESS_COPY)  # fileno=-1 means map anonymous memory,length不能小于所写内容总字节数
    mm.write(
        b"Hello world!\n")  # 会移动文件指针,If the mmap was created with ACCESS_READ, then writing to it will raise a TypeError exception.
    mm.write(b"welcome to python!\n")  # 如果剩余空间不足,则抛出ValueError

    # 不会移动文件指针,也不使用文件指针
    print(re.findall(rb'!', mm))
    mm[0] = 97
    mm[6:12] = b'python'
    print(mm[:5])

    # 会移动文件指针
    mm.seek(0)  # 指定文件指针到某个位置
    print(mm.read(13))  # 读指定字节数据
    print(mm.readline())  # 读一行数据
    mm.close()  # Subsequent calls to other methods of the object will result in a ValueError exception being raised. This will not close the open file.


def test1():
    with open("hello.txt", "wb") as f:
        f.write(b"Hello Python!\n")

    with open("hello.txt", "r+b") as f:  # 读写权限要与mmap保持一致
        with mmap.mmap(f.fileno(), 0,
                       access=mmap.ACCESS_COPY) as mm:  # 向ACCESS_WRITE内存映射赋值会影响内存和底层的文件,向ACCESS_COPY内存映射赋值会影响内存,但不会更新底层的文件
            print(mm.readline())  # prints b"Hello Python!\n"
            print(mm[:5])  # prints b"Hello"
            mm[6:] = b" world!\n"
            mm.seek(0)
            print(mm.readline())  # prints b"Hello  world!\n"


def test2():
    '''
    create an anonymous map and exchange data between the parent and child processes
    MAP_PRIVATE creates a private copy-on-write mapping, so changes to the contents of the mmap object will be private to this process(A进程更改的数据不会同步到B进程);
    MAP_SHARED creates a mapping that's shared with all other processes mapping the same areas of the file. The default value is MAP_SHARED(A进程更改的数据会同步到B进程).
    在MAP_SHARED情况下各个进程的mm对象独立,意味着close,文件指针等不相互影响,仅共享数据
    
    length申请的是虚拟内存VIRT(注意length要大点,应为本身会预申请一定大小的虚拟内存)
    如果flags=mmap.MAP_PRIVATE,write占用的是驻留内存RES; 如果flags=mmap.MAP_SHARED,write占用的是共享内存SHR,但由于RES包含SHR,所以RES也会相应增大
    '''
    mm = mmap.mmap(-1, length=13, flags=mmap.MAP_SHARED)
    mm.write(b"Hello world!")
    mm.seek(0)
    pid = os.fork()

    if pid == 0:  # In a child process
        mm[6:12] = b'python'
        print('child process: ', mm.readline())
        print('child process: ', mm.tell())
        mm.close()
        os._exit(0)
    else:  # In a parent process
        time.sleep(1)  # 让子进程先执行
        print('parent process: ', mm.tell())
        print('parent process: ', mm.readline())
        mm.close()


def test3():  # 进程间通信(模拟multiprocessing.Value)
    mm = mmap.mmap(fileno=-1, length=8)
    buf = memoryview(mm)
    obj = ctypes.c_int.from_buffer(buf)  # buf大小不能小于c_int大小,正确使用方式是跟c_int一般大
    # obj=ctypes.c_int(12)  # 此obj无法在进程间共享
    ctypes.memset(ctypes.addressof(obj), 97, ctypes.sizeof(obj))  # 非必须,一般用于未给定初始值情况下的初始化工作
    obj.value = 2 ** 31 - 1  # 最大数
    print(mm[:], buf.tobytes(), obj.value)
    mm.write(b"Hello\n")  # 会影响到obj的值,应为操作的是同一块内存
    print(mm[:], buf.tobytes(), obj.value)

    print('in parent', obj.value)
    if 0 == os.fork():
        obj.value = 13
        print('in son', obj.value)
    else:
        time.sleep(1)
        print('in parent', obj.value)


if __name__ == '__main__':
    test2()

##################################################################################################################################

# thread local
from multiprocessing.dummy import Process
from threading import local
import time
from os import urandom


class ThreadLocal:
    def __init__(self):
        # self.token=local()  # 保证同一个实例在不同线程中拥有不同的token值,redis分布式锁利用该性质达到线程安全
        self.token = type('dummy', (), {})

    def show(self, timeout):
        self.token.value = urandom(16)
        time.sleep(timeout)
        print(self.token.value)


thread_local = ThreadLocal()

processes = [Process(target=lambda thread_local, timeout: thread_local.show(timeout), args=(thread_local, idx)) for idx
             in range(1, 4)]
for process in processes:
    process.start()
for process in processes:
    process.join()

##################################################################################################################################

import threading


def plyer_display():
    print('初始化通过完成,音视频同步完成,可以开始播放....')


barrier = threading.Barrier(3, action=plyer_display, timeout=None)  # 设置3个障碍对象


def player_init(status):
    print(status)
    try:
        barrier.wait(2)  # 如果2秒内没有达到障碍线程数量,会进入断开状态,引发BrokenBarrierError错误
    except Exception as e:  # BrokenBarrierError错误
        print("等待超时了... ")
    else:
        print("xxxooooxxxxxooooxxxoooo")


if __name__ == '__main__':

    status_list = ["init ready", "video ready", "audio ready"]
    thread_list = []
    for i in range(0, 3):
        t = threading.Thread(target=player_init, args=(status_list[i],))
        t.start()
        thread_list.append(t)
    for t in thread_list:
        t.join()
'''
output:
init ready
video ready
audio ready
初始化通过完成,音视频同步完成,可以开始播放....
xxxooooxxxxxooooxxxoooo
xxxooooxxxxxooooxxxoooo
xxxooooxxxxxooooxxxoooo
'''

##################################################################################################################################

int('0x01002', 16)  # 字符串是16进制,并将其转换成10进制

x = 1
eval('x+1')  # 2  执行字符串形式的表达式,返回执行结果

x = 1
exec('x += 10')  # 执行字符串形式的代码，返回None
print(x)  # 11

#########################################################################################################################################

类变量 & 实例变量
'''
对象访问变量x,先在对象自身的__dict__中查找是否有x,如果有则返回,否则进入对象所属的类__dict__中进行查找,找不到则抛出异常
类变量(class variable)是类的属性和方法,它们会被类的所有实例共享.而实例变量(instance variable)是实例对象所特有的数据,不能通过类名访问
'''


class Test:
    class_var = [1]

    def __init__(self):
        self.i_var = 2
        self.__secret = 3


v1 = Test()
v2 = Test()
print(v1.__dict__)  # {'i_var': 2, '_Test__secret': 3},只包含实例属性,私有属性__secret被更改为_Test__secret
print(Test.__dict__)  # {'class_var': [1], '__init__': <function Test.__init__ at 0x0000000003731D90>},除了实例属性以外的所有成员
v1.class_var = [4]  # 当且仅当class_var是可变类属性并修改他时才会修改类属性,否则改变的是当前的实例属性
print(v1.__dict__)  # {'i_var': 2, '_Test__secret': 3, 'class_var': [4]},新增class_var实例属性
print(v2.__dict__)  # {'i_var': 2, '_Test__secret': 3},不包含v1新增的实例属性class_var
print(
    Test.__dict__)  # {'class_var': [1], '__init__': <function Test.__init__ at 0x0000000003731D90>},此时的class_var = [1]不变


class A: a = []


obj1 = A()
obj2 = A()
obj1.a += [2]  # 等价于obj1.a.append(2);obj1.a=A.a
print(id(obj1.a), id(obj2.a), id(A.a))  # 58584712 58584712 58584712
print(obj1.a, obj2.a, A.a)  # [2] [2] [2]
print(obj1.__dict__, obj2.__dict__,
      A.__dict__)  # {'a': [2]} {} {'fun': <function A.fun>, '__dict__': <attribute '__dict__' of 'A' objects>, 'a': [2]}


class A: a = 10


obj1 = A()
obj2 = A()
obj1.a += 2
print(id(obj1.a), id(obj2.a), id(A.a))  # 8790824644704 8790824644640 8790824644640
print(obj1.a, obj2.a, A.a)  # 12 10 10
print(obj1.__dict__, obj2.__dict__,
      A.__dict__)  # {'a': 12} {} {'a': 10, '__dict__': <attribute '__dict__' of 'A'>, 'fun': <function A.fun>}

#########################################################################################################################################

inherit


# MRO全称Method Resolution Order,用来定义继承方法的调用顺序,MRO采用广度优先
# 在继承中一旦定义了子类的构造函数,则需要在第一行显示调用基类的构造函数super().__init__()
# 在类的继承层次结构中,super只想按子类MRO指定的顺序调用"下一个方法",而不是父类的方法(super不总是代理子类的父类,还有可能代理其兄弟类)
# super的目标就是解决复杂的多重继承问题,保证在类的继承层次结构中每一个方法只被执行一次
class A:  # 模拟object类
    def __init__(self):
        print('init A...')


class B(A):
    def __init__(self):
        super().__init__()
        print('init B...')


class C(A):
    def __init__(self):
        super().__init__()
        print('init C...')


class D(B, C):
    def __init__(self):
        super().__init__()
        print('init D...')


print(
    D.mro())  # [<class '__main__.D'>, <class '__main__.B'>, <class '__main__.C'>, <class '__main__.A'>, <class 'object'>]
print(B.mro())  # [<class '__main__.B'>, <class '__main__.A'>, <class 'object'>]
print(A.mro())  # [<class '__main__.A'>, <class 'object'>]
d = D()
# init A...
# init C...
# init B...
# init D...
b = B()


# init A...
# init B...

#########################################################################################################################################

class Sample:
    def __enter__(self):
        print("In __enter__")
        return 'test'  # 返回值赋给with后面的as变量

    def __exit__(self, type, value, trace):
        '''
        没有异常的情况下整个代码块运行完后触发__exit__,他的三个参数均为None
        当有异常产生时,从异常出现的位置直接触发__exit__
        __exit__运行完毕就代表整个with语句执行完毕
        返回值为True代表吞掉了异常,并且结束代码块运行,但是代码块之外的代码会继续运行,否则代表抛出异常,结束所有代码的运行,包括代码块之外的代码
        '''
        print("In __exit__,type: {}, value: {}, trace: {}".format(type, value, trace))
        return True

    def do_something(self):
        1 / 0


sample = Sample()
with sample as f:  # 相当于f = sample.__enter__()
    print(f)  # test
    sample.do_something()
    print('after do something')

#########################################################################################################################################

property(fget=None, fset=None, fdel=None, doc=None)：函数
property()
的作用就是把类中的方法当作属性来访问


class C:
    def __init__(self):
        print('init')
        self.__x = None

    def getx(self):
        print('getx')
        return self.__x

    def setx(self, value):
        print('setx')
        self.__x = value

    def delx(self):
        print('delx')
        del self.__x

    x = property(getx, setx, delx, "I'm the 'x' property.")


c = C()
c.x = 20  # 相当于c.setx(20)
print(c.x)  # 相当于c.getx()
del c.x  # 相当于c.delx()

#########################################################################################################################################

__getattr__ & __setattr__


class Rectangle:
    keys = 'keys'

    def __init__(self):
        self.width = 0  # 调用__setattr__
        self.length = 0  # 调用__setattr__

    def __setattr__(self, name, value):
        '''
        会拦截所有属性的的赋值语句,如果定义了这个方法,self.attr = value就会变成self.__setattr__("attr", value)
        当在__setattr__方法内对属性进行赋值時,不可使用self.attr = value,因为他会再次调用self.__setattr__("attr", value)形成无穷递归循环,最后导致堆栈溢出异常
        应该通过对属性字典做索引运算来赋值任何实例属性,也就是使用self.__dict__['name']= value
        '''
        print('调用__setattr__', end='\t')
        if name == "size":
            print('in')
            self.width, self.length = value  # 调用__setattr__
        else:
            print('out')
            self.__dict__[name] = value

    def __getattr__(self, name):  # 使用实例直接访问实例不存在的属性时,会调用__getattr__方法
        print('调用__getattr__', end='\t')
        if name == "size":
            return self.width, self.length
        else:
            return 'default'

    def __getitem__(self, key):
        print('调用__getitem__', end='\t')
        return self.width

    def __setitem__(self, key, value):
        print('调用__setitem__')
        self.__dict__[key] = value

    def test(self):
        return 20


if __name__ == "__main__":
    r = Rectangle()
    r.width = 3  # 调用__setattr__    out, 等价于setattr(r,'width',3)
    r.length = 4  # 调用__setattr__    out
    print(r.size)  # 调用__getattr__ (3, 4), 等价于getattr(r,'size')
    print(r.area)  # 调用__getattr__  default
    r.size = 30, 40  # 调用__setattr__ in
    print(r.width, r.length)  # (30,40),不会调用__setattr__和__getattr__
    print(r['width'])  # 调用__getitem__ 30
    r['q'] = 9  # 调用__setitem__, 相当于r.q=9

    print(getattr(r, 'test')())  # 获取对象中test方法并执行,不调用__getattr__
    print(getattr(r, 'avatar', 'akatsuki'))  # 调用__getattr__   default, 由于定义了__getattr__,所以这里的默认值akatsuki不会生效
    print(getattr(r, 'keys'))  # keys

#########################################################################################################################################

__base__ & __name__ & __class__


class Tests:
    a = '10'

    def test(self):
        return 20


t = Tests()

print(Tests, type(t),
      t.__class__)  # <class '__main__.Tests'> <class '__main__.Tests'> <class '__main__.Tests'>  完全等价
# print(t.__base__ ,t.__name__)       #实例t无此属性
print(type, type(Tests), Tests.__class__)  # <class 'type'> <class 'type'> <class 'type'>   完全等价
print(Tests.__base__, Tests.__name__)  # <class 'object'> Tests
# 注意: 类定义里面的self跟类实例的类型一样

#########################################################################################################################################

big - endian & little - endian
# include <stdbool.h>
bool
is_big_endian() // 如果字节序为big - endian, 返回1, 反之返回0
{
    unsigned
short
test = 0x1122;
if (*((unsigned char *) & test) == 0x11)
return true;
else
return false;
}
/ *
big - endian: 低位地址保存高位数字, 方便阅读理解
little - endian: 在变量指针转换的时候地址保持不变, 比如int64 * 转到int32 *
                                                   目前看来是little - endian成为主流了
                                                   * /

                                                   #########################################################################################################################################

                                                   locals() & globals()
a = 5


def test(arg):
    z = 1
    print(locals())
    print(globals())


test(3)

'''
{'z': 1, 'arg': 3}
{'__loader__': <_frozen_importlib_external.SourceFileLoader object at 0x000001FDBDCC8940>, '__package__': None, '__name__': '__main__', 'a': 5, '__doc__': None, '__file__': 'C:\\Users\\root\\Desktop\\zzzz.py', 'test': <function test at 0x000001FDBDBD7F28>, '__spec__': None, '__cached__': None, '__builtins__': <module 'builtins' (built-in)>}
'''

#########################################################################################################################################

sub & subn & split
regex.sub(repl, string, count=0):
使用repl替换string中每一个匹配的子串, 返回替换后的字符串.若找不到匹配, 则返回原字符串
当repl是一个字符串时, 任何在其中的反斜杠都会被处理
count用于指定最多替换次数, 不指定时全部替换
subn同sub, 只不过返回值是一个二元tuple, 即(sub函数返回值, 替换次数)
r'^[a-zA-Z0-9]+$'  # 匹配全部由数字字母组成的字符串

import re

pattern = re.compile(
    r"like")  # compile内部也会有缓存,因此少量正则匹配不需要compile,refer: https://github.com/python/cpython/blob/master/Lib/re.py#L289
s1 = pattern.sub(r"love", "I like you, do you Like me?")
print(s1)  # I love you, do you love me?
print(re.subn(r'(\w+) (\w+)', r'\2 \1', 'i say, hello world!'))  # ('say i, world hello!', 2)
#  re.split(pattern, string, maxsplit=0, flags=0)   flags用于指定匹配模式
print(re.split(r'[\s\,\;]+', 'a,b;; c d'))  # ['a', 'b', 'c', 'd']

#########################################################################################################################################

md5
import hashlib

m = hashlib.md5(b"hello blockchain world, this is yeasy@github")
print(m.hexdigest())  # 1ee216d3ef1d217cd2807348f5f7ce19
'''
echo -n "hello blockchain world, this is yeasy@github"|md5sum
注意Linux下要去掉字符串末尾的\n
'''

#########################################################################################################################################

search: 匹配到就终止, 只匹配一个, 可指定起始位置跟结束位置
findall: 匹配所有, 可指定起始位置跟结束位置
match: 从头开始匹配, 最多匹配一个, 可指定起始位置跟结束位置
import re

s = 'avatar cao nihao 1234,'
regex = re.compile(r'(ava\w+) cao (nihao)')
# group默认是group(0),返回全部,groups是以tuple类型返回括号内所有内容
print(regex.search(s).group())  # avatar cao nihao
print(regex.search(s).groups())  # ('avatar', 'nihao')

s = 'avat1ar cao avat2ar cao,'
regex = re.compile(r'(ava\w+) cao')
print(regex.findall(s))  # ['avat1ar', 'avat2ar']
regex = re.compile(r'ava\w+ cao')
print(regex.findall(s))  # ['avat1ar cao', 'avat2ar cao']

# 注意r''的使用
re.findall(r'\[q\\w1', '[q\w1')  # ['[q\\w1']
re.findall('\\[q\\\w1', '[q\w1')  # ['[q\\w1']
re.findall('\[q\\w1', '[q\w1')  # [],匹配不到的原因是python字符串也是用\转义特殊字符,\[被python理解成[
re.findall(r'\bor\b', 'which or orange ')  # ['or'] 建议使用\b单词\b形式,如\bw+\b
re.findall('\bor\b', 'which or orange ')  # []

[]
匹配所包含的任意一个字符
连字符 - 如果出现在字符串中间表示字符范围描述;
如果如果出现在首位则仅作为普通字符
特殊字符仅有反斜线\保持特殊含义, 用于转义字符.其它特殊字符如 *、+、? 等均作为普通字符匹配
脱字符 ^ 如果出现在首位则表示匹配不包含其中的任意字符;
如果 ^ 出现在字符串中间就仅作为普通字符匹配

[\u4e00 -\u9fa5]  # 匹配中文
^ [ ^ t]+  # 匹配不以t开头的字符串

#########################################################################################################################################

\w
s = 'as_6の5你ava'
print(re.findall(r'\w+', s))  # ['as_6の5你ava']
print(re.findall(r'\w+', s, re.ASCII))  # ['as_6', '5', 'ava']

For
Unicode(str)
patterns:
Matches
Unicode
word
characters;
this
includes
most
characters
that
can
be
part
of
a
word in any
language,
as well as numbers and the
underscore.If
the
ASCII
flag is used, only[a - zA - Z0 - 9
_] is matched.

#########################################################################################################################################

多行匹配 / 断言(re.S & re.M)
# \n匹配换行符,默认.不会匹配换行符,re.S也有同样效果,re.I忽略大小写
print(re.findall(r"a\d+b.+a\d+b", "a23b\na34b"))  # []
print(re.findall(r"a\d+b(?:.|\n)+a\d+b",
                 "a23b\na34b"))  # ['a23b\na34b'] ?:意思是让findall,search等函数'看不见'括号,类似用法如re.findall(r'(?:\d{1,3}\.){3}\d{1,3}','192.168.1.33')
print(re.findall(r"a\d+b.+a\d+b", "a23b\na34b", re.S))  # ['a23b\na34b']

# re.M：可以使^$标志将会匹配每一行,默认^和$只会匹配第一行
print(re.findall(r"^a(\d+)b", "a23b\na34b"))  # ['23']
print(re.findall(r"^a(\d+)b", "a23b\na34b", re.M))  # ['23', '34']

# 但是如果没有^标志,是无需re.M
print(re.findall(r"a(\d+)b", "a23b\na34b"))  # ['23', '34']

# 断言,且都是零宽
print(re.findall(r'\w+\.(?!com)\w+', 'www.com https.org'))  # ['https.org'],不以...结束
print(re.findall(r'\w+(?<!www)\.\w+', 'www.com https.org'))  # ['https.org'],不以...开头
print(re.findall(r'\w+\.(?=c.m)', 'www.com https.org'))  # ['www.'],以...结束
print(re.findall(r'(?<=\w{5})\.\w+', 'www.com https.org'))  # ['.org'],以...开头
