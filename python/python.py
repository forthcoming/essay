# Type hinting
from typing import List

def greater(a: int, b: int) -> bool:
    return a > b
a: int = 123
b: str = 'hello'
l: List[int] = [1, 2, 3]  # 指明一个全部由整数组成的列表
print(greater.__annotations__) # {'a': <class 'int'>, 'b': <class 'int'>, 'return': <class 'bool'>}

##################################################################################################################################

# thread local
from multiprocessing.dummy import Process
from threading import local
import time
from os import urandom

class ThreadLocal:
    def __init__(self):
        self.token=local()  # 保证同一个实例在不同线程中拥有不同的token值,redis分布式锁利用该性质达到线程安全
        # self.token=type('dummy',(),{})

    def show(self,timeout):
        self.token.value=urandom(16)
        time.sleep(timeout)
        print(self.token.value)

thread_local=ThreadLocal()

processes=[Process(target=lambda thread_local,timeout:thread_local.show(timeout),args=(thread_local,idx)) for idx in range(1,4)]
for process in processes:
    process.start()
for process in processes:
    process.join()

##################################################################################################################################
    
函数调用(引用传参)
# 关键字参数/解包参数调用函数(可通过keyword=value形式调用函数,参数顺序无所谓)
def fun(name, age, gender):  
    print('name:',name,'age:',age,'gender:',gender)  
fun(gender='man', name='Jack', age=20)  
fun(*['Jack',20,'man'])
fun(**{'gender':'man', 'name':'Jack', 'age':20}) # 解包字典,会得到一系列key=value,本质上是使用关键字参数调用函数
fun(**{'Gender':'man', 'name':'Jack', 'age':20}) # Error,键必须与参数名相同

# 默认实参调用函数(默认值只被计算一次,如果默认值是一个可变对象如列表,字典,大多类对象时,函数在随后调用中会累积参数值)
def fun(a, L=[]):  
    L.append(a)  
    print(L)  
fun(1)  # 输出[1]  
fun(2)  # 输出[1, 2]  

# 可变参数调用函数(在形参前加一个*或**来指定函数可以接收任意数量的实参,关键字参数必须跟随在位置参数后面)
def fun(a,*args,**kwargs):  
    print(a,end='\t')
    print(type(args),args,end='\t')    
    print(type(kwargs),kwargs)    
fun(1,2,3,c=4,d=5)   # 1	<class 'tuple'> (2, 3)	<class 'dict'> {'c': 4, 'd': 5}

#########################################################################################################################################

作用域
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
print(mc(),mc(),mc())   # 1,2,3

x = 0
def outer():
    x = 1
    def inner():
        # nonlocal x  # inner: 8	outer: 8	global: 0
        # global x    # inner: 7	outer: 1	global: 7
        x = 2         # inner: 9	outer: 1	global: 0
        x += 7 
        print("inner:", x,end='\t')
    inner()
    print("outer:", x,end='\t')
outer()
print("global:", x)

#########################################################################################################################################

sort
# if you don’t need the original list, list.sort is slightly more efficient than sorted.
# By default the sort and the sorted built-in function notices that the items are tuples so it sorts on the first element first and on the second element second.
items = [(1, 'B'), (1, 'A'), (2, 'A'), (0, 'B'), (0, 'a')]
sorted(items)                                       # [(0, 'B'), (0, 'a'), (1, 'A'), (1, 'B'), (2, 'A')]
sorted(items, key=lambda x: (x[0], x[1].lower()))   # [(0, 'a'), (0, 'B'), (1, 'A'), (1, 'B'), (2, 'A')]

peeps = [{'name': 'Bill', 'salary': 1000}, {'name': 'Bill', 'salary': 500}, {'name': 'Ted', 'salary': 500}]
sorted(peeps, key=lambda x: (x['name'], x['salary']))   # [{'salary': 500, 'name': 'Bill'}, {'salary': 1000, 'name': 'Bill'}, {'salary': 500, 'name': 'Ted'}]
# Bill comes before Ted and 500 comes before 1000. But how do you sort it like that on the name but reverse on the salary?
sorted(peeps, key=lambda x: (x['name'], -x['salary']))  # [{'salary': 1000, 'name': 'Bill'}, {'salary': 500, 'name': 'Bill'}, {'salary': 500, 'name': 'Ted'}]

#########################################################################################################################################

What kinds of global value mutation are thread-safe?
A global interpreter lock (GIL) is used internally to ensure that only one thread runs in the Python VM at a time. 
In general, Python offers to switch among threads only between bytecode instructions; how frequently it switches can be set via sys.setswitchinterval(). 
Each bytecode instruction and therefore all the C implementation code reached from each instruction is therefore atomic from the point of view of a Python program.

In theory, this means an exact accounting requires an exact understanding of the PVM bytecode implementation. 
In practice, it means that operations on shared variables of built-in data types (ints, lists, dicts, etc) that “look atomic” really are.
For example, the following operations are all atomic (L, L1, L2 are lists, D, D1, D2 are dicts, x, y are objects, i, j are ints):
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
Operations that replace other objects may invoke those other objects’ __del__() method when their reference count reaches zero, and that can affect things. 
This is especially true for the mass updates to dictionaries and lists. When in doubt, use a mutex!

#########################################################################################################################################

