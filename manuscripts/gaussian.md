# 高斯分布的性质

NOTE: 摘录于 《视觉 SLAM 十四讲 》，也可以参考 《应用多元统计分析/高惠璇》第二章。

## 高斯分布



如果一个随机变量 $x$ 服从高斯分布 $N(\mu, \sigma)$ ，那么它的概率密度函数为：
$$
p(x) = \frac{1}{\sqrt{2\pi}\sigma}exp	\left( -\frac{1}{2}\frac{(x-\mu)^2}{\sigma^2}\right)
$$
其高维形式为：
$$
p(x) = \frac{1}{\sqrt{(2\pi)^N}det(\Sigma)}exp	\left( -\frac{1}{2}(x-\mu)^T{\Sigma}^{-1}(x-\mu)\right)
$$


## 运算

### 线性运算

设两个独立的高斯分布：
$$
x \backsim N(\mu_x, \Sigma_{xx}), y \backsim N(\mu_y, \Sigma_{yy})
$$
那么，它们的和仍是高斯分布
$$
x + y \backsim N(\mu_x+\mu_y, \Sigma_{xx}+\Sigma_{yy}）
$$
如果以常数 $a$ 乘以 $x$，那么 $ax$ 满足：
$$
ax \backsim N(a\mu_x, a^2\Sigma_{xx})
$$
如果取 $y=Ax$，那么 $y$ 满足：
$$
y \backsim N(A\mu_x, A\Sigma_{xx}A^T)
$$

## 乘积

设两个高斯分布的乘积满足 $p(xy)=N(\mu, \Sigma)$，那么：
$$
\Sigma^{-1} = \Sigma_{xx}^{-1} + \Sigma_{yy}^{-1} \\
\Sigma^{-1} \mu = \Sigma_{xx}^{-1}\mu_x + \Sigma_{yy}^{-1}\mu_y
$$
该公式可以推广到任意多个高斯分布之乘积

## 复合运算

同样考虑 $x$ 和 y, 若其不独立，则其复合分布为：
$$
p(x,y) = N \left(  \left[
 \begin{matrix}
   \mu_x \\
   \mu_y \\
  \end{matrix}
  \right], 
   \left[
 \begin{matrix}
   \Sigma_{xx} & \Sigma_{xy}\\
   \Sigma_{yx} & \Sigma_{yy}\\
  \end{matrix}
  \right]\right)
$$
由条件分布展开式 $p(x,y) = p(x|y)p(y)$ 可以推出，条件概率 $p(x|y)$ 满足：
$$
p(x|y) = N (\mu_x+\Sigma_{xy}\Sigma_{yy}^{-1}(y-\mu_y), \Sigma_{xx}-\Sigma_{xy}\Sigma_{yy}^{-1}\Sigma_{yx})
$$

## 例子

卡尔曼滤波器相关，考虑随机变量 $x \backsim N(\mu_x, \Sigma_{xx})$，另一变量 $y$ 满足：
$$
y = Ax + b + w
$$


其中 $A,b$ 为线性变量的系数矩阵和偏移量，$w$ 为噪声项，为零均值的高斯分布：$w \backsim N(0, R)$，那么 $y$ 的分布：
$$
p(y) = N(A\mu_x+b, R+A\Sigma_{xx}A^T)
$$


