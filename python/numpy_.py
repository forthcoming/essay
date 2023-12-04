import numpy as np
import pandas as pd


def test_pandas():
    # 读excel表格,读csv用pd.read_csv
    # df = pd.read_excel('map.xlsx',
    #                    sheet_name='Sheet2',
    #                    header=1,  # header指定开始读取的行号
    #                    dtype={'name': str, 'id': int},
    #                    names=['name', 'id', 'score']
    #                    )
    df = pd.DataFrame(np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]]), index=[5, 'six', 7], columns=['A', 'B', 'C'])
    print(df)
    '''
         A  B  C
    5    0  1  2
    six  3  4  5
    7    6  7  8
    '''
    print(df.shape)  # (3, 3), tuple类型
    print(df.index)  # Index([5, 'six', 7], dtype='object')
    print(df.columns)  # Index(['A', 'B', 'C'], dtype='object')
    print(df['A'].values)  # [0, 3, 6], numpy.ndarray类型
    print(df % 2 == 0)
    '''
         A      B      C
    5     True  False   True
    six  False   True  False
    7     True  False   True
    '''
    print(df[df['C'] % 2 == 0])  # 查找所有满足C列条件的所有行
    '''
       A  B  C
    5  0  1  2
    7  6  7  8
    '''
    for name in df.columns:
        column = df[name]  # pandas.core.series.Series类型
        print(column)
    for index in df.index:
        print(df.loc[index])  # pandas.core.series.Series类型

    for index in df.index:
        for name in df.columns:
            print(df.loc[index][name])


np.cross(np.array([1, 2, 3]), np.array([-1, 2, 0]))  # 两列向量叉积 [-6 -3 4]
np.exp(np.array([1, 2]))
np.sinh(2)  # 双曲正弦
np.inf  # infinity
np.pi

np.fromstring('abcdefgh', dtype=np.int8)  # [ 97  98  99 100 101 102 103 104]
np.linspace(0, 2, 4)  # 4 numbers from 0 to 2   [.0 .66666667 1.33333333 2.]
np.logspace(0, 2, 5)  # 产生10^0到10^2有5个元素的等比数列   [1. 3.16227766 10. 31.6227766 100.]
np.zeros((3, 4))
np.nonzero(
    [1, 2, 0, 0, 3, 0])  # (array([0, 1, 4], dtype=int64),)  Return the indices of the elements that are non-zero.
np.diag([1, 2, 3])  # 对角方阵
np.eye(2)  # 单位方阵
np.ones((2, 3, 4), dtype=np.int16)  # 类似于[[[1 for j in range(4)] for i in range(3)] for k in range(2)]
np.empty((2,
          3))  # creates an array whose initial content is random and depends on the state of the memory. By default, the dtype of the created array is float64
a = np.arange(24).reshape(2, 3, 4)  # 三维数组
'''
[   
    [   
        [ 0,  1,  2,  3],
        [ 4,  5,  6,  7],
        [ 8,  9, 10, 11]
    ],

    [
        [12, 13, 14, 15],
        [16, 17, 18, 19],
        [20, 21, 22, 23]
    ]
    
]
a.shape  # (2, 3, 4)
a.ndim   # 3
a.dtype.name  # int32
a.itemsize   # 4 ,bytes per element
a.size       # 24

dx,dy,dz=2,3,4
a=[[[k+j for k in range(dz)] for j in range(i,i+dz*(dy-1)+1,dz)] for i in range(0,24,24//dx)]
'''
b = np.array([[1, 2, 3], [5, 6, 7]])
b.flags.writeable = False  # Make an array immutable (read-only)
b[:, 1]  # each row in the second column of b  [2,6]
b[0:1, :]  # [[1 2 3]]
b[-1]  # [5 6 7]
c = np.array([[1, 2], [3, 4]], dtype=complex)
'''
array([[ 1.+0.j,  2.+0.j],
       [ 3.+0.j,  4.+0.j]])
'''

a = np.array([20, 30, 40, 50])
b = np.arange(4)
a - b  # [20 29 38 47] A new array is created and filled with the result.
b ** 2
a < 35  # array([ True, True, False, False], dtype=bool)
a[2] = 4
a[::-1]  # reversed a  [50  4 30 20]

