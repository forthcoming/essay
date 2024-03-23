import numpy as np  # 定长,元素类型唯一,支持矩阵运算等优点使其比python数组更快
import pandas as pd


def test_pandas():
    # 读excel用read_excel,excel为二进制文件,不用指定编码格式
    # 读csv,txt用read_csv,txt需要指定delimiter参数
    # df = pd.read_excel('map.xlsx',
    #                    sheet_name='Sheet2',
    #                    header=1,  # header指定开始读取的行号
    #                    dtype={'name': str, 'id': int},
    #                    names=['name', 'id', 'score']
    #                    )
    df = pd.DataFrame([[0, 1, 2], [3, 4, 5], [6, 7, 8]], index=[5, 'six', 7], columns=['A', 'B', 'C'])
    print(df)
    '''
         A  B  C
    5    0  1  2
    six  3  4  5
    7    6  7  8
    '''
    df = df.drop_duplicates(subset=['C'], keep='last')  # 去除C列中重复的行,保留重复行中的最后一行数据
    print(df.shape)  # (3, 3), tuple类型
    print(df.index)  # Index([5, 'six', 7], dtype='object')
    print(df.columns)  # Index(['A', 'B', 'C'], dtype='object')
    print(df['A'].values)  # [0, 3, 6], numpy.ndarray类型
    print(df.iloc[:, 1])  # 第二列的所有行,pandas.core.series.Series类型
    print(df.iloc[1, :])  # 第二行的所有列的转秩,pandas.core.series.Series类型
    print(df.loc['six', ["B", "C"]])  # 第six行的B、C列,pandas.core.series.Series类型
    print(df.iloc[:, [1, 2]])  # 第二、三列的所有行,pandas.core.frame.DataFrame类型
    print(df % 2 == 0)  # pandas.core.frame.DataFrame类型
    '''
         A      B      C
    5     True  False   True
    six  False   True  False
    7     True  False   True
    '''
    print(df[(df['C'] > 2) & (df['C'] % 2 == 0)])  # 查找满足C列条件的所有行, pandas.core.frame.DataFrame类型
    '''
       A  B  C
    7  6  7  8
    '''

    for name in df.columns:
        column = df[name]  # pandas.core.series.Series类型
        print(column)
    for index in df.index:
        print(df.loc[index])  # loc对应的是df.index, iloc对应的是从0开始的索引, pandas.core.series.Series类型

    for name in df.columns:
        for index in df.index:
            print(df[name][index])

    for index in df.index:
        for name in df.columns:
            print(df.loc[index][name])

    df = df.rename(columns={'A': 'a', 'B': 'b'})
    df.describe()  # 以每列为单位,统计count,mean,max,min等信息

    print(pd.DataFrame([df['a'], df['b']]))
    '''
       5  six  7
    a  0    3  6
    b  1    4  7
    '''
    print(pd.DataFrame([df['a'], df['b']]).T)
    '''
         a  b
    5    0  1
    six  3  4
    7    6  7
    '''

    df['new'] = ['x', np.NaN, 'x']  # 新增列
    '''
         a  b  C  new
    5    0  1  2  x
    six  3  4  5  NaN
    7    6  7  8  x
    '''
    df = df.dropna()  # 删除元素为NaN的所有行
    '''
       a  b  C   new
    5  0  1  2   x
    7  6  7  8   x
    '''
    df['C'] = df['C'].astype(float)
    df = df.merge(pd.DataFrame([[6, 5], [4, 3]], columns=['a', 'd']), on='a', how='inner')  # join
    '''
       a  b    C new  d
    0  6  7  8.0   x  5
    '''
    # pd.concat([df1, df2], axis=0, ignore_index=False)  # axis=0代表垂直方向拼接,axis=1代表水平方向拼接


def one_dimension():
    arr_a = np.array([20, 30, 40, 50])  # shape=(4,), ndim: 1, 注意区别一维和二维shape的区别
    arr_b = np.arange(4)
    print(arr_a - arr_b)  # [20 29 38 47]
    print(arr_b ** 2)  # [0 1 4 9]
    print(arr_a < 35)  # [True True False False]
    arr_a[2] = 4
    print(arr_a[::-1])  # [50 4 30 20]

    print(np.frombuffer(b'abc', dtype=np.int8))  # [97  98  99]
    print(np.linspace(0, 2, 4))  # [0,2]之间4个元素的等差数列 [.0 .66666667 1.33333333 2.]
    print(np.logspace(0, 2, 4))  # 产生10^0到10^2之间4个元素的等比数列 [1. 4.64158883 21.5443469 100.]
    print(np.cross([1, 2, 3], [-1, 2, 0]))  # 两列向量叉积 [-6 -3 4]


