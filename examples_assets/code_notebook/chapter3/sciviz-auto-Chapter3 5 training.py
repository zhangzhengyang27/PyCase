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

import io
import os
from netCDF4 import Dataset
import seaborn as sns
# 新增
from scipy.cluster.hierarchy import dendrogram, linkage

X = [[i] for i in [2, 8, 0, 4, 1, 9, 9, 0, 3]]
Z = linkage(X, method='ward',  metric='euclidean')

dn = dendrogram(Z)

# 数据随包内联（原课件读 Data/mtcars/mtcars.csv；工作区不携带 Data/ 目录，内联后随处可跑）
MTCARS_CSV = """model,mpg,cyl,disp,hp,drat,wt,qsec,vs,am,gear,carb
Mazda RX4,21,6,160,110,3.9,2.62,16.46,0,1,4,4
Mazda RX4 Wag,21,6,160,110,3.9,2.875,17.02,0,1,4,4
Datsun 710,22.8,4,108,93,3.85,2.32,18.61,1,1,4,1
Hornet 4 Drive,21.4,6,258,110,3.08,3.215,19.44,1,0,3,1
Hornet Sportabout,18.7,8,360,175,3.15,3.44,17.02,0,0,3,2
Valiant,18.1,6,225,105,2.76,3.46,20.22,1,0,3,1
Duster 360,14.3,8,360,245,3.21,3.57,15.84,0,0,3,4
Merc 240D,24.4,4,146.7,62,3.69,3.19,20,1,0,4,2
Merc 230,22.8,4,140.8,95,3.92,3.15,22.9,1,0,4,2
Merc 280,19.2,6,167.6,123,3.92,3.44,18.3,1,0,4,4
Merc 280C,17.8,6,167.6,123,3.92,3.44,18.9,1,0,4,4
Merc 450SE,16.4,8,275.8,180,3.07,4.07,17.4,0,0,3,3
Merc 450SL,17.3,8,275.8,180,3.07,3.73,17.6,0,0,3,3
Merc 450SLC,15.2,8,275.8,180,3.07,3.78,18,0,0,3,3
Cadillac Fleetwood,10.4,8,472,205,2.93,5.25,17.98,0,0,3,4
Lincoln Continental,10.4,8,460,215,3,5.424,17.82,0,0,3,4
Chrysler Imperial,14.7,8,440,230,3.23,5.345,17.42,0,0,3,4
Fiat 128,32.4,4,78.7,66,4.08,2.2,19.47,1,1,4,1
Honda Civic,30.4,4,75.7,52,4.93,1.615,18.52,1,1,4,2
Toyota Corolla,33.9,4,71.1,65,4.22,1.835,19.9,1,1,4,1
Toyota Corona,21.5,4,120.1,97,3.7,2.465,20.01,1,0,3,1
Dodge Challenger,15.5,8,318,150,2.76,3.52,16.87,0,0,3,2
AMC Javelin,15.2,8,304,150,3.15,3.435,17.3,0,0,3,2
Camaro Z28,13.3,8,350,245,3.73,3.84,15.41,0,0,3,4
Pontiac Firebird,19.2,8,400,175,3.08,3.845,17.05,0,0,3,2
Fiat X1-9,27.3,4,79,66,4.08,1.935,18.9,1,1,4,1
Porsche 914-2,26,4,120.3,91,4.43,2.14,16.7,0,1,5,2
Lotus Europa,30.4,4,95.1,113,3.77,1.513,16.9,1,1,5,2
Ford Pantera L,15.8,8,351,264,4.22,3.17,14.5,0,1,5,4
Ferrari Dino,19.7,6,145,175,3.62,2.77,15.5,0,1,5,6
Maserati Bora,15,8,301,335,3.54,3.57,14.6,0,1,5,8
Volvo 142E,21.4,4,121,109,4.11,2.78,18.6,1,1,4,2
"""
data_cars=pd.read_csv(io.StringIO(MTCARS_CSV))
df = data_cars.set_index('model')
df.index.name = None
models=df.index
Z = linkage(df.values, method='ward',  metric='euclidean')
plt.figure()
ax=plt.gca()
dn = dendrogram(Z, orientation='top', ax=ax)
leaves=np.array(dn['leaves'],dtype=int)
ax.xaxis.set_ticklabels(models[leaves],rotation=90)
# print(dn)
plt.savefig('sciviz-auto-Chapter3 5 training_preview.png', bbox_inches='tight', dpi=110)
plt.close('all')

data_cars=pd.read_csv(io.StringIO(MTCARS_CSV))
df = data_cars.set_index('model')
df.index.name = None
models=df.index

clustermap=sns.clustermap(df, z_score=1,cmap='magma')  #dendrogram_row.linkage
clusterdata=clustermap.data2d
plt.close()

models=clusterdata.index
names=clusterdata.columns
values=np.array(clusterdata.values,dtype=float)


fig,axs=plt.subplots(2,2,gridspec_kw={'width_ratios':[1,0.25], 'height_ratios':[0.2,1],
                                      'hspace':0,'wspace':0},figsize=(6,6))
ax=axs[1][0]
x = np.arange(values.shape[1] + 1)
y = np.arange(values.shape[0] + 1)
heatmap=ax.pcolor(values,cmap='magma')
ax.set_xticks(x[:-1]+0.5)
ax.set_xticklabels(names)
ax.invert_yaxis()

ax=axs[0][0]
linkage_col=clustermap.dendrogram_col.linkage
dendrogram(linkage_col, ax=ax)
ax.axis('off')

ax=axs[1][1]
linkage_row=clustermap.dendrogram_row.linkage
dendrogram(linkage_row, ax=ax, orientation='right')
ax.axis('off')

ax=axs[0][1]
w_cb=0.2
ax_cb=ax.inset_axes([0.5-w_cb/2.0, 0, w_cb, 1], transform=ax.transAxes)
cbar = plt.colorbar(heatmap, cax=ax_cb, ticks=np.arange(-3,3))
ax.axis('off')
plt.savefig('sciviz-auto-Chapter3 5 training_preview_2.png', bbox_inches='tight', dpi=110)
plt.close('all')