pickle
除个别外(如不能序列化lambda表达式),pickle.dumps可以序列化任何数据类型成b字符串,并保留原有的数据(比如生成好的树,图结构)
pickle.loads反序列化后的对象与原对象是等值的副本对象,类似与deepcopy

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
v1=Test()
v2=Test()
print(v1.__dict__)   # {'i_var': 2, '_Test__secret': 3},只包含实例属性,私有属性__secret被更改为_Test__secret 
print(Test.__dict__) # {'class_var': [1], '__init__': <function Test.__init__ at 0x0000000003731D90>},除了实例属性以外的所有成员
v1.class_var=[4]     # 当且仅当class_var是可变类属性并修改他时才会修改类属性,否则改变的是当前的实例属性
print(v1.__dict__)   # {'i_var': 2, '_Test__secret': 3, 'class_var': [4]},新增class_var实例属性
print(v2.__dict__)   # {'i_var': 2, '_Test__secret': 3},不包含v1新增的实例属性class_var
print(Test.__dict__) # {'class_var': [1], '__init__': <function Test.__init__ at 0x0000000003731D90>},此时的class_var = [1]不变

class A: a = []
obj1 = A()
obj2 = A()   
obj1.a += [2]                                   # 等价于obj1.a.append(2);obj1.a=A.a   
print(id(obj1.a), id(obj2.a), id(A.a))          #58584712 58584712 58584712
print(obj1.a, obj2.a, A.a)                      #[2] [2] [2]
print(obj1.__dict__, obj2.__dict__, A.__dict__) #{'a': [2]} {} {'fun': <function A.fun>, '__dict__': <attribute '__dict__' of 'A' objects>, 'a': [2]}

class A: a = 10   
obj1 = A()
obj2 = A()   
obj1.a += 2
print(id(obj1.a), id(obj2.a), id(A.a))         #8790824644704 8790824644640 8790824644640
print(obj1.a, obj2.a, A.a)                     #12 10 10
print(obj1.__dict__, obj2.__dict__,A.__dict__) #{'a': 12} {} {'a': 10, '__dict__': <attribute '__dict__' of 'A'>, 'fun': <function A.fun>}

#########################################################################################################################################

inherit
# MRO全称Method Resolution Order,用来定义继承方法的调用顺序,MRO采用广度优先
# 在继承中一旦定义了子类的构造函数,则需要在第一行显示调用基类的构造函数super().__init__()
# 在类的继承层次结构中,super只想调用"下一个方法",而不是父类的方法
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

print(D.mro()) # [<class '__main__.D'>, <class '__main__.B'>, <class '__main__.C'>, <class '__main__.A'>, <class 'object'>]
print(B.mro()) # [<class '__main__.B'>, <class '__main__.A'>, <class 'object'>]
print(A.mro()) # [<class '__main__.A'>, <class 'object'>]
d=D()
# init A...
# init C...
# init B...
# init D...
b=B()
# init A...
# init B...

#########################################################################################################################################

class Sample:
    def __enter__(self):
        print("In __enter__")
        return self  # 返回的值赋值给with后面的as变量

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
        1/0

with Sample() as sample:  # 相当于s=Sample().__enter__(),但不等价
    print(sample.__class__)  # <class '__main__.Sample'>
    sample.do_something()
    print('after do something')
print('out of code block')

#########################################################################################################################################

__slots__
实例的__dict__只保存实例变量,不保存类属性(变量和函数)
__slots__限制实例的属性,阻止实例拥有__dict__属性,能达到更快的属性访问和更少的内存消耗
it really only saves you when you have thousands of instances
__slots__ declaration is limited to the class where it is defined. As a result, subclasses will have a __dict__ unless they also define __slots__
__slots__定义的属性仅对当前类实例起作用,对继承的子类不起作用,除非在子类中也定义__slots__,这样子类实例允许定义的属性就是自身的__slots__加上父类的__slots__

#########################################################################################################################################

切片 & *
for i in [[1,2,3,4]] * 3:
  print(id(i))
for i in [[1,2,3,4] for _ in range(3)]:
  print(id(i))
'''
2312338042824
2312338042824
2312338042824
2312338042312
2312337166152
2312338058888
'''

#########################################################################################################################################

is & ==
x = y = [4,5,6]
z = [4,5,6]
x == y   #True
x == z   #True
x is y   #True
x is z   #False
print(id(x),id(y),id(z)) #1685786989512 1685786989512 1685786991112
is比较的内存地址,==比较的是字面值

#########################################################################################################################################

open
with open('test.txt','r') as f:
    for _ in f:  #无需要各种read()函数
    print(_)

f = open('/Users/michael/gbk.txt', 'r', encoding='gbk', errors='ignore')
#读取非UTF-8文件,要给open传入encoding参数,例如读取GBK文件
#遇到编码不规范的文件,会提示UnicodeDecodeError,errors参数表示如果遇到编码错误后如何处理,最简单的方式是直接忽略

with open('log1') as obj1, open('log2') as obj2:  #同时打开多个
    file=list(obj1)   #等价于obj1.readlines()
        obj2.seek(33)
        print(obj2.tell())
        print(obj2.readline())

r:read,default
w:write
b:binary
a:append
r+:从头开始读,从头开始往后覆盖
w+:读写,注意其w特性
a+:从头读,追加写

#########################################################################################################################################

sum
a = [[1, 2], [3, 4], [5, 6]]
_=sum(a,[])                #[1, 2, 3, 4, 5, 6]  sum第二个参数默认为0   
sum(_)                     #21
[x for l in a for x in l]  #[1, 2, 3, 4, 5, 6]

#########################################################################################################################################

