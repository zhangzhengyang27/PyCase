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
from matplotlib.colors import LightSource
from nice import niceAxis,text3d
from matplotlib.collections import PolyCollection
from matplotlib import cbook
from matplotlib import cm

fig=plt.figure(figsize=(8,8))

ax=fig.gca(projection='3d')
colors=['r','g','b','y']
yticks=[3,2,1,0]
for c, k in zip(colors, yticks):
    xs=np.arange(20)
    ys=np.random.rand(20)
    cs=[c]*len(xs)
    cs[1]='c'
    ax.bar(xs, ys, zs=k, color=cs, alpha=0.8, zdir='y')
ax.set_box_aspect((4,8,3))
plt.savefig('sciviz-auto-Chapter4 4 training_preview.png', bbox_inches='tight', dpi=110)
plt.close('all')

fig=plt.figure(figsize=(8,8))

ax=fig.gca(projection='3d')
colors=['r','g','b','y', 'm']
yticks=[20, 15, 10, 5, 0]
for c, k in zip(colors, yticks):
    xs=np.arange(20)
    ys=np.random.rand(20)
    cs=[c]*len(xs)
    cs[1]='c'
    ax.bar3d(xs, k, 0, 0.6, 0.6, ys, shade=True)
ax.set_box_aspect((4,8,3))
ax.set_xlim(-2, 22)
ax.set_ylim(-2, 22)
ax.set_zlim(0,1)
plt.savefig('sciviz-auto-Chapter4 4 training_preview_2.png', bbox_inches='tight', dpi=110)
plt.close('all')