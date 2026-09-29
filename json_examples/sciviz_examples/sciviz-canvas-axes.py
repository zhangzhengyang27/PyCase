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

fig=plt.figure(figsize=(12/2.54,5/2.54),facecolor='cyan', edgecolor='r', linewidth=1, constrained_layout='True')
# fig.set_facecolor('r')
ax=plt.gca()
# ax=fig.gca()

ax.set_facecolor('gray')
# plt.savefig('画布.pdf',facecolor=fig.get_facecolor(),edgecolor=fig.get_edgecolor())
ax.grid(axis='x',which='minor')
ax.spines['right'].set_linestyle('--')
plt.savefig('sciviz-canvas-axes_preview.png', bbox_inches='tight', dpi=110)
plt.close('all')

fig=plt.figure(figsize=(12/2.54,5/2.54),constrained_layout='True')

# 利用numpy的random函数产生随机数作为绘图演示数据
x=np.linspace(0.5,9.5,100)
y=np.random.random(len(x))*4.8+1
y2=np.random.random(len(x))*4.8+1
y3=np.sin(np.pi*x)*2+3
p1,=plt.plot(x,y,'o',color='red',label='data 1')
p2,=plt.plot(x,y2,'o',color='green',label='data 2')
p3,=plt.plot(x,y3,label='Sin($\pi x$)')
ax=plt.gca()

# 1. 图标题：title
# ax.set_title('First Figure',FontSize=12)
plt.title('First Figure',FontSize=12)

# 2. 坐标轴标签：xlabel, ylabel
ax.set_xlabel('x axis label')
ax.set_ylabel('y axis label')

# 3. 主刻度
ax.xaxis.set_major_locator(MultipleLocator(2))           #将x主刻度标签设置为2的倍数
ax.xaxis.set_major_formatter(FormatStrFormatter('%.0f')) #设置x轴标签文本的格式零位小数

ax.yaxis.set_major_locator(MultipleLocator(1))
ax.yaxis.set_major_formatter(FormatStrFormatter('%.0f'))

# ax.yaxis.set_major_locator(plt.NullLocator())           #取消ticks
# ax.xaxis.set_major_formatter(plt.NullFormatter()) 

# ax.xaxis.set_ticks(np.linspace(0,10,5))                 # 指定坐标刻度位置
# ax.xaxis.set_ticklabels(['a','b','c','d','e','f'])      # 指定坐标刻度标注文字

# # 4. 次（副）刻度：minor ticks       
# ax.xaxis.set_minor_locator(MultipleLocator(0.4)) #将x轴次刻度标签设置为0.4的倍数
# ax.yaxis.set_minor_locator(MultipleLocator(0.2)) #将此y轴次刻度标签设置为0.2的倍数

# 5. 网格：grid
ax.xaxis.grid(True, which='major',lw=0.1,color='red')    #x坐标轴的网格使用主刻度
ax.yaxis.grid(True, which='minor',lw=0.1,color='gray')      #y坐标轴的网格使用次刻度

# 6. 坐标轴范围：xlim, ylim
ax.set_xlim(0,10)
ax.set_ylim(0,8)

# 7. 坐标轴边框线：spines
# ax.spines['right'].set_visible(False)
# ax.spines['right'].set_position(("axes", 1.2))
# ax.spines['right'].set_bounds(2,4)
ax.spines['right'].set_color('red')
ax.spines['right'].set_linewidth(1)

# ax.axis('off')

# 8. legend
leg=ax.legend(loc='upper right',shadow=True,ncol=3)
# ax.legend(['a','b','c'],loc='upper right',shadow=True,ncol=3)

# 9. 图层：zorder
for p in [p1,p2,p3]:
    print(p.get_zorder())
p3.set_zorder(2)
print(leg.get_zorder())
leg.set_zorder(3)

# # save fig
plt.savefig('fig_axis.pdf')
plt.savefig('sciviz-canvas-axes_preview_2.png', bbox_inches='tight', dpi=110)
plt.close('all')