split
mystr="Line1-abcdef \nLine2-abc \nLine4-abcd"
print(mystr.split())           #['Line1-abcdef', 'Line2-abc', 'Line4-abcd']
print(mystr.split(' ',1))      #['Line1-abcdef', '\nLine2-abc \nLine4-abcd']
print(mystr.split(' '))        #['Line1-abcdef', '\nLine2-abc', '\nLine4-abcd']
# 应用: 去除字符串中空白符content =''.join(content.split())

#########################################################################################################################################

__add__ & __iadd__
a1 = a2 = [1, 2]
b1 = b2 = [1, 2]
a1 += [3]          # Uses __iadd__, modifies a1 in-place
b1 = b1 + [3]      # Uses __add__, creates new list, assigns it to b1
print(a2)          # [1, 2, 3]   a1 and a2 are still the same list
print(b2)          # [1, 2]      whereas only b1 was changed

'''
The general answer is that += tries to call the __iadd__ special method, and if that isn't available it tries to use __add__ instead.
So the issue is with the difference between these special methods.
The __iadd__ special method is for an in-place addition, that is it mutates the object that it acts on.
The __add__ special method returns a new object and is also used for the standard + operator.
So when the += operator is used on an object which has an __iadd__ defined the object is modified in place.
Otherwise it will instead try to use the plain __add__ and return a new object.
That is why for mutable types like lists += changes the object's value,
whereas for immutable types like tuples, strings and integers a new object is returned instead (a += b becomes equivalent to a = a + b).
For types that support both __iadd__ and __add__ you therefore have to be careful which one you use.
a += b will call __iadd__ and mutate a, whereas a = a + b will create a new object and assign it to a. They are not the same operation!
For immutable types (where you don't have an __iadd__) a += b and a = a + b are equivalent.
This is what lets you use += on immutable types, which might seem a strange design decision until you consider that otherwise you couldn't use += on immutable types like numbers!
'''

#########################################################################################################################################

property(fget=None, fset=None, fdel=None, doc=None)：函数 property() 的作用就是把类中的方法当作属性来访问
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
c.x = 20      # 相当于c.setx(20)
print(c.x)    # 相当于c.getx()
del c.x       # 相当于c.delx()

#########################################################################################################################################

__getattr__ & __setattr__
class Rectangle:
    def __init__(self):
        self.width = 0  # 调用__setattr__
        self.length = 0 # 调用__setattr__

    def __setattr__(self, name, value):
        '''
        会拦截所有属性的的赋值语句,如果定义了这个方法,self.attr = value就会变成self.__setattr__("attr", value)
        当在__setattr__方法内对属性进行赋值時,不可使用self.attr = value,因为他会再次调用self.__setattr__("attr", value)形成无穷递归循环,最后导致堆栈溢出异常
        应该通过对属性字典做索引运算来赋值任何实例属性,也就是使用self.__dict__['name']= value
        '''
        print('__setattr__')
        if name == "size":
            print('in name')
            self.width, self.length = value  # 调用__setattr__
        else:
            print('out name')
            self.__dict__[name] = value

    def __getattr__(self, name):   #  # 使用实例直接访问实例不存在的属性时,会调用__getattr__方法
        print('__getattr__')
        if name == "size":
            return self.width, self.length
        else:
            raise AttributeError

    def __getitem__(self,key):
        print('__getitem__')
        return self.width

    def __setitem__(self,key,value):
        print('__setitem__')
        self.__dict__[key]=value

if __name__ == "__main__":
    r = Rectangle()
    r.width = 3  # 调用__setattr__
    r.length = 4 # 调用__setattr__
    print(r.size)   #(3, 4)
    r.size = 30,40  # 调用__setattr__
    print(r.width,r.length)  #(30,40)
    print(r['width'])
    r['q']=9  # 相当于r.q=9

#########################################################################################################################################

getattr & __base__ & __name__ & __class__
class Tests:   
a = '10'     
def test(self):
   return 20
t = Tests()

snap1 = getattr(t, 'test')()         #获取对象中test方法并执行
snap2 = getattr(t, 'a' ,'default' )  #获取对象中相应的值,如果没有则调用__getattr__,使用default(或者__getattr__规定的值)
snap3 = getattr(t,' c', 'default' )  #获取对象中相应的值,如果没有则使用default
print(snap1,snap2,snap3)             #20 10 default

print(Tests,type(t),t.__class__)     #<class '__main__.Tests'> <class '__main__.Tests'> <class '__main__.Tests'>  完全等价   
#print(t.__base__ ,t.__name__)       #实例t无此属性
print(type,type(Tests),Tests.__class__) #<class 'type'> <class 'type'> <class 'type'>   完全等价   
print(Tests.__base__,Tests.__name__)    #<class 'object'> Tests
# 注意: 类定义里面的self跟类实例的类型一样

#########################################################################################################################################

关系运算符
(1, 2, 3)              < (1, 2, 4)
[1, 2, 3]              < [1, 2, 4]
'ABC' < 'C' < 'Pascal' < 'Python'
(1, 2, 3, 4)           < (1, 2, 4)
(1, 2)                 < (1, 2, -1)
(1, 2, 3)             == (1.0, 2.0, 3.0)
(1, 2, ('aa', 'ab'))   < (1, 2, ('abc', 'a'), 4)
{1}<{2}  #False,子集运算符
{2}<{1}  #False,子集运算符

#########################################################################################################################################

walk
os.walk(top[, topdown=True[, onerror=None[, followlinks=False]]])
top -- 根目录下的每一个文件夹(包含它自己),产生3-元组 (dirpath,dirnames,filenames)[文件夹路径,文件夹名字,文件名]
topdown --为True或者没有指定,目录自上而下.如果topdown为False,目录自下而上
followlinks -- 设置为true,则通过软链接访问目录