A = np.arange(6).reshape(2, 3)
B = np.arange(6).reshape(3, 2)
A @ B  # matrix product   [[10 13] [28 40]]
A = np.arange(6).reshape(2, 3)
B = np.arange(6).reshape(2, 3)
A * B  # elementwise product  [[ 0  1  4] [ 9 16 25]]

# Some operations, such as += and *=, act in place to modify an existing array rather than create a new one.
a = np.ones((2, 3), dtype=int)
b = np.random.random((2, 3))  # 随机生成0到1之间的小数
b += a
# a+=b    #TypeError: Cannot cast ufunc add output from dtype('float64') to dtype('int32') with casting rule 'same_kind'
b.sum()
b.min()
b.max()
b.mean()

b = np.arange(12).reshape(3, 4)
b.sum(axis=0)  # sum of each column   [12 15 18 21]
b.min(axis=1)  # min of each row      [0, 4, 8]
b.cumsum(axis=1)  # cumulative sum along each row
'''
array([[ 0,  1,  3,  6],
       [ 4,  9, 15, 22],
       [ 8, 17, 27, 38]])
'''

c = np.array([
    [
        [0, 1, 2],
        [10, 12, 13]
    ],
    [
        [100, 101, 102],
        [110, 112, 113]
    ]
]
)
d = [i for i in c.flat]  # 依次访问每个元素
c[1, ...]  # same as c[1,:,:] or c[1]  [[100 101 102] [110 112 113]]
c[..., 2]  # same as c[:,:,2]   [[2 13] [102 113]]

a = np.floor(10 * np.random.random((3, 4)))  # [[2. 4. 0. 6.] [1. 6. 6. 5.] [6. 1. 4. 2.]]
a.T  # 转置   [[2. 1. 6.] [4. 6. 1.] [0. 6. 4.] [6. 5. 2.]]
a.ravel()  # flatten the array   [2. 1. 6. 4. 6. 1. 0. 6. 4. 6. 5. 2.]
# a.shape = 6, 2  #自身改变要求正好合适
a.resize(4, 5)  # 自身改变,功能更强,超出部分用0补充

a = np.arange(12)
b = a  # no new object is created
b is a  # a and b are two names for the same ndarray object
b.shape = 3, 4  # changes the shape of a
a.shape  # (3, 4)

a = np.arange(4).reshape(2, 2)
b = np.arange(4, 8).reshape(2, 2)
np.vstack((a, b))  # [[0 1] [2 3] [4 5] [6 7]]
np.hstack((a, b))  # [[0 1 4 5] [2 3 6 7]]
a = np.arange(24).reshape(2, 12)
np.hsplit(a,
          3)  # Split a into 3 [ array([[0,1,2,3],[12,13,14,15]]), array([[4,5,6,7],[16,17,18,19]]), array([[8,9,10,11],[20,21,22,23]]) ]
np.hsplit(a, (3,
              4))  # Split a after the third and the fourth column [array([[0,1,2],[12,13,14]]), array([[3],[15]]), array([[4,5,6,7,8,9,10,11],[16,17,18,19,20,21,22,23]])]

# np.linalg.det(a)    #返回的是矩阵a的行列式
# np.linalg.eig(a)    #矩阵a的特征值和特征向量
# np.linalg.inv(a)    #矩阵a的逆矩阵


x = np.linspace(0, 2 * np.pi, 10)
y = np.sin(x)
'''
对数组x中的每个元素进行正弦计算,返回一个同样大小的新数组
计算之后x中的值并没有改变,而是新创建了一个数组保存结果。
如果我们希望将sin函数所计算的结果直接覆盖到数组x上去的话,可以将要被覆盖的数组作为第二个参数传递给ufunc函数。
'''
t = np.sin(x, x)
x
'''
array([  0.00000000e+00,   6.42787610e-01,   9.84807753e-01,
         8.66025404e-01,   3.42020143e-01,  -3.42020143e-01,
        -8.66025404e-01,  -9.84807753e-01,  -6.42787610e-01,
        -2.44921271e-16])
'''
id(t) == id(x)  # True

# x = np.array([i * .001 for i in range(10000000)])
# start = time.clock()
# np.sin(x,x)
# print("numpy.sin:", time.clock() - start)

