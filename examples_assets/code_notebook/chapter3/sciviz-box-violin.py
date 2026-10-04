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
print('共有',len(data),'个数据')
fig = plt.figure()
ax=plt.gca()
whis=1.5

# 箱形图
flierprops = dict(markerfacecolor='c',markeredgecolor='None', marker='.')
box=ax.boxplot(data,notch=False,showfliers=True,
           vert=True,patch_artist=True,showmeans=True,flierprops=flierprops,
           boxprops=dict(facecolor='orange',edgecolor='b'),
           medianprops={'color':'purple','lw':2},
           meanprops={'color':'g','marker':'o'},
           whiskerprops={'color':'m'},capprops={'color':'r','lw':3},whis=whis)
# 小提琴图
x_violin=1.6
violin=ax.violinplot(data,[x_violin],showmeans=True,showextrema=True, showmedians=True,widths=0.3)
for bd in violin['bodies']:
    bd.set_facecolor(box['boxes'][0].get_facecolor())
    bd.set_alpha(0.8)
    bd.set_edgecolor(box['boxes'][0].get_edgecolor())
# 自定义属性
violin['cmeans'].set_color(box['means'][0].get_color())
violin['cmedians'].set_color(box['medians'][0].get_color())
violin['cbars'].set_color(box['whiskers'][0].get_color())
violin['cmins'].set_color(box['fliers'][0].get_markerfacecolor())
violin['cmaxes'].set_color(box['fliers'][0].get_markerfacecolor())

# ===============================供参考学习==============================================
# 标注箱形图
Q1,Median,Q3 = np.percentile(data, [25, 50, 75])
for Q, label in zip([Q1,Q3],['Q1','Q3']):
    ax.text(0.9,Q,label,va='center',ha='right',color=box['boxes'][0].get_edgecolor())
    ax.hlines(Q,xmin=1,xmax=x_violin,ls='dotted',lw=1,color=box['boxes'][0].get_edgecolor())
ax.text(0.9,Median,'Median',va='center',ha='right',color=box['medians'][0].get_color())
ax.text(1,data.mean()-5,'Mean',va='top',ha='center',color=box['means'][0].get_color())
for whisker,label in zip(box['whiskers'],['upper whisker','lower whisker']):
    ax.text(whisker.get_xdata()[0]-0.05,whisker.get_ydata().mean(),label,va='center',ha='right',color=whisker.get_color())
for cap,label in zip(box['caps'],['upper extreme','lower extreme']):
    ax.text(cap.get_xdata()[0]-0.05,cap.get_ydata()[1],label,va='center',ha='right',color=cap.get_color())
    ax.hlines(cap.get_ydata()[1],xmin=cap.get_xdata()[0],xmax=x_violin,ls='dashed',lw=1)
ax.text(box['fliers'][0].get_xdata()[0]-0.05, box['fliers'][0].get_ydata()[-1], 'outlier',ha='right',va='center',color=box['fliers'][0].get_markerfacecolor())
ax.set_xlim(0.65,1.8)
ax.xaxis.set_ticks([1,x_violin])
ax.xaxis.set_ticklabels(['Box','Violin'])
# =============================================================================
fname_fig='Lecture3_7_basic1.pdf'
plt.savefig(fname_fig)

plt.savefig('sciviz-box-violin_preview.png', bbox_inches='tight', dpi=110)
plt.close('all')

