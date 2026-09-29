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

# 数据
delta=0.01
x = np.arange(-2.0, 2.0, delta)
y = np.arange(-2.0, 2.0, delta*2)
X, Y = np.meshgrid(x, y)
Z = -X*np.exp(-X**2 - Y**2)*10

# 2. 画布
fig=plt.figure(figsize=(5,5))
ax=plt.gca()
CS = ax.contour(X,Y,Z, levels=15, colors='k', linewidths=1)
# 自定义线型
for line, lvl in zip(CS.collections, CS.levels):
    if(lvl<0):
        line.set_linestyle('--')
        line.set_color('b')
    elif(lvl==0):
        line.set_linestyle('dotted')
    else:
        line.set_linestyle('-')
        line.set_color('r')

ax.clabel(CS, fmt='%.1f', inline=True, fontsize=10)
ax.set_xlabel('x')
plt.savefig('sciviz-auto-Lecture2 9 training_preview.png', bbox_inches='tight', dpi=110)
plt.close('all')

fig=plt.figure(figsize=(5,5))
ax=plt.gca()

# 读取数据
TT=np.loadtxt('data/contour/TT.dat')
PP=np.loadtxt('data/contour/PP.dat')
RHO=np.loadtxt('data/contour/RHO.dat')
# plot contour
nlevel=20
levels=np.linspace(np.min(RHO), np.max(RHO),nlevel )
# levels=[200, 400]
# print(levels)
CS=ax.contour(TT,PP/1e5,RHO,levels=levels, cmap='jet')
ax.clabel(CS, fontsize=10, fmt='%.0f')
plt.savefig('sciviz-auto-Lecture2 9 training_preview_2.png', bbox_inches='tight', dpi=110)
plt.close('all')

# read nc
data=Dataset('data/contour/osu91a1f_16.nc')
# print(data)
lon=data.variables['lon'][:]
lat=data.variables['lat'][:]
geoid=data.variables['z'][:]
X,Y = np.meshgrid(lon,lat)
# plot
fig=plt.figure(figsize=(6,4))
ax=plt.gca()
CS=ax.contour(X,Y,geoid,colors='k', linewidths=1, levels=16)
ax.clabel(CS, fmt='%.0f', fontsize=7)
plt.savefig('sciviz-auto-Lecture2 9 training_preview_3.png', bbox_inches='tight', dpi=110)
plt.close('all')