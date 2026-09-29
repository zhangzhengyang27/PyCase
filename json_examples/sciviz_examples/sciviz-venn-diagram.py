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
from matplotlib_venn import venn2,venn2_circles,venn3, venn3_circles

# 第一种方式: 给定三个数字表示分别表示A， AB， B区域的大小
venn2(subsets = (3, 3, 1.5), set_labels = ('A', 'B'))
fname_fig=str('Lecture3_4_basic1.pdf')
plt.tight_layout(pad=0)
plt.savefig(fname_fig)
plt.savefig('sciviz-venn-diagram_preview.png', bbox_inches='tight', dpi=110)
plt.close('all')

# 第二种方式：给定两个集合的元素，自动根据相交情况绘制韦恩图
fig=plt.figure()
ax=plt.gca()
venn2([set(['A', 'B', 'C', 'D']), set(['D', 'E', 'A'])],ax=ax)
fname_fig=str('Lecture3_4_basic2.pdf')
plt.tight_layout(pad=0)
plt.savefig(fname_fig)
plt.savefig('sciviz-venn-diagram_preview_2.png', bbox_inches='tight', dpi=110)
plt.close('all')


v = venn3(subsets=(1, 1, 1, 1, 1, 1, 1), set_labels = ('A', 'B', 'C'))
# 1. 获取区域编号
print(v.id2idx)

# 2. 获取区域label
for i in range(0,len(v.subset_labels)):
    subset_label=v.subset_labels[i]
    subset_label.set_text(i)

#  3. 根据id获取区域的patch，并设置其属性
v.get_patch_by_id('A').set_alpha(1)
v.get_patch_by_id('A').set_color('red')
v.get_label_by_id('100').set_text('Unknown')

for ID in v.id2idx.keys():
    v.get_label_by_id(ID).set_text(ID)

# 4. 绘制边框
c = venn3_circles(subsets=(1, 1, 1, 1, 1, 1, 1), linestyle='solid')
c[0].set_lw(1.0)
c[0].set_ls('dotted')

plt.tight_layout(pad=0.)
fname_fig=str('Lecture3_4_example1.pdf')
plt.savefig(fname_fig)
# Show it
plt.savefig('sciviz-venn-diagram_preview_3.png', bbox_inches='tight', dpi=110)
plt.close('all')

fig=plt.figure(facecolor='k')
ax=plt.gca()

v=venn2(subsets = (3, 3, 1.5), set_labels = ('A', 'B'),set_colors=('r','orange'),alpha=1)
for i in range(0,len(v.subset_labels)):
    subset_label=v.subset_labels[i]
    subset_label.set_text('')
ax.text(0.5,-0.07,'mastercard',color='w',fontsize=50,va='bottom',ha='center',transform=ax.transAxes)
fname_fig=str('Lecture3_4_example2.pdf')
plt.tight_layout(pad=0)
plt.savefig(fname_fig,facecolor='k')
plt.savefig('sciviz-venn-diagram_preview_4.png', bbox_inches='tight', dpi=110)
plt.close('all')