#########################################################################################################################################

__call__: 一个类实例也可以变成一个可调用对象
class Person(object):
  def __init__(self, name, gender):
    self.name = name

  def __call__(self, friend):
    print('My name is {},My friend is {}.'.format(self.name,friend))

p = Person('Bob', 'male')
p('Tim')    #My name is Bob,My friend is Tim.

#########################################################################################################################################

__len__: 要让 len() 函数工作正常,类必须提供一个特殊方法__len__(),它返回元素的个数
class Students(object):
  def __init__(self, *args):
    self.names = args
  def __len__(self):
    return len(self.names)

student = Students('Bob', 'Alice', 'Tim')
print(len(student))  #3

#########################################################################################################################################

__str__: 自定义打印类的格式
class Node:
    def __init__(self, data, right=None):
        self.data = data
        self.right = right
    def __str__(self):
        return 'data:{}'.format(self.data)

print(Node(1))

#########################################################################################################################################

isinstance(object, class):   判断对象object是不是类class或其派生类的实例
issubclass(class,baseclass): 判断一个类是否是另一个类的子类
class Person():
  def __init__(self, name, gender):
    self.name = name
    self.gender = gender

class Student(Person):
  def __init__(self, name, gender, score):
    super().__init__(name, gender)
    self.score = score

p = Person('Tim', 'Male')
s = Student('Bob', 'Male', 88)

isinstance(p, Person)  #True
isinstance(p, Student) #False
# 父类实例不能是子类类型,因为子类比父类多了一些属性和方法

isinstance(s, Person)  #True
isinstance(s, Student) #True
# 子类实例可以看成它本身的类型,也可以看成它父类的类型

#########################################################################################################################################

enumerate(iterable, start=0): 返回一个可迭代的enumerate object,对其使用next()得到的是包含索引和元素的tuple,通常用于同时遍历索引和元素
seasons = ['Spring', 'Summer', 'Fall', 'Winter']
list(enumerate(seasons))  #[(0, 'Spring'), (1, 'Summer'), (2, 'Fall'), (3, 'Winter')]
for x in enumerate(seasons):
  print(x, end=' ')  #(0, 'Spring') (1, 'Summer') (2, 'Fall') (3, 'Winter')

means:
def enumerate(sequence, start=0):
  n = start
  for elem in sequence:
    yield n, elem
    n += 1

#########################################################################################################################################

决斗之城挂机
import win32api
import time
import win32con
import random
def LeftClick(x, y,t=0):    
    win32api.SetCursorPos((x, y)) # 鼠标定位,不同的屏幕分辨率请用百分比换算    
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)    # 鼠标左键按下    
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)    # 鼠标左键弹起    
    time.sleep(random.uniform(t,t+2))

while True:    
    LeftClick(460, 380,6)  # 战斗    
    LeftClick(80, 50,6)  # 左上角返回    
    LeftClick(32, 140)   # 手动    
    LeftClick(350, 340)   # 返回(等级升级)    
    LeftClick(280, 430,6)  # 返回

#########################################################################################################################################

exception
try: 
    1/0
except ValueError:  # 至多只有一个except被执行
    print('That was no valid number.')  
except ZeroDivisionError:  
    print('The divisor can not be zero.')  
except:  # 匹配任何类型异常,必须放在最后(default 'except:' must be last)
    print('Handling other exceptions...')  
else: # 必须放在所有except后面,当没有异常发生时执行
    print('no exception happen')
finally: # 定义一些清理工作,异常发生/捕捉与否,是否有return都会执行
    print('Some clean-up actions!')

#########################################################################################################################################

ipdb
whatis       Prints the type of the argument.
enter        重复上次命令
set_trace()  在该点打断(from ipdb import set_trace,或者直接在该处使用breakpoint(),不需要使用set_trace()函数)
c(ont(inue))   Continue execution, only stop when a breakpoint is encountered.执行到下个断点处
l(ist) [first [,last]]   List source code for the current file.Without arguments, list 11 lines around the current line or continue the previous listing.
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

#########################################################################################################################################

enum
from enum import Enum
class Color(Enum):  # 不能实例化
    red=1  # 不能给相同变量重复赋值
    orange=2
    yellow=3

print(Color(2),Color.red,Color(3)==3,Color(1)==Color.red)  # Color.orange Color.red False True

#########################################################################################################################################

bisect
from bisect import insort_right,bisect_left,bisect_right
a=[]
for i in [3,1,6,4,1,3,6,5,1,4]:
    insort_right(a,i)
print(a)
print(bisect_left(a,3))
print(bisect_right(a,3))
insort_right(a,2)

#########################################################################################################################################

读excel表格
import pandas as pd
df=pd.read_excel('map.xlsx',sheet_name='Sheet2',header=1,usercols=[2,4,6,7],dtype={'name':str,'id':int},names=['name','id','score'])  // header指定开始读取的行号
for row in range(df.shape[0]):
    if pd.isna(df.loc[row]['name']):
        pass

#########################################################################################################################################

set(无序不重复,添加元素用add)
A = {1, 2, 3, 3}
B = {3, 4, 5, 6, 7}
print(A==B)   #False
print(A<B)    #False,A不是B的子集
print(A | B)  #set([1, 2, 3, 4, 5, 6, 7])
print(A & B)  #set([3])
print(A - B)  #set([1, 2])
print(B - A)  #set([4, 5, 6, 7])
print(A ^ B)  #set([1, 2, 4, 5, 6, 7])
#(A ^ B) == ((A - B) | (B - A)),numbers in A or in B but not both
#区别于位运算符中的& ,| ,^和逻辑运算符 and or not

