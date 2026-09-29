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

np.random.seed(19680801)

fig = plt.figure(figsize=(8,8))
ax = fig.add_subplot(111, projection='3d')

colors = ['r', 'g', 'b', 'y']
yticks = [3, 2, 1, 0]
for c, k in zip(colors, yticks):
    xs = np.arange(20)
    ys = np.random.rand(20)
    cs = [c] * len(xs)
    cs[0] = 'c'
    ax.bar(xs, ys, zs=k, zdir='y', color=cs, alpha=0.8)

ax.set_xlim(-2, 20)
ax.set_ylim(0,4)
ax.set_zlim(0,1)
ax.set_box_aspect((4,8,3))
ax.xaxis.set_major_locator(MultipleLocator(5))

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

ax.set_yticks(yticks)
ax.view_init(elev=30, azim=-30)
# 重新自定义坐标轴属性
niceAxis(ax,fill_pane=False,label3D=True,fs_label=1,length_major=[0.1,0.5,0.4],length_minor=0.05, scaled=False)

# savefig
fname_fig=str('Lecture4_4_basic1.pdf')
plt.savefig(fname_fig)
plt.savefig('sciviz-3d-bars_preview.png', bbox_inches='tight', dpi=110)
plt.close('all')

np.random.seed(19680801)

fig = plt.figure(figsize=(8,8))
ax = fig.add_subplot(111, projection='3d')

colors = ['r', 'g', 'b', 'y','m', 'c']
yticks = [20, 15, 10, 5, 0]
for c, k in zip(colors, yticks):
    xs = np.arange(20)
    ys = np.random.rand(20)
    cs = [c] * len(xs)
    cs[0] = 'c'
    ax.bar3d(xs,k, 0, 0.6, 0.6, ys, shade=True,alpha=0.8)

ax.set_xlim(-2, 22)
ax.set_ylim(-2,22)
ax.set_zlim(0,1)
ax.set_box_aspect((4,8,3))
ax.xaxis.set_major_locator(MultipleLocator(5))

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

ax.set_yticks(yticks)
ax.view_init(elev=30, azim=-30)
# 重新自定义坐标轴属性
niceAxis(ax,fill_pane=False,label3D=True,fs_label=1,length_major=[0.5,0.5,0.4],length_minor=0.05, scaled=False)

# savefig
fname_fig=str('Lecture4_4_basic2.pdf')
plt.savefig(fname_fig)
plt.savefig('sciviz-3d-bars_preview_2.png', bbox_inches='tight', dpi=110)
plt.close('all')