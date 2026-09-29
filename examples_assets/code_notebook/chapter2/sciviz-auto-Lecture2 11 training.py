import pandas as pd
import numpy as np
from matplotlib.ticker import MultipleLocator
import matplotlib as mpl
mpl.rcParams["font.family"] = 'Arial'  #默认字体类型
mpl.rcParams["mathtext.fontset"] = 'cm' #数学文字字体
mpl.rcParams["contour.negative_linestyle"] = 'dashed'  #默认字体类型
import matplotlib.pyplot as plt
# 中文字体配置（找不到中文字体时中文显示为方块但不影响运行）
try:
    from matplotlib import font_manager as _fm
    _zh = [f.name for f in _fm.fontManager.ttflist if any(
        k in f.name for k in ("PingFang", "Heiti", "Songti", "Hiragino", "YaHei", "SimHei", "Arial Unicode"))]
    if _zh:
        plt.rcParams["font.sans-serif"] = [_zh[0]]
    plt.rcParams["axes.unicode_minus"] = False
except Exception:
    pass

import os
# 新增
from netCDF4 import Dataset
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

def genVelocity(m,x,y):
    U=m*(x - 1/3.1*x**3 - y)
    V=x/m
    return U,V

l=8
n=100
mu=0.5
x=np.linspace(-l,l,n)
y=np.linspace(-l,l,n)
X,Y=np.meshgrid(x,y)
U,V=genVelocity(mu,X,Y)
vel=(U**2+V**2)**0.5
fig=plt.figure(figsize=(6,6))
ax=plt.gca()
ax.streamplot(X,Y,U,V,density=(1,2),color=vel,cmap='jet',arrowsize=2,arrowstyle='->',linewidth=4*vel/np.max(vel))

plt.savefig('sciviz-auto-Lecture2 11 training_preview.png', bbox_inches='tight', dpi=110)
plt.close('all')

fig=plt.figure(figsize=(6,6))
ax=plt.gca()
interval=4
skip=(slice(None, None, interval),slice(None, None, interval))
ax.quiver(X[skip],Y[skip],U[skip],V[skip],vel[skip],cmap='jet',units='xy',scale=60,pivot='mid')
ax.scatter(X[skip],Y[skip],s=4,color='r')
plt.savefig('sciviz-auto-Lecture2 11 training_preview_2.png', bbox_inches='tight', dpi=110)
plt.close('all')

# 1. 读取nc
data=Dataset('data/streamplot/globalWind.nc')
# print(data.variables) #查看变量
lon=data.variables['longitude'][:]
lat=data.variables['latitude'][:]
u=data.variables['u100'][:]
v=data.variables['v100'][:]
# print(U.shape,V.shape,lon.shape,lat.shape)
U=u.reshape((u.shape[1], u.shape[2]))
V=v.reshape((v.shape[1], v.shape[2]))
# print(U.shape,V.shape,lon.shape,lat.shape)
interval=10
skip=(slice(None, None, interval),slice(None, None, interval))
# 构建网格
X, Y = np.meshgrid(lon, lat)
vel=(U**2+V**2)**0.5
fig=plt.figure(figsize=(8,5))
ax=plt.gca()
ax.streamplot(X[skip],Y[skip],U[skip],V[skip],density=3,color=vel[skip],cmap='magma',linewidth=1)

plt.savefig('sciviz-auto-Lecture2 11 training_preview_3.png', bbox_inches='tight', dpi=110)
plt.close('all')