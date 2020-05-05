'''
静态方法和类方法都可以用类或者类实例调用,都可以被继承,不能访问实例属性,可以访问类属性
classmethod must have a reference to a class object as the first parameter(cls), whereas staticmethod can have no parameters at all.
'''
class Kls:
    def __init__(self, data):
        self.data = data
    def printd(self):
        print(self.data)

    @staticmethod
    def smethod(*arg):
        print('Static:',arg)

    @classmethod
    def cmethod(*arg):
        print('Class:', arg)

ik = Kls(23)
ik.smethod() #Static: ()
ik.cmethod() #Class: (<class '__main__.Kls'>,)
Kls.smethod() #Static: ()
Kls.cmethod() #Class: (<class '__main__.Kls'>,)


'''
cls is an object that holds class itself, not an instance of the class.
It's pretty cool because if we inherit our Date class, all children will have from_string defined also.
'''
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
    What this means is that even if the Date class is subclassed, the subclasses will still create plain Date object (without any property of the subclass).
    '''
    @staticmethod
    def s_from_string(date_as_string):
        day, month, year = map(int, date_as_string.split('-'))
        return Date(day, month, year)

    '''
    We have a date string that we want to validate somehow. This task is also logically bound to Date class we've used so far, but still doesn't require instantiation of it.
    Often there is some functionality that relates to the class, but does not need the class or any instance(s) to do some work.
    Perhaps something like setting environmental variables, changing an attribute in another class, etc.
    In these situation we can also use a function, however doing so also spreads the interrelated code which can cause maintenance issues later.
    '''
    @staticmethod
    def is_date_valid(date_as_string):
        day, month, year = map(int, date_as_string.split('-'))
        return day <= 31 and month <= 12 and year <= 3999

date = Date.from_string('11-09-2012')
print(Date.is_date_valid('11-09-2012'))