#########################################################################################################################################

Counter
from collections import Counter

count = Counter([1, 1, 2, 2, 3, 3, 3, 3, 4, 5])
print(count)                  #Counter({3: 4, 1: 2, 2: 2, 4: 1, 5: 1})
print(count[3],count['y'])    #4 0 ,访问不存在的元素返回0
print(count.most_common(1))   #[(3, 4)]
print(count.most_common(3))   #[(3, 4), (1, 2), (2, 2)]
count.update('plus')          #计数器更新
count.subtract('minus')       #计数器更新
print(count)                  #Counter({3: 4, 1: 2, 2: 2, 4: 1, 5: 1, 'l': 1, 'p': 1, 'u': 0, 's': 0, 'i': -1, 'n': -1, 'm': -1})
print(list(count.elements())) #[1, 1, 2, 2, 3, 3, 3, 3, 4, 5, 'l', 'p']

A = Counter([0, 1, 2, 2, 2])  #Counter({2: 3, 0: 1, 1: 1})
B = Counter([2, 2, 3])        #Counter({2: 2, 3: 1})
print(A | B)  #Counter({2: 3, 0: 1, 1: 1, 3: 1})
print(A & B)  #Counter({2: 2})
print(A + B)  #Counter({2: 5, 0: 1, 1: 1, 3: 1})
print(A - B)  #Counter({0: 1, 1: 1, 2: 1})
print(B - A)  #Counter({3: 1})

#########################################################################################################################################

heap
from heapq import heapify,heappop,heappush,nlargest,nsmallest,heappushpop

heap=[3,54,64,4,34,24,2,4,24,33]
heapify(heap)
print(heap)
print([heappop(heap) for i in range(len(heap))])

'''
Heap elements can be tuples.
This is useful for assigning comparison values (such as task priorities) alongside the main record being tracked:
'''
h=[]
heappush(h, (5, 'write code'))
heappush(h, (7, 'release product'))
heappush(h, (1, 'write spec'))
heappush(h, (3, 'create tests'))
print(nsmallest(3,h))
print(nlargest(2,h))
print(heappushpop(h, (4, 'for tests')))
print(h[0])  #查看堆中最小值，不弹出
print(heappop(h),h)

#########################################################################################################################################

format(最新版Python的f字符串可以看作format的简写)
string = "My name is: {}, I am {} years old, {} Engineer".format(*["ansheng",20,"Python"])
string #'My name is: ansheng, I am 20 years old, Python Engineer'

string = "My name is: {0}, I am {1} years old, {0} Engineer".format(*["ansheng",20,"Python"])
string #'My name is: ansheng, I am 20 years old, ansheng Engineer'

string = "My name is: {name}, I am {age} years old, {job} Engineer".format(**{"name":"ansheng","age":20,"job":"Python"})
string #'My name is: ansheng, I am 20 years old, Python Engineer'

string = "My name is: {:s}, I am {:d} years old, {:f} wage".format("Ansheng",20,66666.55)
string #'My name is: Ansheng, I am 20 years old, 66666.550000 wage'

string = "numbers: {0:b},{0:f},{0:d},{0:#x},{0:X}, {0:%}".format(15)
string #'numbers: 1111,15.000000,15,0xf,F, 1500.000000% '
print(f"numbers: {15:b},{15:f},{15:d},{15:#x},{15:X}, {15:%}")

#########################################################################################################################################

subprocess
#!/root/miniconda3/bin/python
#如果指定编译器,则可通过./test来执行，否则只能通过python test来执行
from subprocess import run,PIPE
#run(['mkdir','-p','11'])
#run('rm -rf 11'.split())
ret=run('ls -l',shell=True,stdout=PIPE,stderr=PIPE)
print(ret.args,'\n',ret.returncode,'\n',ret.stdout,'\n',ret.stderr)

#########################################################################################################################################

解包/拆箱
a, b, c = 1, 2, 3
a, (b, c), d = [1, (2, 3), 4]
a, *b, c = [1, 2, 3, 4, 5]

a, b = 1, 2
a, b = b, a   #使用拆箱进行变量交换
                                       
first, _, third, *_ = range(10)
print(first, third,_)  # 0 2 [3, 4, 5, 6, 7, 8, 9]

#########################################################################################################################################

datetime(有局限性,获取的是本地时间)
from datetime import datetime,timedelta
print(datetime.now())
print(datetime.now().date())
print(datetime.now().time())
print(datetime.now().weekday())
print(datetime.now().year)
print(datetime.now().month)
print(datetime.now().strftime('%Y-%m-%d'))  # <class 'str'>
print(datetime.now()-timedelta(days=2))    # weeks,minutes
print(datetime.strptime('2016-9-9 18:19:59', '%Y-%m-%d %H:%M:%S'))  # <class 'datetime.datetime'>
print(datetime.fromtimestamp(1541755412))  # 2018-11-09 17:23:32

OUT:
2016-12-17 11:46:32.815229
2016-12-17
11:46:32.815229
5
2016
12
2016-12-17
2016-12-15 11:46:32.815229
2016-09-09 18:19:59

import time
time_struct = time.localtime(1555395365)
print(time.strftime("%Y-%m-%d %H:%M:%S", time_struct))  # 时间戳转时间字符串
                                       
