import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mpl_toolkits.mplot3d import Axes3D

x=np.linspace(-3,3,50)
y1=2*x+1
y2=x**2

plt.figure()
plt.subplot(2,1,1)
plt.plot(x,y1)
plt.subplot(2,2,3)
plt.scatter(x,y2,s=10,c='green',alpha=.3) # 散点图
plt.text(2,3,'text content')

plt.figure()
plt.plot(x,y1,color='red',linewidth=.5,linestyle='--',label='up')
plt.plot(x,y2,label='down')
plt.legend() # 增加图例(配合plot的label参数)
plt.xlabel('x axis')
plt.ylabel('y axis')

# 3D绘图
fig = plt.figure()
ax=Axes3D(fig) 
X=np.arange(-4,4,.25)
Y=np.arange(-4,4,.25)
X,Y=np.meshgrid(X,Y)
R=np.sqrt(X**2+Y**2)
Z=np.sin(R)
ax.plot_surface(X,Y,Z)

plt.show()

############################################################################################

data=pd.Series([1,1,1,1,1,1])
print(data)
data.plot()
df=pd.DataFrame(np.random.randn(1000,4),index=np.arange(1000),columns=['A','B','C','D'])
df=df.cumsum()
print(df)
df.plot()
ax=df.plot.scatter(x='A',y='B',color='red',s=5)
df.plot.scatter(x='A',y='C',color='green',s=7,ax=ax)  # ax=ax保证相应的plot在同一个figure下面
plt.show()