# x = [i * .001 for i in range(10000000)]
# start = time.clock()
# for i, t in enumerate(x):
#   x[i] = np.sin(t)
# print("numpy.sin:", time.clock() - start)

# x = [i * .001 for i in range(10000000)]
# start = time.clock()
# for i, t in enumerate(x):
#     x[i] = math.sin(t)
# print("math.sin:", time.clock() - start)
'''
OUT:
numpy.sin: 0.11066219182106055
numpy.sin: 8.58892698473108
math.sin: 2.561601807457043
'''

'''
atan2(a,b)是4象限反正切,它的取值不仅取决于正切值a/b,还取决于点 (b, a) 落入哪个象限
当点(b, a) 落入第一象限时,atan2(a,b)的范围是 0 ~ pi/2
当点(b, a) 落入第二象限时,atan2(a,b)的范围是 pi/2 ~ pi
当点(b, a) 落入第三象限时,atan2(a,b)的范围是 －pi～－pi/2
当点(b, a) 落入第四象限时,atan2(a,b)的范围是 -pi/2～0

而 atan(a/b) 仅仅根据正切值为a/b求出对应的角度(可以看作仅仅是2象限反正切)
当 a/b > 0 时,atan(a/b)取值范围是 0 ~ pi/2
当 a/b < 0 时,atan(a/b)取值范围是 -pi/2～0

故 atan2(a,b) = atan(a/b) 仅仅发生在 点 (b, a) 落入第一象限(b>0, a>0)或第四象限(b>0, a<0)
当点(b, a)落入第二、三象限时,很显然atan2(a,b) 不等于 atan(a/b),并且atan2(a,b)也不可能等于 2*atan(a/b)
这是因为假如点 (b, a) 落入第二象限，则 a/b<0,故atan(a/b)取值范围始终是 -pi/2～0,2*atan(a/b) 的取值范围是－pi～0
然而atan2(a,b)的范围是 pi/2 ~ pi,故不可能有atan2(a,b) = 2*atan(a/b),假如点(b, a) 落入第三象限，则则 a/b>0
故 atan(a/b) 取值范围是 0 ~ pi/2,2*atan(a/b) 的取值范围是 0 ~ pi,而此时atan2(a,b)的范围是 －pi～－pi/2,很显然atan2(a,b) = 2*atan(a/b)
举个最简单的例子,a = 1, b = -1,则 atan(a/b) = atan(-1) = -pi/4, 而 atan2(a,b) = 3*pi/4
'''

'''
当使用布尔数组b作为下标存取数组x中的元素时,将收集数组x中所有在数组b中对应下标为True的元素
使用布尔数组作为下标获得的数组不和原始数组共享数据空间
'''
a = np.arange(6).reshape(2, 3)  # [[0 1 2] [3 4 5]]
b = a > 3  # [[False False False] [False  True  True]]
a[b]  # 这里b的元素类型必须是bool  [4 5]
a = np.arange(12) ** 2  # [0 1 4 9 16 25 36 49 64 81 100 121]
i = np.array([1, 1, 3, -4, 5])
a[i]  # [1 1 9 64 25]  the elements of a at the positions i
j = np.array([[3, 4], [9, 7]])  # a bidimensional array of indices
a[j]  # [[ 9 16] [81 49]]  the same shape as j

# a,b,c共享数据存储内存区域
a = np.array([1, 2, 3, 4])
b = a.reshape(2, 2)
c = a[:]  # 与list的切片操作不同!!
# print(b)
# print(c)
a[3] = -1
# print(b)
# print(c)


a = np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]], dtype=np.float32)
b = a[::2, ::2]  # 切片操作  [[0. 2.] [6. 8.]]
b[0][0] = -1  # a也跟着变
a = np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]], dtype=np.float32)
b = a[::2, [0, 2]]  # 非切片操作   [[0.  2.] [ 6.  8.]]
b[0][0] = -1  # a不变

a = np.arange(0, 60, 10)  # array([ 0, 10, 20, 30, 40, 50])
a.shape  # (6,)
a = np.arange(0, 60, 10).reshape(-1, 1)  # -1 means "whatever is needed"
'''
array([[ 0],
       [10],
       [20],
       [30],
       [40],
       [50]])
'''
a.shape  # (6, 1)