#########################################################################################################################################

random
from random import randrange,uniform,choice,sample,shuffle,randint,random

print(random())            # 随机生成一个[0,1)范围内实数                                 
print(randrange(1, 10, 2)) # 从range(start, stop[, step])范围内选取一个值并返回(不包含stop)
print(uniform(-2,5))       # 随机生成一个[x,y]范围内实数
print(randint(-2,5))       # 随机生成一个[x,y]范围内整数
a=[1,2,3,4,5,6,6,6,6]
print(choice(a))           # 返回一个列表,元组或字符串的随机项
print(sample(a,3))         # 返回列表指定长度个不重复位置的元素
shuffle(a)                 # 方法将序列的所有元素随机排序
print(a)

OUT:
3
3.7145573142558552
5
[6, 2, 6]
[6, 5, 6, 6, 3, 6, 4, 2, 1]

注意:
random是伪随机,默认随机数生成种子是从/dev/urandom或者是系统时间戳获取,所以种子肯定不会是一样的
但两个进程的父进程是同一个进程,进程在导入random模块的时候种子已经选好了,所以不同子进程生成的随机数序列肯定是一样的
验证如下
import random
import os
if os.fork() == 0:
    print(f"[rand 1] {random.randint(1,100)}")
    print(f"[rand 1] {random.randint(1,100)}")
    print(f"[rand 1] {random.randint(1,100)}")
else:
    print(f"[rand 2] {random.randint(1,100)}")
    print(f"[rand 2] {random.randint(1,100)}")
    print(f"[rand 2] {random.randint(1,100)}")
» python test.py
[rand 2] 51
[rand 2] 58
[rand 2] 31
[rand 1] 51
[rand 1] 58
[rand 1] 31

import random
import os
if os.fork() == 0:
    random.seed()
    print(f"[rand 1] {random.randint(1,100)}")
    print(f"[rand 1] {random.randint(1,100)}")
    print(f"[rand 1] {random.randint(1,100)}")
else:
    random.seed()
    print(f"[rand 2] {random.randint(1,100)}")
    print(f"[rand 2] {random.randint(1,100)}")
    print(f"[rand 2] {random.randint(1,100)}")
» python test.py
[rand 2] 7
[rand 2] 52
[rand 2] 43
[rand 1] 16
[rand 1] 70
[rand 1] 97

#########################################################################################################################################

zip
#压缩
a = ['a', 'b', 'c']
b='123'
print(list(zip(a,b)))  #[('a', '1'), ('b', '2'), ('c', '3')]
print(dict(zip(a,b)))  #{'c': '3', 'b': '2', 'a': '1'}
for i,j in zip(a, b):   #同时遍历两个或更多的序列
  print(i,j)
# a 1
# b 2
# c 3

#解压(原理就是利用了解包参数的特性)
matrix = [[1, 2],[3, 4],[5,6]]
for i,j,k in zip(*matrix):  # <class 'zip'>
  print(i,j,k)
# 1 3 5
# 2 4 6

#矩阵置换
[list(_) for _ in zip(*matrix)] # [[1, 3, 5], [2, 4, 6]]
[[row[i] for row in matrix] for i in range(2)]
[[matrix[j][i] for j in range(3)] for i in range(2)]
[row[i] for i in range(2) for row in matrix]

#########################################################################################################################################

字典(py3.6中字典已经有序)
d = {'a': 1, 'b': 2}
d.update({'a':3,'c':4})             # {'c': 4, 'a': 3, 'b': 2}
print(d.pop('a','无a'))  # 类似于get,3
print(d.setdefault('d')) # None
print(d.setdefault('e','avatar')) # avatar
print(d.setdefault('b','akatsuki')) # 2
print(d)   # {'d': None, 'b': 2, 'c': 4, 'e': 'avatar'}

# dict.setdefault(key, default=None)
# key -- 查找的键值
# default -- 键不存在时,设置的默认键值
# get()方法类似,如果key在字典中,返回对应的值.如果不在字典中,则插入key及设置的默认值default,并返回default

#########################################################################################################################################

big-endian & little-endian
#include <stdbool.h>
bool is_big_endian() //如果字节序为big-endian,返回1,反之返回0
{
  unsigned short test = 0x1122;
  if(*( (unsigned char*) &test ) == 0x11)
    return true;
  else
    return false;
}
/*
big-endian:内存顺序和数字的书写顺序是一致的,方便阅读理解。
little-endian:在变量指针转换的时候地址保持不变,比如int64*转到int32*
目前看来是little-endian成为主流了
*/

#########################################################################################################################################

locals() & globals()
a=5
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

深拷贝与浅拷贝
import copy
a = [0,[1,],(2,),'str']
b=a #相当于&
c = a[:] #等价于copy.copy(a),相当于部分&
d = copy.copy(a)
e=copy.deepcopy(a) #此时d跟a无任何关系
a[0]=5
a[1][0] = 4

print ('a:',a)
print ('b:',id(b)==id(a),id(b[0])==id(a[0]),id(b[1])==id(a[1]),id(b[2])==id(a[2]),id(b[3])==id(a[3]),b)
print ('c:',id(c)==id(a),id(c[0])==id(a[0]),id(c[1])==id(a[1]),id(c[2])==id(a[2]),id(c[3])==id(a[3]),c)
print ('d:',id(d)==id(a),id(d[0])==id(a[0]),id(d[1])==id(a[1]),id(d[2])==id(a[2]),id(d[3])==id(a[3]),d)
print ('e:',id(e)==id(a),id(e[0])==id(a[0]),id(e[1])==id(a[1]),id(e[2])==id(a[2]),id(e[3])==id(a[3]),e)

