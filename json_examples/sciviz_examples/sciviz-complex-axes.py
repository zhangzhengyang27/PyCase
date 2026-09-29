import matplotlib as mpl
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

import numpy as np
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
mpl.rcParams["font.family"] = 'Arial'  #默认字体类型
mpl.rcParams["mathtext.fontset"] = 'cm' #数学文字字体

dt = 0.01
t = np.arange(dt, 20.0, dt)

y=np.log10(t)

# 线性坐标轴
plt.figure(figsize=(4,3), constrained_layout='True')
ax=plt.gca()
ax.plot(t,y)
ax.grid()
# save fig
plt.savefig('plot_logt.pdf')

# x轴为对数
plt.figure(figsize=(4,3), constrained_layout='True')
ax=plt.gca()
ax.semilogx(t,y)
ax.grid()
# save fig
plt.savefig('semilogx.pdf')

plt.savefig('sciviz-complex-axes_preview.png', bbox_inches='tight', dpi=110)
plt.close('all')

dt = 0.01
t = np.arange(dt, 20.0, dt)
y=np.exp(t)

# 线性坐标轴
plt.figure(figsize=(4,3), constrained_layout='True')
ax=plt.gca()
ax=plt.gca()
ax.plot(t,y)
ax.grid()
# save fig
plt.savefig('plot_10t.pdf')

# y轴为对数
plt.figure(figsize=(4,3), constrained_layout='True')
ax=plt.gca()
ax.semilogy(t,y)
ax.grid()
# save fig
plt.savefig('semilogy.pdf')

# x，y轴均为对数
plt.figure(figsize=(4,3), constrained_layout='True')
ax=plt.gca()
ax.loglog(t,y)
ax.grid()
# save fig
plt.savefig('loglog.pdf')

plt.savefig('sciviz-complex-axes_preview_2.png', bbox_inches='tight', dpi=110)
plt.close('all')

plt.figure(figsize=(8,3), constrained_layout='True')
ax=plt.gca()


# 1. 绘制每个物理量对应的曲线
p1, = ax.plot([0, 1, 2], [0, 1, 2], "b-", label="Density")

# 2. 创建第二个（右边）Y轴，与第一个Y轴（左边）共享x轴
ax2=ax.twinx()
p2, = ax2.plot([0, 1, 2], [0, 3, 2], "r-", label="Temperature")

# 3. 设置每个物理量对应y轴的label
ax.set_xlabel("Time")
ax.set_ylabel("Density")
ax2.set_ylabel("Temperature")

# 4. 设置每个y轴的颜色与对应的曲线颜色一致
ax.yaxis.label.set_color(p1.get_color())
ax2.yaxis.label.set_color(p2.get_color())

# 5. 设置坐标轴属性，可以使用字典批量设置(在第一章第二节中讲过)
tkw = dict(size=4, width=1.5)
ax.tick_params(axis='y', colors=p1.get_color(), **tkw)
ax2.tick_params(axis='y', colors=p2.get_color(), **tkw)

# # plt.legend()
# plt.legend(handles=(p1,p2),loc='upper left')


# save fig
plt.savefig('multiY.pdf')
plt.savefig('sciviz-complex-axes_preview_3.png', bbox_inches='tight', dpi=110)
plt.close('all')

dt = 0.01
t = np.arange(dt, 20.0, dt)
y=np.exp(t)

# 1. 主图
plt.figure(figsize=(4,3), constrained_layout='True')
ax=plt.gca()
ax.plot(t,y)

# 2. 图中图
axin=ax.inset_axes([0.02,0.45,0.48,0.48]) # 括号内参数：x0,y0,w,h
# axin.xaxis.set_ticks([])
# axin.yaxis.set_ticks([])
axin.yaxis.set_ticks_position('right')
axin.plot(t,y)
axin.set_xlim(15,20)
axin.set_ylim(0,4E8)

# 3. 添加一个指示框
ax.indicate_inset_zoom(axin,fc='lightgreen',alpha=0.5,ec='red') #face color, edge color

# save fig
plt.savefig('inset1_indicate.pdf')

plt.savefig('sciviz-complex-axes_preview_4.png', bbox_inches='tight', dpi=110)
plt.close('all')

from matplotlib.ticker import MultipleLocator

# 1. 创建多行多列子图阵列
fig,axs=plt.subplots(2,2,sharex=True,sharey=True,constrained_layout=True,figsize=(5,3),
                     gridspec_kw={"width_ratios":[1,1],"height_ratios":[1,1],"hspace":0.1,"wspace":0.1}
                    )

# 2. ax的获取方式 axs[i][j]
for i in range(0,2):
    for j in range(0,2):
        axs[i][j].text(0.5,0.5,'axs['+str(i)+']'+'['+str(j)+']',va='center',ha='center')
        axs[i][j].xaxis.set_major_locator(MultipleLocator(0.2))
        axs[i][j].yaxis.set_major_locator(MultipleLocator(0.4))
        axs[i][j].set_xlim(0,1)
        axs[i][j].set_ylim(0,1)
axs[1][1].plot([0,1],[0,4])

# save fig
plt.savefig('subplots1.pdf')

# 1. 创建子图阵列
fig,axs=plt.subplots(2,2,sharex=True,sharey=True,gridspec_kw={"width_ratios":[1,1],"height_ratios":[1,1]},
                         figsize=(5,3),constrained_layout=True)
for i in range(0,2):
    for j in range(0,2):
        axs[i][j].text(0.5,0.5,'axs['+str(i)+']'+'['+str(j)+']',va='center',ha='center')
        axs[i][j].xaxis.set_major_locator(MultipleLocator(0.2))
        axs[i][j].yaxis.set_major_locator(MultipleLocator(0.4))

# 2. 获取子图网格
gs=axs[0][0].get_gridspec()

# 3. 在子图网格范围内新建子图，比如第二列
axbig = fig.add_subplot(gs[:, 1])
axbig.xaxis.set_major_locator(MultipleLocator(0.2))
axbig.yaxis.set_major_locator(MultipleLocator(0.2))
axbig.text(0.5,0.5,'Combined big axis',va='center',ha='center')

# 4. 删除不用的坐标轴
axs[0][1].remove()
axs[1][1].remove()

# save fig
plt.savefig('subplots1_combine.pdf')