def two_dimension():
    print(np.array([[1], [2], [3], [4], [5], [6]]))  # shape: (6, 1), ndim: 2
    print(np.array([[1, 2, 3, 4, 5, 6]]))  # shape: (1, 6), ndim: 2
    print(np.zeros((3, 4)))  # 3 x 4阶0矩阵
    print(np.diag([1, 2, 3]))  # 3阶对角方阵
    print(np.eye(2))  # 单位方阵
    print(np.nonzero([1, 2, 0, 3]))  # 返回非0元素的索引[0, 1, 3]
    print(np.array([[1, 2], [3, 4]], dtype=complex))
    '''
    array([[ 1.+0.j,  2.+0.j],
           [ 3.+0.j,  4.+0.j]])
    '''

    arr = np.array([[1, 2, 3], [5, 6, 7]])
    arr.flags.writeable = False  # Make an array immutable (read-only)
    print(arr[:, 1])  # 所有行的第二列, [2,6]
    print(arr[0:1, :])  # [[1 2 3]]
    print(arr[-1])  # [5 6 7]

    A = np.arange(6).reshape(2, 3)
    B = np.arange(6).reshape(3, 2)
    print(A @ B)  # matrix product   [[10 13] [28 40]]
    A = np.arange(6).reshape(2, 3)
    B = np.arange(6).reshape(2, 3)
    print(A * B)  # elementwise product  [[ 0  1  4] [ 9 16 25]]

    # Some operations, such as += and *=, act in place to modify an existing array rather than create a new one.
    C = np.ones((2, 3), dtype=int)
    D = np.arange(6).reshape(2, 3)
    D += C  # [[1 2 3] [4 5 6]]
    print(D.sum(), D.min(), D.max(), D.mean())  # 21 1 6 3.5
    print(D.sum(axis=0))  # sum of each column  [5 7 9]
    print(D.min(axis=1))  # min of each row   [1 4]
    print(D.cumsum(axis=1))  # cumulative sum along each row [[1  3  6] [4  9 15]]

    arr = np.floor(10 * np.random.random((3, 4)))  # [[2. 1. 5. 5.] [1. 1. 7. 0.] [7. 8. 2. 0.]]
    print(arr.T)  # 转置
    arr.resize(5, 3)  # 自身改变,超出部分用0补充
    print(arr)  # [[2. 1. 5.] [5. 1. 1.] [7. 0. 7.] [8. 2. 0.] [0. 0. 0.]]

    arr = np.arange(4)
    print(arr[:, np.newaxis])  # shape: (4, 1), ndim: 2


def three_dimension():
    # 类似于[[[1 for j in range(4)] for i in range(3)] for k in range(2)]
    print(np.ones((2, 3, 4), dtype=np.int16))

    arr = np.arange(24).reshape(2, 3, 4)
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
    '''
    print(arr.ravel())  # [ 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23]
    print(arr[1, ...])  # same as arr[1,:,:] or c[1]  [[12 13 14 15] [16 17 18 19] [20 21 22 23]]
    print(arr[..., 2])  # same as arr[:,:,2]   [[ 2  6 10] [14 18 22]]

    assert arr.shape == (2, 3, 4)
    assert arr.ndim == 3
    assert arr.dtype.name == 'int32'
    assert arr.itemsize == 4  # bytes per element
    assert arr.size == 24  # 24


def common():
    """
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
    """

    arr = np.arange(6).reshape(2, 3)  # [[0 1 2] [3 4 5]]
    # 当使用布尔数组b作为下标存取数组x中的元素时,将收集数组x中所有在数组b中对应下标为True的元素
    # 使用布尔数组作为下标获得的数组不和原始数组共享数据空间
    bool_arr = arr > 3  # [[False False False] [False  True  True]]
    print(arr[bool_arr])  # 这里b的元素类型必须是bool  [4 5]
    arr = np.arange(12) ** 2  # [0 1 4 9 16 25 36 49 64 81 100 121]
    i = np.array([1, 1, 3, -4, 5])
    print(arr[i])  # [1 1 9 64 25]  the elements of arr at the positions i
    j = np.array([[3, 4], [9, 7]])  # a bidimensional array of indices
    print(arr[j])  # [[9 16] [81 49]]  the same shape as j

    print(np.inf, np.pi, np.sinh(2), np.cos([1, 2]))  # sinh双曲正弦, cos对数组中的每个元素进行余弦计算, 返回一个同样大小的新数组

    # a,b,c,d共享数据存储内存区域
    a = np.arange(12)
    b = a  # no new object is created, a and b are two names for the same ndarray object
    c = a.reshape(3, 4)
    d = a[:]  # 与list切片操作不同!!

    e = np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]], dtype=np.float32)
    f = e[::2, ::2]  # 切片操作  [[0. 2.] [6. 8.]]
    f[0][0] = -1  # e也跟着变
    print(e)
    e = np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]], dtype=np.float32)
    f = e[::2, [0, 2]]  # 非切片操作   [[0.  2.] [ 6.  8.]]
    f[0][0] = -1  # e不变
    print(e)

    g = np.array([[0, 1], [2, 3]])
    h = np.array([[4, 5], [6, 7]])
    np.vstack((g, h))  # [[0 1] [2 3] [4 5] [6 7]]
    np.hstack((g, h))  # [[0 1 4 5] [2 3 6 7]]
    np.linalg.det(g)  # 返回矩阵的行列式
    np.linalg.eig(g)  # 矩阵的特征值和特征向量
    np.linalg.inv(g)  # 矩阵的逆矩阵

    i = np.arange(12).reshape(2, 6)
    # 将向量拆分成3组 ([[0, 1],[6, 7]]), array([[2, 3],[8, 9]]), array([[4, 5],[10, 11]])]
    np.hsplit(i, 3)
    # 在第三列和第四列之后拆分向量[array([[0, 1, 2],[6, 7, 8]]), array([[3],[9]]), array([[ 4,  5],[10, 11]])]
    np.hsplit(i, (3, 4))


if __name__ == "__main__":
    test_pandas()
    # one_dimension()
    # two_dimension()
    # three_dimension()
    # common()