'''
a: [5, [4], (2,), 'str']
b: True True True True True [5, [4], (2,), 'str']
c: False False True True True [0, [4], (2,), 'str']
d: False False True True True [0, [4], (2,), 'str']
e: False False False True True [0, [1], (2,), 'str']
'''

#########################################################################################################################################

and & or & not
x and y 返回的结果是决定表达式结果的值,如果x为真,则y决定结果,返回y;如果x为假,x决定了结果为假,返回x
x or y  跟and一样都是返回决定表达式结果的值
not     返回表达式结果的相反的值,如果表达式结果为真则返回false,如果表达式结果为假则返回true

#########################################################################################################################################

sub & subn & split
regex.sub(repl, string, count=0):
使用repl替换string中每一个匹配的子串,返回替换后的字符串.若找不到匹配,则返回原字符串
当repl是一个字符串时,任何在其中的反斜杠都会被处理
count用于指定最多替换次数,不指定时全部替换
subn同sub,只不过返回值是一个二元tuple,即(sub函数返回值, 替换次数)

import re
pattern = re.compile(r"like")
s1 = pattern.sub(r"love", "I like you, do you Like me?")
print(s1)     # I love you, do you love me?
print(re.subn(r'(\w+) (\w+)' ,r'\2 \1','i say, hello world!'))  #('say i, world hello!', 2)
#  re.split(pattern, string, maxsplit=0, flags=0)   flags用于指定匹配模式
print(re.split(r'[\s\,\;]+','a,b;; c d'))    #['a', 'b', 'c', 'd']

#########################################################################################################################################

列表切片赋值
a = [1, 2, 3, 4, 5]
a[2:3] = [0, 0]      #注意这里的用法(区别于a[2] = [0, 0])   [1, 2, 0, 0, 4, 5]
a[1:1] = [8, 9]      #[1, 8, 9, 2, 0, 0, 4, 5]
a[1:-1]=[]           #[1,5] ,等价于del a[1:-1]

#########################################################################################################################################

deque(链式存储结构,可以当栈和队列来使用)
'''
class collections.deque([iterable[, maxlen]])
Deques are a generalization of stacks and queues (the name is pronounced “deck” and is short for “double-ended queue”).
Deques support memory efficient appends and pops from either side of the deque with approximately the same O(1) performance in either direction.
Though list objects support similar operations, they are optimized for fast fixed-length operations and incur O(n) memory movement costs for pop(0) and insert(0, v) operations which change both the size and position of the underlying data representation.
If maxlen is not specified or is None, deques may grow to an arbitrary(任意的) length.
Otherwise the maxlen is full, when new items are added, a corresponding number of items are discarded from the opposite end.
maxlen会影响到append,extend,insert等增加队列长度这一类函数的行为，此时队列是循环队列
In addition to the above, deques support iteration, pickling, len(d), reversed(d), copy.copy(d), copy.deepcopy(d), membership testing with the in operator, and subscript references such as d[-1].
Indexed access is O(1) at both ends but slows to O(n) in the middle. For fast random access, use lists instead.
remove(value) Remove the first occurrence of value. If not found, raises a ValueError.
index(x[, start[, stop]]) Return the position of x in the deque (at or after index start and before index stop). Returns the first match or raises ValueError if not found.
Rotate the deque n steps to the right. If n is negative, rotate to the left. Rotating one step to the right is equivalent to: d.appendleft(d.pop()).
一般情况下list可以代替stack结构,但不能代替queue
'''

from collections import deque
Q=deque(range(5),maxlen=4)
Q.append(5)
Q.appendleft(4)
print(Q)              #deque([4, 2, 3, 4], maxlen=4)
print(Q.count(4))     #2
Q.clear()
Q+=[4,5,6,7,8]        #extend
Q.extendleft([2,3])   #extendleft() reverses the input order
print(len(Q),Q)       #4 deque([3, 2, 5, 6], maxlen=4)，遍历一个list对象，插入一个进deque对象，并不能像list那样直接拼接
print(4 in Q)
Q.pop()
Q.popleft()
Q.reverse()  #deque([5, 2], maxlen=4)
print(Q)

Q=deque(range(4))
Q.insert(1,5)   #第一个参数是位置，索引从1开始，数组才是从0开始索引
Q.insert(-2,6)
print(Q)              #deque([0, 5, 1, 6, 2, 3])
Q.rotate(8)
print(Q)              #deque([2, 3, 0, 5, 1, 6])
newQ=deque(reversed(Q))

def moving_average(iterable, n=3):
    # moving_average([40, 30, 50, 46, 39, 44]) --> 40.0 42.0 45.0 43.0
    it = iter(iterable)
    d = deque(itertools.islice(it, n-1))
    d.appendleft(0)
    s = sum(d)
    for elem in it:
        s += elem - d.popleft()
        d.append(elem)
        yield s / n

def tail(filename, n=10):
    'Return the last n lines of a file'
    with open(filename) as f:
        return deque(f, n)

#########################################################################################################################################

默认参数
def f(a,L=[]):
    L.append(a)
    return L
print(f(1)) #[1]
print(f(3,[1,2])) #[1, 2, 3]
print(f(2)) #[1, 2]
'''
Default parameter values are evaluated when the function definition is executed. This means that the expression is evaluated once,
when the function is defined, and that the same “pre-computed” value is used for each call.
该特性可以实现装饰器实现的统计调用次数的功能
'''

