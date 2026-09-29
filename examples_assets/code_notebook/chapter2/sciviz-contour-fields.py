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

# 1. 准备数据
delta = 0.01
x = np.arange(-2.0, 2.0, delta)
y = np.arange(-2.0, 2.0, delta)
X, Y = np.meshgrid(x, y)
Z = -X*np.exp(-X**2 - Y**2)*10
# 2. 创建画布
fig = plt.figure(figsize=(5,5))
ax=plt.gca()
# 3. 绘制等值线
CS = ax.contour(X, Y, Z, levels=10,cmap='jet',linewidths=2)
# 4. 设置线型
for line, lvl in zip(CS.collections, CS.levels):
    if lvl < 0:
        line.set_linestyle('--')
    elif lvl == 0:
        line.set_linestyle(':')
    else:
        line.set_linestyle('-')
# 设置等值文字标注
ax.clabel(CS, inline=True, fmt='%.1f', fontsize=15)
# title
ax.set_title('$Z\ = \ -Xe^{-X^2-Y^2}$')
# xy方向一比一
ax.axis('scaled')
# savefig
plt.tight_layout()
plt.savefig('Lecture2_9_basic.pdf')
plt.savefig('sciviz-contour-fields_preview.png', bbox_inches='tight', dpi=110)
plt.close('all')

plt.figure(figsize=(5,5))
ax=plt.gca()
cmap='rainbow'
prop='RHO'
nlevel=20
TT=np.loadtxt('data/contour/TT.dat')
PP=np.loadtxt('data/contour/PP.dat')
Prop=np.loadtxt('data/contour/'+prop+'.dat')
levels=np.linspace(np.min(Prop),np.max(Prop),nlevel)
CS=ax.contour(TT,PP/1e5,Prop,cmap=cmap,levels=levels)
ax.set_xlim(0,990)
ax.set_ylim(0,990)
ax.set_xlabel('Temperature ($^{\circ}$C)')
ax.set_ylabel('Pressure (bar)')
ax.set_title('Density of water in P-T space')
# 设置等值文字标注
ax.clabel(CS, inline=True, fmt='%.0f', fontsize=10)
# savefig
plt.tight_layout()
plt.savefig('Lecture2_9_example1.pdf')
plt.savefig('sciviz-contour-fields_preview_2.png', bbox_inches='tight', dpi=110)
plt.close('all')

# 1. 读取nc
data=Dataset('data/contour/osu91a1f_16.nc')
# print(data.variables) #查看变量
lon=data.variables['lon'][:]
lat=data.variables['lat'][:]
z=data.variables['z'][:]
# 构建网格
X, Y = np.meshgrid(lon, lat)
print(lon.shape,lat.shape,z.shape,X.shape)
# 绘制等值线
fig=plt.figure(figsize=(6,4))
ax=plt.gca()
CS=ax.contour(X,Y,z,colors='k',linewidths=1,levels=16)
# CS=ax.contour(X,Y,z,linewidths=1,levels=16,cmap='rainbow')
# 设置等值文字标注
ax.clabel(CS, inline=True, fmt='%.0f', fontsize=7)
ax.set_xlabel('Longitude (degree)')
ax.set_ylabel('Latitude (degree)')
ax.set_title('Low Order Geoid')
# savefig
plt.tight_layout()
plt.savefig('Lecture2_9_example2.pdf')
plt.savefig('sciviz-contour-fields_preview_3.png', bbox_inches='tight', dpi=110)
plt.close('all')