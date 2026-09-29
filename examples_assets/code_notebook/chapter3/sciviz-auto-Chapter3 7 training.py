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
from netCDF4 import Dataset
# 新增

import seaborn as sns

# Fixing random state for reproducibility
np.random.seed(19680801)

# fake up some data
spread = np.random.rand(50) * 100
center = np.ones(25) * 60
flier_high = np.random.rand(10) * 100 + 60
flier_low = np.random.rand(10) * -40
data = np.concatenate((spread, center, flier_high, flier_low))

# plt.figure()
# ax=plt.gca()
# boxes=ax.boxplot(data,showfliers=False, patch_artist=True)
# print(boxes['boxes'][0].set_facecolor('r'))
# boxes['medians'][0].set_color('b')
# boxes['medians'][0].set_lw(4)
# plt.savefig('sciviz-auto-Chapter3 7 training_preview.png', bbox_inches='tight', dpi=110)
plt.close('all')

plt.figure()
ax=plt.gca()
violins=ax.violinplot(data,[0.5],widths=0.3)
ax.set_xlim(0,2)
violins['bodies'][0].set_facecolor('g')
violins['bodies'][0].set_alpha(0.5)
violins['cbars'].set_color('r')
ax.plot(0.5,data.mean(),'o',mfc='w')

plt.savefig('sciviz-auto-Chapter3 7 training_preview_2.png', bbox_inches='tight', dpi=110)
plt.close('all')

alldata=pd.read_csv('Data/box_violin/data.csv')
x=alldata['species']
y=alldata['sepal_length'].values
groups=np.unique(x)
print(groups)
value_group=[]
for group in groups:
    ind=(x==group)
    value_group.append(y[ind])

plt.figure()
ax=plt.gca()
boxes=ax.boxplot(value_group,showfliers=False, patch_artist=True)
for box, color in zip(boxes['boxes'], plt.get_cmap('Set1').colors):
    box.set_facecolor(color)
ax.set_xticklabels(groups)
plt.savefig('sciviz-auto-Chapter3 7 training_preview_3.png', bbox_inches='tight', dpi=110)
plt.close('all')

for media in boxes['medians']:
    print(media.get_ydata()[0])

plt.figure()
ax=plt.gca()
violins=ax.violinplot(value_group)
for bd, color in zip(violins['bodies'], plt.get_cmap('Set1').colors):
    bd.set_facecolor(color)
    bd.set_alpha(1)
ax.set_xticklabels(groups)
plt.savefig('sciviz-auto-Chapter3 7 training_preview_4.png', bbox_inches='tight', dpi=110)
plt.close('all')

# alldata

plt.figure()
ax=plt.gca()
sns.violinplot(data=alldata,x='species',y='sepal_length',ax=ax)

plt.savefig('sciviz-auto-Chapter3 7 training_preview_5.png', bbox_inches='tight', dpi=110)
plt.close('all')

plt.figure()
ax=plt.gca()
sns.boxplot(data=alldata,x='species',y='sepal_length',ax=ax)

plt.savefig('sciviz-auto-Chapter3 7 training_preview_6.png', bbox_inches='tight', dpi=110)
plt.close('all')