# 语法糖@
def deco(func):
  count=0   #计数
  def _deco(*args, **kw):
    nonlocal count  #注意这里要用nonlocal
    count+=1
    print(f"第{count}次调用")
    ret = func(*args, **kw)
    print(f"after myfunc() called result: {ret}")
    return ret
  return _deco

@deco   #相当于myfunc=deco(myfunc)
def myfunc(a, b):
  return a + b

myfunc(4, 5)
myfunc(6, 7)

# 第1次调用
# after myfunc() called result: 9
# 第2次调用
# after myfunc() called result: 13
#使用内嵌包装函数_deco来确保每次新函数都被调用，
#内嵌包装函数的形参和返回值与原函数相同，装饰函数返回内嵌包装函数对象

#########################################################################################################################

# 装饰器带参数
import functools
def logger(text):
  def decorator(func):
    @functools.wraps(func)  #作用是让func.__name__能正确显示
    def wrapper(*args, **kw):
      print('{} {}():'.format(text, func.__name__))
      return func(*args, **kw)
    return wrapper
  return decorator

@logger('DEBUG')  #相当于today=logger('DEBUG')(today)
def today():
  print('2015-3-25')

today()
print(today.__name__)
'''
DEBUG today():
2015-3-25
today
'''
#和上一示例相比在外层多了一层包装

#########################################################################################################################

# 装饰器装饰类方法(装饰器装饰类与装饰函数原理一样,例如单例模式)
def log(fn):
  def wrapper(*a,**b):
    print('in wrapper,start!')
    a=fn(*a,**b)
    print('end !')
    return a
  return wrapper

class A:
  @log
  def func(self,a=1,b=3):
    return a+b

print(A().func())
'''
in wrapper,start!
end !
4
'''

#########################################################################################################################

# using classes as decoration mechanisms instead of functions,In addition, it's more powerful.
# which basically means it must be callable. Thus, any classes we use as decorators must implement__call__.
# https://www.artima.com/forums/flat.jsp?forum=106&thread=240808
class entryExit:
  def __init__(self, f):
    self.f = f
  def __call__(self,*args,**kw):
      print ("Entering", self.f.__name__)
      _=self.f(*args,**kw)
      print ("Exited", self.f.__name__)
      return _

@entryExit   # 等价于func=entryExit(func)
def func(a,b):
  return a+b

print(func(3,5))
# Entering func
# Exited func
# 8
print(type(func))  #<class '__main__.entryExit'>

#########################################################################################################################

# Decorators with Arguments
# If there are decorator arguments, the function to be decorated is not passed to the constructor!

class decoratorWithArguments:
  def __init__(self, arg1):
    self.arg1 = arg1

  def __call__(self, f):
   """
   If there are decorator arguments, __call__() is only called
   once, as part of the decoration process! You can only give
   it a single argument, which is the function object.
   """
   print("Inside __call__()")
   def wrapped_f(*args):
     print("Decorator arguments:", self.arg1)
     f(*args)
     print("After f(*args)")
   return wrapped_f

@decoratorWithArguments("hello")   # 等价于decoratorWithArguments("hello")(sayHello)
def sayHello(a1, a2):
    print('sayHello arguments:', a1, a2)

sayHello("say", "goodbye")
# Inside __call__()
# Decorator arguments: hello
# sayHello arguments: say goodbye
# After f(*args)
'''
the constructor is now used to capture the decorator arguments, but the object __call__() can no longer be used as the decorated function call,
so you must instead use __call__() to perform the decoration --it is nonetheless surprising the first time you see it because it's acting so much differently than the no-argument case, and you must code the decorator very differently from the no-argument case.
'''
