import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.font_manager import FontProperties
from mpl_toolkits.mplot3d import Axes3D

font = FontProperties(fname='/System/Library/Fonts/Hiragino Sans GB.ttc')
plt.rcParams['font.sans-serif'] = ['SimSun']  # 指定默认字体为宋体,Windows下设置
plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题,Windows下设置


def draw_line():  # 曲线图
    x = np.linspace(-3, 3, 50)
    y1 = 2 * x + 1
    y2 = x ** 2

    plt.subplot(1, 2, 1)  # 一行两列中的第一个图
    plt.plot(x, y1, color='red', linewidth=.5, linestyle='--', label='up')
    plt.plot(x, y2, label='down')  # 一个画布上画多张图
    plt.title("这是title", fontproperties=font)
    plt.xlabel('x axis')  # x轴说明
    plt.ylabel('y axis')
    plt.legend()  # 增加图例,需要画图函数有label参数
    plt.text(0, 3, '这是text', fontproperties=font)
    plt.xticks([-3, -2, -1, 0, 1, 2, 3], fontsize=5, color='g')  # 设置x轴刻度
    plt.ylim(-2, 10)  # 设置y轴刻度范围
    plt.grid(axis='y', ls='--')  # 设置y轴网格

    plt.subplot(1, 2, 2)
    plt.plot(['one', 'two', 'three', 'four'], [1, 2, 3, 4])

    plt.show()  # 画图并结束当前画布


def draw_scatter():  # 散点图
    # 读excel表格,读csv用pd.read_csv
    # df = pd.read_excel('map.xlsx',
    #                    sheet_name='Sheet2',
    #                    header=1,  # header指定开始读取的行号
    #                    dtype={'name': str, 'id': int},
    #                    names=['name', 'id', 'score']
    #                    )
    # print(df.name, df.id, df.score)
    # for row in range(df.shape[0]):
    #     print(pd.isna(df.loc[row]['name']))

    # np.random.randn(m, n)产生m行n列服从标准正态分布的随机数矩阵
    df = pd.DataFrame(np.random.randn(20, 3), index=np.arange(20), columns=['A', 'B', 'C'])
    print(df)
    print(df.shape)  # (20, 3)
    plt.scatter(df.A, df.B, color='red', s=20, alpha=.6)
    plt.scatter(df.A, df.C, color='green', s=10)
    plt.show()


def draw_bar():  # 柱状图
    subjects, scores = ['English', 'Chinese', 'Math'], [70, 80, 50]
    plt.bar(subjects, scores, width=.7)  # width代表柱体间距
    for subject, score in zip(subjects, scores):
        plt.text(subject, score + 1, score, ha='center', fontsize=8)  # ha代表对齐方式
    plt.bar(subjects, [10, 20, 30], width=.7, bottom=scores)  # bottom意思是画堆叠柱状图
    plt.show()


def draw_hist():  # 直方图,横轴表示数据类型,纵轴表示分布情况
    x = np.random.randint(0, 10, 100)
    plt.hist(x, bins=5, density=True)  # bins意思是多少个数据一组,density=True会以概率分布呈现
    plt.show()


def draw_pie():  # 饼图
    plt.pie([10, 20, 30], labels=['A', 'B', 'C'], autopct='%.2f%%')
    plt.show()


def draw_3d():  # 3D绘图
    fig = plt.figure()  # 设置画布
    ax = Axes3D(fig)
    fig.add_axes(ax)
    x = np.arange(-4, 4, .25)
    y = np.arange(-4, 4, .25)
    x, y = np.meshgrid(x, y)
    z = np.sqrt(16 - x ** 2 - y ** 2)
    ax.plot_surface(x, y, z)
    plt.show()


def move_axes():
    x = np.arange(-50, 51)
    y = x ** 2
    ax = plt.gca()  # 获取当前坐标轴,通过spines,找到top,bottom,left,right
    ax.spines['right'].set_color("none")  # 将右侧坐标轴隐藏
    ax.spines['top'].set_color("none")
    ax.spines['left'].set_position(('axes', .5))  # 轴上的比例,介于[0,1]之间
    ax.spines['bottom'].set_position(('data', 0))  # data表示按数值移动,其后数字代表移动到y轴的刻度值
    plt.plot(x, y)
    plt.show()


if __name__ == "__main__":
    # draw_line()
    # draw_bar()
    # draw_hist()
    # draw_scatter()
    # draw_pie()
    # draw_3d()
    move_axes()
