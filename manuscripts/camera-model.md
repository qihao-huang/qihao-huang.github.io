# Camera Model

[TOC]

## Camera Frame to Image Frame

Point $P$ coordinate in camera frame: $P_c = [ X_c, Y_c, Z_c]$, corresponding point $p$ coordinate in image coordinate: $p=[x, y]^T$. 

Given:
$$
\frac{Z}{f}=\frac{Y}{y}=\frac{X}{x}
$$
then: 
$$
x=f\frac{X_c}{Z_c}=\frac{\hat{x}}{\hat{z}} \\
y=f\frac{Y_c}{Z_c}=\frac{\hat{y}}{\hat{z}} \\
z=f, \hat{z} \neq 0
$$
Formulation:
$$
\begin{equation}
{
    \left [ 
        \begin{array}{c}
            x \\
            y 
        \end{array} 
    \right ]
} \Leftrightarrow
{
    \left [ 
        \begin{array}{c}
            \hat{x} \\
            \hat{y} \\
            \hat{z}
        \end{array} 
    \right ]
} = 
{
    \left[ 
        \begin{array}{cccc}
            f & 0 & 0 & 0 \\
            0 & f & 0 & 0 \\
            0 & 0 & 1 & 0
        \end{array}
    \right ]
}
{
    \left[ 
        \begin{array}{c}
            X_c \\
            Y_c \\
            Z_c \\
            1
        \end{array}
    \right ]
}
\end{equation}
$$
​	

## Intrinsic

### Image Frame to Pixel Frame: scaling and translation

$$
\left\{
\begin{aligned}
u & = \alpha\cdot x +c_x = \alpha \cdot f\frac{X_c}{Z} + c_x = f_x \cdot \frac{X_c}{Z} + c_x, 
  \  \ f_x = \alpha \cdot f \\
v & =  \alpha\cdot y +c_y = \alpha \cdot f\frac{Y_c}{Z} + c_y = f_y \cdot \frac{Y_c}{Z} + c_y, 
  \  \ f_y = \alpha \cdot f \\
\end{aligned}
\right.
$$

### matrix form: $p=KP$

$$
\begin{equation}
{
    \left [ 
        \begin{array}{c}
            u \\
            v \\
            1
        \end{array} 
    \right ]
} = \frac{1}{Z}
{
    \left[ 
        \begin{array}{ccc}
            f_x & 0 & c_x \\
            0 & f_y & c_y \\
            0 & 0 & 1 
        \end{array}
    \right ]
}
{
    \left[ 
        \begin{array}{c}
            X_c \\
            Y_c \\
            Z_c 
        \end{array}
    \right ]
}
\end{equation}
$$

$$
\begin{equation}
{
    \left [ 
        \begin{array}{c}
            u \\
            v \\
            1
        \end{array} 
    \right ]
} \Leftrightarrow Z
{
    \left [ 
        \begin{array}{c}
            u \\
            v \\
            1
        \end{array} 
    \right ]
} = 
{
    \left[ 
        \begin{array}{ccc}
            f_x & 0 & c_x \\
            0 & f_y & c_y \\
            0 & 0 & 1 
        \end{array}
    \right ]
} 
{
    \left[ 
        \begin{array}{c}
            X_c \\
            Y_c \\
            Z_c 
        \end{array}
    \right ]
}
\end{equation}
$$

$$
\begin{equation}
Intrinsic\ matrix\ K = {
    \left[ 
        \begin{array}{ccc}
            f_x & 0 & c_x \\
            0 & f_y & c_y \\
            0 & 0 & 1 
        \end{array}
    \right ]
} 
\end{equation}
$$

## Extrinsic

### World Frame to Camera Frame

Point coordinate in word frame: $P_w$, in camera frame: $P_c$.
$$
\begin{equation}
P_c = RP_w + t, \ 
{
    \left [ 
        \begin{array}{c}
            X_c \\
            Y_c \\
            Z_c
        \end{array} 
    \right ]
}  = 
{
    \left[ 
        \begin{array}{ccc}
            R_{11} & R_{12} & R_{13} \\
            R_{21} & R_{22} & R_{23} \\
            R_{31} & R_{32} & R_{33} 
        \end{array}
    \right ]
} 
{
    \left[ 
        \begin{array}{c}
            X_w \\
            Y_w \\
            Z_w 
        \end{array}
    \right ]
} + 
{
    \left[ 
        \begin{array}{c}
            t_1 \\
            t_2 \\
            t_3 
        \end{array}
    \right ]
}
\end{equation}
$$

$$
\begin{equation}
{
    \left [ 
        \begin{array}{c}
            X_c \\
            Y_c \\
            Z_c \\ 
            1
        \end{array} 
    \right ]
}  = 
{
    \left[ 
        \begin{array}{cccc}
            R_{11} & R_{12} & R_{13} & t_1 \\
            R_{21} & R_{22} & R_{23} & t_2 \\
            R_{31} & R_{32} & R_{33} & t_3 \\
            0      & 0      & 0      & 1
        \end{array}
    \right ]
} 
{
    \left[ 
        \begin{array}{c}
            X_w \\
            Y_w \\
            Z_w \\
            1
        \end{array}
    \right ]
} = 
{
    \left[ 
        \begin{array}{cc}
            R & t \\
            0^T & 1 
        \end{array}
    \right ]
} 
{
    \left[ 
        \begin{array}{c}
            X_w \\
            Y_w \\
            Z_w \\
            1
        \end{array}
    \right ]
}
\end{equation}
$$

### Camera model in matrix
$$
\begin{equation}
p = K[R|t]P, \ 
{
    \left [ 
        \begin{array}{c}
            u \\
            v \\
            1
        \end{array} 
    \right ]
}  = 
{
    \left[ 
        \begin{array}{cccc}
            f_x & 0   & c_x & 0 \\
            0   & f_y & c_y & 0 \\
            0   & 0   &  1  & 0 
        \end{array}
    \right ]
}
{
    \left[ 
        \begin{array}{cc}
            R & t \\
            0^T & 1 
        \end{array}
    \right ]
} 
{
    \left[ 
        \begin{array}{c}
            X_w \\
            Y_w \\
            Z_w \\
            1
        \end{array}
    \right ]
}
\end{equation}
$$
