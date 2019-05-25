##### 凸性判断
```python
设函数f(x)在[a,b]上可导,则f(x)是[a,b]上的下凸函数的充要条件是f'(x)在[a,b]上单调增
下凸性质:
若a,b大于0且a+b=1,则af(x1)+bf(x2)>f(ax1+bx2)
```

---
##### Lagrange乘子法(条件极值问题)
```python
{max|min(f(x,y,z)),g(x,y,z)=0,h(x,y,z)=0}  <=>  {max|min(L(x,y,z,λ,μ)=f(x,y,z)+λg(x,y,z)+μh(x,y,z))}
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