#if u dont want the default to be shared between subsequent calls ,u can write the function like this instead.
def f(a,L=None):
    if L is None:
        L=[]
    L.append(a)
    return L
print(f(1)) #[1]
print(f(2)) #[2]

i = 5
def f(arg=i):
  print(arg)
i = 6
f() #The default values are evaluated at the point of function definition in the defining scope, so that will print 5.
print(f.__defaults__) #(5,)

#########################################################################################################################################

md5
import hashlib
m=hashlib.md5(b"hello blockchain world, this is yeasy@github")
print(m.hexdigest())  # 1ee216d3ef1d217cd2807348f5f7ce19
'''
echo -n "hello blockchain world, this is yeasy@github"|md5sum
注意Linux下要去掉字符串末尾的\n
'''

#########################################################################################################################################

search: 匹配到就终止,只匹配一个,可指定起始位置跟结束位置
findall: 匹配所有,可指定起始位置跟结束位置
match: 从头开始匹配,最多匹配一个,可指定起始位置跟结束位置
import re
s='avatar cao nihao 1234,'
regex=re.compile(r'(ava\w+) cao (nihao)')
print(regex.search(s).group())     #avatar cao nihao
#group默认是group(0),返回全部
print(regex.search(s).groups())    #('avatar', 'nihao')

s='avat1ar cao avat2ar cao,'
regex=re.compile(r'(ava\w+) cao')
print(regex.findall(s))   #['avat1ar', 'avat2ar']
regex=re.compile(r'ava\w+ cao')
print(regex.findall(s))   #['avat1ar cao', 'avat2ar cao']

#注意r''的使用
re.findall(r'\[q\\w1','[q\w1')    #['[q\\w1']
re.findall('\\[q\\\w1','[q\w1')             #['[q\\w1']
re.findall('\[q\\w1','[q\w1')     #[],匹配不到的原因是python字符串也是用\转义特殊字符,\q被python理解成[
re.findall(r'\bor\b', 'which or orange ')   #['or'] 建议使用\b单词\b形式,如\bw+\b
re.findall('\bor\b', 'which or orange ')    #[]

[]
匹配所包含的任意一个字符
连字符 - 如果出现在字符串中间表示字符范围描述;如果如果出现在首位则仅作为普通字符
特殊字符仅有反斜线\保持特殊含义,用于转义字符.其它特殊字符如 *、+、? 等均作为普通字符匹配
脱字符 ^ 如果出现在首位则表示匹配不包含其中的任意字符;如果 ^ 出现在字符串中间就仅作为普通字符匹配

[\u4e00-\u9fa5]  # 匹配中文
^[^t]+           # 匹配不以t开头的字符串

#########################################################################################################################################

\w
s='as_6の5你ava'
print(re.findall(r'\w+',s)) # ['as_6の5你ava']
print(re.findall(r'\w+',s,re.ASCII)) # ['as_6', '5', 'ava']

For Unicode (str) patterns:
Matches Unicode word characters; this includes most characters that can be part of a word in any language,
as well as numbers and the underscore. If the ASCII flag is used, only [a-zA-Z0-9_] is matched.

#########################################################################################################################################

多行匹配/断言(re.S & re.M)
#\n匹配换行符,默认.不会匹配换行符,re.S也有同样效果,re.I忽略大小写
print(re.findall(r"a\d+b.+a\d+b","a23b\na34b"))  # []
print(re.findall(r"a\d+b(?:.|\n)+a\d+b","a23b\na34b"))  # ['a23b\na34b'] ?:意思是让findall,search等函数'看不见'括号,类似用法如re.findall(r'(?:\d{1,3}\.){3}\d{1,3}','192.168.1.33')
print(re.findall(r"a\d+b.+a\d+b","a23b\na34b",re.S))  # ['a23b\na34b']

#re.M：可以使^$标志将会匹配每一行,默认^和$只会匹配第一行
print(re.findall(r"^a(\d+)b","a23b\na34b"))  # ['23']
print(re.findall(r"^a(\d+)b","a23b\na34b",re.M))  # ['23', '34']

# 但是如果没有^标志,是无需re.M
print(re.findall(r"a(\d+)b","a23b\na34b"))  # ['23', '34']

#断言,且都是零宽
print(re.findall(r'\w+\.(?!com)\w+','www.com https.org'))   #['https.org'],不以...结束
print(re.findall(r'\w+(?<!www)\.\w+','www.com https.org'))  #['https.org'],不以...开头
print(re.findall(r'\w+\.(?=c.m)','www.com https.org'))      #['www.'],以...结束
print(re.findall(r'(?<=\w{5})\.\w+','www.com https.org'))   #['.org'],以...开头

#########################################################################################################################################

地板除(不管操作数为何种数值类型,总是会舍去小数部分,返回数字序列中比真正的商小的最接近的数字)
print(5//2)    #2
print(5//2.0)  #2.0
print(5//-2)   #-3

#########################################################################################################################################

延时绑定
# because y is not local to the lambdas, but is defined in the outer scope and it is accessed when the lambda is called — not when it is defined.
squares = [lambda: y**2 for _ in range(3)]
y=5
for square in squares:
    print(square()) # 25 25 25

squares = [lambda y=x: y**2 for x in range(3)]
for square in squares:
    print(square()) # 0 1 4  
      
squares=(lambda: x**2 for x in range(3))  # generator
for square in squares:
    print(square()) # 0 1 4




