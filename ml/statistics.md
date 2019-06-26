##### 样本数字特征(统计量)
![Image](https://github.com/forthcoming/essay/blob/master/ml/source/样本数字特征.jpg)          
```python
E(S^2)=[1/(n-1)](nDX-nDXbar+nμ^2-nμ^2)=[n/(n-1)](DX-DX/n)=DX
注意：
正是由于Xbar并不是μ,才会使分母除以n-1,即无偏差估计
这里可以把样本集看作是随机变量分布的一个模拟
在概率论中期望是一阶原点矩,方差是二阶中心矩,但在统计学中却不一样,要区分
概率是频率随样本趋于无穷的极限,期望是平均数随样本趋于无穷的极限
统计量的分布称为抽样分布
```

---
##### 卡方分布
![Image](https://github.com/forthcoming/essay/blob/master/ml/source/卡方分布.png)          
```python
设X1,X2,...Xn是来自总体N(0,1)的样本,则称统计量χ^2=X1^2+X2^2+...+Xn^2服从自由度为n的χ2分布
概率密度f(x)=x^(.5n-1)e^(-.5x)/[2^(.5n)Γ(.5n)]  ,x>0
证明: 
由Xi~N(0,1)可知Xi^2~Γ(1/2,2)
再由X1,X2,...Xn独立性知X1^2,X2^2,...,Xn^2相互独立
由Γ分布可加性知χ2～Γ(n/2,2)

E(χ2)=n   D(χ2)=2n
证明:
E(Xi^2)=D(Xi)=1
D(Xi^2)=E(Xi^4)-E(Xi^2)^2=3-1=2   # 注意E(Xi^4)直接根据期望定义可得到4/√π*Γ(2.5)=3
```

---
##### t分布
![Image](https://github.com/forthcoming/essay/blob/master/ml/source/t分布.jpg)          

---
##### F分布
![Image](https://github.com/forthcoming/essay/blob/master/ml/source/F分布.jpg)          
