##### 相似三角形
```python
两角分别对应相等的两个三角形相似
两边成比例且夹角相等的两个三角形相似
三边成比例的两个三角形相似
一条直角边与斜边成比例的两个直角三角形相似
根据以上判定定理,可以推出下列结论:
三边对应平行的两个三角形相似
一个三角形的两边和三角形任意一边上的中线与另一个三角形的对应部分成比例,那么这两个三角形相似
```

---
##### 凸性判断
```python
设函数f(x)在[a,b]上可导,则f(x)是[a,b]上的下凸函数的充要条件是f'(x)在[a,b]上单调增
下凸性质:
若a,b大于0且a+b=1,则af(x1)+bf(x2)>f(ax1+bx2)
```

---
##### 最小二乘法
```python
设回归直线y=a+bx
线性代数角度(前提是A列满秩,否则应该用伪逆A.+来求解)
A[a;b]=y  =>  [a;b]= (A.TA).-1A.Ty, 几何意义是先将y投影到C(A)中再求解a,b
A[a;b]=y  =>  QR[a;b]= y  =>  [a;b]= R.-1Q.Ty
数分角度
S(a,b)=∑[yk-(a+bxk)]^2，分别对a,b求偏导等于0
```

---
##### 多元函数有界闭域上的最值
```python
处理过程类似于一元函数,先在定义域内找出所有极值,然后再加上边界上的最大最小值,便构成该区域内的最值
{max(f(x,y)=x^2-y^2+4),x^2+y^2/4≤1}
所有可能点有(0,0), (0,2), (0,-2), (1,0), (-1,0), 且max{f(x,y)}=f(1,0)=f(-1,0)=5
```

---
##### 曲面极值点
```python
设函数f(x,y)在(a,b)的两个偏导数均存在,若(a,b)是f(x,y)的一个极值点,则函数在该点处的所有偏导数等于0
注意: 
所有偏导数等于0的点不一定是极值点,如f(x,y)=xy在(0,0)处,需要根据他的Hessian矩阵来判断
偏导数不存在的点也可能是极值点如f(x,y)=√(x^2+y^2)
```

---
##### Fermat定理
```python
若函数f(x)在x0处可导且f(x0)是f(x)的一个极值,则f'(x0)=0,即可导极值点的导数为0
注意: 
导数等于0处的点不一定是极点,如y=x^3在x=0处
不可导点也可能是极值点,如y=|x|在x=0处
```

---
##### 极值点
```python
若f(x)可导且导函数在x0的两侧异号,则x0是f(x)的极值点
极值点充分条件: 
若f(x)在x0处具有二阶导数,且f'(x0)=0
则当f''(x0)>0时x0是函数f(x)的极小值点,当f''(x0)<0时x0是函数f(x)的极大值点(等价于f'(x)在x0的两侧异号)
若f(x)在x0处具有n阶导数,且前1到n-1阶导函数在x0处等于0
则当n是奇数时x0非极值点,当n是偶数时,若fn(x0)>0,x0是函数f(x)的极小值点,当fn(x0)<0,x0是函数f(x)的极大值点 
```

---
##### common
```python
积分中值定理: 
若f(x)在闭区间[a,b]上连续,则在[a,b]上至少存在一点ξ使得∫(a,b)f(x)dx=f(ξ)(b-a)

零点存在定理: 
若函数f(x)在[a,b]上连续且f(a)f(b)<0,则存在ξ∈(a,b)使f(ξ)=0

罗比达法则:
处理0/0型或∞/∞型不定式要注意f'(x)/g'(x)在某点处极限存在或者为无穷大量,反例如x^2sin(1/x)/sinx在x=0处的极限

单调性:
非常数函数f(x)在[a,b]连续(a,b)内可导,则f(x)在[a,b]上严格单增的充要条件是f'(x)>=0

分部积分(顺序是反对幂三指): 
若u(x),v(x)连续可导,则(uv)'=u'v+uv'  =>  uv'=(uv)'-vu'  =>  ∫u(x)dv(x)=u(x)v(x)-∫v(x)du(x)

Beta函数: 
B(α,β)=∫(0,1)t^(α-1)(1-t)^(β-1)dt    α,β>0

二项式定理:
(a＋b)^n＝C(n,0)a^n＋C(n,1)a^(n-1)b＋…＋C(n,r)a^(n-r)b^r＋…＋C(n,n)b^n (n∈N*)

Lagrange乘子法(条件极值问题):
{max|min(f(x,y,z)),g(x,y,z)=0,h(x,y,z)=0}  <=>  {max|min(L(x,y,z,λ,μ)=f(x,y,z)+λg(x,y,z)+μh(x,y,z))}

点线距离(ax+by+c=0) & 点面距离(ax+by+cz+d=0):
d=|ax+by+c|/√(a^2+b^2)
d=|ax+by+cz+d|/√(a^2+b^2+c^2)

万能公式:
设tan(A/2)=t,则
sinA=2t/(1+t^2);  cosA=(1-t^2)/(1+t^2);  tanA=2t/(1-t^2)

欧拉公式:
e^(ix) = (1-x^2/2!+x^4/4!-...)+i(x-x^3/3!+x^5/5!-...) = cosx+i*sinx
e^(-ix)=cosx-i*sinx
=> sinx=[e^(ix)-e^(-ix)]/2i;  cosx=[e^(ix)+e^(-ix)]/2
e^i(A+B) = e^iA * e ^iB = (cosA+ isinA)(cosB+ isinB) = cosAcosB-sinAsinB+ i(sinAcosB+sinBcosA) = cos(A+B)+isin(A+B)
=> cos(A+B)=cosAcosB-sinAsinB;  sin(A+B)=sinAcosB+cosAsinB
```

---
##### 微分中值定理(Rolle定理的推广)
```python
若函数f(x)在闭区间[a,b]上连续在开区间(a,b)内可导,则存在ξ∈(a,b)使f(b)-f(a)=f'(ξ)*(b-a)
应用: 
函数单调性与导数的关系
x/(1+x)<ln(1+x)<x不等式的证明
3ax^2+2bx-a-b=0在(0,1)上必有实根,令F(x)=ax^3+bx^2-ax-bx
```

---
##### 定积分应用
```python
直角系区域弧长∫(a,b)√(1+y'^2)dx和三维直角坐标系区域弧长∫(a,b)√[x'(t)^2+y'(t)^2+z'(t)^2]dt
直角系区域面积∫(a,b)[f(x)-d(x)]dx和极坐标系区域面积∫(α,β)[(r^2)/2]dθ
绕坐标轴旋转的旋转体表面积2π∫(a,b)f(x)(1+f'(x)^2)^.5dx,注意这里不要把(1+f'(x)^2)^.5搞丢了,一般曲面z=f(x,y)表面积S=∫∫(D)√[1+(∂z/∂x)^2+(∂z/∂y)^2]dxdy
绕坐标轴旋转的旋转体体积(圆盘法or壳层法or一般二重积分方法),二重积分可以求非旋转体体积
求曲线的曲率△α/△L=|f''(x)/[1+f'(x)^2]^1.5|=|[y''(t)x'(t)-x''(t)y'(t)]/[y'(t)^2+x'(t)^2]^1.5|; 注意参数形式只需加个x=t即可
```