# 读取数据
# 数据随包内联（原课件读 Data/box_violin/data.csv，即经典鸢尾花数据集；工作区不携带 Data/ 目录）
IRIS_CSV = """sepal_length,sepal_width,petal_length,petal_width,species
5.1,3.5,1.4,0.2,setosa
4.9,3.0,1.4,0.2,setosa
4.7,3.2,1.3,0.2,setosa
4.6,3.1,1.5,0.2,setosa
5.0,3.6,1.4,0.2,setosa
5.4,3.9,1.7,0.4,setosa
4.6,3.4,1.4,0.3,setosa
5.0,3.4,1.5,0.2,setosa
4.4,2.9,1.4,0.2,setosa
4.9,3.1,1.5,0.1,setosa
5.4,3.7,1.5,0.2,setosa
4.8,3.4,1.6,0.2,setosa
4.8,3.0,1.4,0.1,setosa
4.3,3.0,1.1,0.1,setosa
5.8,4.0,1.2,0.2,setosa
5.7,4.4,1.5,0.4,setosa
5.4,3.9,1.3,0.4,setosa
5.1,3.5,1.4,0.3,setosa
5.7,3.8,1.7,0.3,setosa
5.1,3.8,1.5,0.3,setosa
5.4,3.4,1.7,0.2,setosa
5.1,3.7,1.5,0.4,setosa
4.6,3.6,1.0,0.2,setosa
5.1,3.3,1.7,0.5,setosa
4.8,3.4,1.9,0.2,setosa
5.0,3.0,1.6,0.2,setosa
5.0,3.4,1.6,0.4,setosa
5.2,3.5,1.5,0.2,setosa
5.2,3.4,1.4,0.2,setosa
4.7,3.2,1.6,0.2,setosa
4.8,3.1,1.6,0.2,setosa
5.4,3.4,1.5,0.4,setosa
5.2,4.1,1.5,0.1,setosa
5.5,4.2,1.4,0.2,setosa
4.9,3.1,1.5,0.2,setosa
5.0,3.2,1.2,0.2,setosa
5.5,3.5,1.3,0.2,setosa
4.9,3.6,1.4,0.1,setosa
4.4,3.0,1.3,0.2,setosa
5.1,3.4,1.5,0.2,setosa
5.0,3.5,1.3,0.3,setosa
4.5,2.3,1.3,0.3,setosa
4.4,3.2,1.3,0.2,setosa
5.0,3.5,1.6,0.6,setosa
5.1,3.8,1.9,0.4,setosa
4.8,3.0,1.4,0.3,setosa
5.1,3.8,1.6,0.2,setosa
4.6,3.2,1.4,0.2,setosa
5.3,3.7,1.5,0.2,setosa
5.0,3.3,1.4,0.2,setosa
7.0,3.2,4.7,1.4,versicolor
6.4,3.2,4.5,1.5,versicolor
6.9,3.1,4.9,1.5,versicolor
5.5,2.3,4.0,1.3,versicolor
6.5,2.8,4.6,1.5,versicolor
5.7,2.8,4.5,1.3,versicolor
6.3,3.3,4.7,1.6,versicolor
4.9,2.4,3.3,1.0,versicolor
6.6,2.9,4.6,1.3,versicolor
5.2,2.7,3.9,1.4,versicolor
5.0,2.0,3.5,1.0,versicolor
5.9,3.0,4.2,1.5,versicolor
6.0,2.2,4.0,1.0,versicolor
6.1,2.9,4.7,1.4,versicolor
5.6,2.9,3.6,1.3,versicolor
6.7,3.1,4.4,1.4,versicolor
5.6,3.0,4.5,1.5,versicolor
5.8,2.7,4.1,1.0,versicolor
6.2,2.2,4.5,1.5,versicolor
5.6,2.5,3.9,1.1,versicolor
5.9,3.2,4.8,1.8,versicolor
6.1,2.8,4.0,1.3,versicolor
6.3,2.5,4.9,1.5,versicolor
6.1,2.8,4.7,1.2,versicolor
6.4,2.9,4.3,1.3,versicolor
6.6,3.0,4.4,1.4,versicolor
6.8,2.8,4.8,1.4,versicolor
6.7,3.0,5.0,1.7,versicolor
6.0,2.9,4.5,1.5,versicolor
5.7,2.6,3.5,1.0,versicolor
5.5,2.4,3.8,1.1,versicolor
5.5,2.4,3.7,1.0,versicolor
5.8,2.7,3.9,1.2,versicolor
6.0,2.7,5.1,1.6,versicolor
5.4,3.0,4.5,1.5,versicolor
6.0,3.4,4.5,1.6,versicolor
6.7,3.1,4.7,1.5,versicolor
6.3,2.3,4.4,1.3,versicolor
5.6,3.0,4.1,1.3,versicolor
5.5,2.5,4.0,1.3,versicolor
5.5,2.6,4.4,1.2,versicolor
6.1,3.0,4.6,1.4,versicolor
5.8,2.6,4.0,1.2,versicolor
5.0,2.3,3.3,1.0,versicolor
5.6,2.7,4.2,1.3,versicolor
5.7,3.0,4.2,1.2,versicolor
5.7,2.9,4.2,1.3,versicolor
6.2,2.9,4.3,1.3,versicolor
5.1,2.5,3.0,1.1,versicolor
5.7,2.8,4.1,1.3,versicolor
6.3,3.3,6.0,2.5,virginica
5.8,2.7,5.1,1.9,virginica
7.1,3.0,5.9,2.1,virginica
6.3,2.9,5.6,1.8,virginica
6.5,3.0,5.8,2.2,virginica
7.6,3.0,6.6,2.1,virginica
4.9,2.5,4.5,1.7,virginica
7.3,2.9,6.3,1.8,virginica
6.7,2.5,5.8,1.8,virginica
7.2,3.6,6.1,2.5,virginica
6.5,3.2,5.1,2.0,virginica
6.4,2.7,5.3,1.9,virginica
6.8,3.0,5.5,2.1,virginica
5.7,2.5,5.0,2.0,virginica
5.8,2.8,5.1,2.4,virginica
6.4,3.2,5.3,2.3,virginica
6.5,3.0,5.5,1.8,virginica
7.7,3.8,6.7,2.2,virginica
7.7,2.6,6.9,2.3,virginica
6.0,2.2,5.0,1.5,virginica
6.9,3.2,5.7,2.3,virginica
5.6,2.8,4.9,2.0,virginica
7.7,2.8,6.7,2.0,virginica
6.3,2.7,4.9,1.8,virginica
6.7,3.3,5.7,2.1,virginica
7.2,3.2,6.0,1.8,virginica
6.2,2.8,4.8,1.8,virginica
6.1,3.0,4.9,1.8,virginica
6.4,2.8,5.6,2.1,virginica
7.2,3.0,5.8,1.6,virginica
7.4,2.8,6.1,1.9,virginica
7.9,3.8,6.4,2.0,virginica
6.4,2.8,5.6,2.2,virginica
6.3,2.8,5.1,1.5,virginica
6.1,2.6,5.6,1.4,virginica
7.7,3.0,6.1,2.3,virginica
6.3,3.4,5.6,2.4,virginica
6.4,3.1,5.5,1.8,virginica
6.0,3.0,4.8,1.8,virginica
6.9,3.1,5.4,2.1,virginica
6.7,3.1,5.6,2.4,virginica
6.9,3.1,5.1,2.3,virginica
5.8,2.7,5.1,1.9,virginica
6.8,3.2,5.9,2.3,virginica
6.7,3.3,5.7,2.5,virginica
6.7,3.0,5.2,2.3,virginica
6.3,2.5,5.0,1.9,virginica
6.5,3.0,5.2,2.0,virginica
6.2,3.4,5.4,2.3,virginica
5.9,3.0,5.1,1.8,virginica"""
alldata=pd.read_csv(io.StringIO(IRIS_CSV))
x=alldata['species'].values
valuename='sepal_length'
y=alldata[valuename].values
groups=np.unique(x)
value_groups=[]
for group in groups:
    ind=(x==group)
    value_groups.append(y[ind])
