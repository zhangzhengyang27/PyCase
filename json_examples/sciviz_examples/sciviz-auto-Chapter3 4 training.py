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

plt.figure()
ax=plt.gca()

# venn2(subsets=(3,3,4),ax=ax)

venn3([set(['a','b','f','g','3']), set(['b','q','m','n','p','3']),set(['0','5'])],ax=ax)

plt.savefig('sciviz-auto-Chapter3 4 training_preview.png', bbox_inches='tight', dpi=110)
plt.close('all')

plt.figure()
ax=plt.gca()

v=venn2(subsets=(3,3,4),ax=ax)
vc=venn2_circles(subsets=(3,3,4),ax=ax)
print(vc[0])
print(v.id2idx)
vc[0].set_edgecolor('b')
# print(v.subset_labels)
v.subset_labels[1].set_text('ddd')

# v.get_patch_by_id('10').set_color('k')

# v.get_patch_by_id('10').set_alpha(1)
# venn3([set(['a','b','f','g','3']), set(['b','q','m','n','p','3']),set(['0','5'])],ax=ax)

plt.savefig('sciviz-auto-Chapter3 4 training_preview_2.png', bbox_inches='tight', dpi=110)
plt.close('all')