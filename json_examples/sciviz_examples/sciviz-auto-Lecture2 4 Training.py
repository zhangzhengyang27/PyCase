import pandas as pd
import numpy as np
from matplotlib.ticker import MultipleLocator
import matplotlib as mpl
mpl.rcParams["font.family"] = 'Arial'  #默认字体类型
mpl.rcParams["mathtext.fontset"] = 'cm' #数学文字字体
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


def autolabel(rects):
    for rect in rects:
        height=rect.get_height()
        x=rect.get_x()+rect.get_width()/2
        ax.text(x, height*1.01, str(height), ha='center',va='bottom')
labels=['G1','G2','G3','G4','G5']
men_means=[20, 35, 30, 35, 27]
men_std=[3, 3, 4, 1, 2]
width=0.35

fig=plt.figure()
ax=plt.gca()

bar=ax.bar(labels, men_means, width=width, color='lightblue', ec='k', lw=0.6)
autolabel(bar)

ax.set_ylim(0, 40)

ax.set_ylabel('Scores')
ax.set_title('Score by group and gender')
plt.savefig('sciviz-auto-Lecture2 4 Training_preview.png', bbox_inches='tight', dpi=110)
plt.close('all')

fig=plt.figure()
ax=plt.gca()

error_kw={'capsize': 5, 'capthick': 2, 'ecolor': 'r'}
bar=ax.bar(labels, men_means, width=width, color='lightblue', ec='k', lw=0.6, yerr=men_std, error_kw=error_kw)

ax.set_ylim(0, 40)

ax.set_ylabel('Scores')
ax.set_title('Score by group and gender')
plt.savefig('sciviz-auto-Lecture2 4 Training_preview_2.png', bbox_inches='tight', dpi=110)
plt.close('all')

def autolabelh(rects):
    for rect in rects:
        x=rect.get_width()
        y=rect.get_y()+rect.get_height()/2
        ax.text(x*1.01, y, str(x), ha='left',va='center')
        
fig=plt.figure()
ax=plt.gca()

bar=ax.barh(labels, men_means, height=width*1.5, color='lightblue', ec='k', lw=0.6)
autolabelh(bar)

ax.set_xlim(0, 40)

ax.set_ylabel('Scores')
ax.set_title('Score by group and gender')
plt.savefig('sciviz-auto-Lecture2 4 Training_preview_3.png', bbox_inches='tight', dpi=110)
plt.close('all')

fig=plt.figure()
ax=plt.gca()

bars=ax.bar(labels, men_means, width=width, color='None', ec='k', lw=0.6)
autolabel(bars)
patterns=('----','+++','xxxx','ooo','*')
for bar, pattern in zip(bars, patterns):
    bar.set_hatch(pattern)
mpl.rcParams['hatch.linewidth']=0.3
ax.set_ylim(0, 40)
ax.set_ylabel('Scores')
ax.set_title('Score by group and gender')
plt.savefig('sciviz-auto-Lecture2 4 Training_preview_4.png', bbox_inches='tight', dpi=110)
plt.close('all')