# plot
#箱形图
fig=plt.figure()
ax=plt.gca()
boxes=ax.boxplot(value_groups,patch_artist=True,tick_labels=groups,
               showmeans=True,meanprops={'marker':'o','mfc':'w','mec':'k'},
               medianprops={'color':'yellow'})
# 自定义
for box,color in zip(boxes['boxes'],plt.get_cmap('Set1').colors):
    box.set_facecolor(color)
ax.set_ylabel(valuename)
fname_fig='Lecture3_7_box.pdf'
plt.savefig(fname_fig)
plt.savefig('sciviz-box-violin_preview_2.png', bbox_inches='tight', dpi=110)
plt.close('all')

# 小提琴图
fig=plt.figure()
ax=plt.gca()
violins=ax.violinplot(value_groups,bw_method='silverman')
violins['cbars'].set_color('k')
violins['cmins'].set_color('k')
violins['cmaxes'].set_color('k')
for violin,pos,box,mean in zip(violins['bodies'],range(0,len(groups)),boxes['boxes'],boxes['means']):
    violin.set_facecolor(box.get_facecolor())
    violin.set_alpha(1)
    violin.set_edgecolor('k')
    upper_fourth=box.get_path().vertices[:-1,1].max()
    lower_fourth=box.get_path().vertices[:-1,1].min()
    ax.vlines(pos+1,ymin=lower_fourth,ymax=upper_fourth,color='k',lw=4)
    ax.plot(pos+1,mean.get_ydata(),'o',mfc='w',mec='k')
ax.set_ylabel(valuename)

fname_fig='Lecture3_7_violin.pdf'
plt.savefig(fname_fig)
plt.savefig('sciviz-box-violin_preview_3.png', bbox_inches='tight', dpi=110)
plt.close('all')

# library & dataset
import seaborn as sns, numpy as np
df = sns.load_dataset("iris")
# Basic violinplot
ax = sns.violinplot(x="species", y="sepal_length", data=df)
# Calculate number of obs per group & median to position labels
medians = df.groupby(['species'])['sepal_length'].median().values
nobs = df['species'].value_counts().values
nobs = [str(x) for x in nobs.tolist()]
nobs = ["n: " + i for i in nobs]
# Add it to the plot
pos = range(len(nobs))
for tick,label in zip(pos,ax.get_xticklabels()):
   ax.text(pos[tick], medians[tick] + 0.03, nobs[tick], horizontalalignment='center', size='x-small', color='w', weight='semibold')
#sns.plt.savefig('sciviz-box-violin_preview_4.png', bbox_inches='tight', dpi=110)
plt.close('all')
fname_fig='Lecture3_7_violin_seaborn.pdf'
plt.savefig(fname_fig)