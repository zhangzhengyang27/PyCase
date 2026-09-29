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
from netCDF4 import Dataset
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

def genVelocity(m,x,y):
    U,V=m*(x - x**3/3 - y), x/m
    return U,V

l = 8.0 #x，y轴尺度的半宽度
n = 300 # 采样点个数
mu = 0.5
x=np.linspace(-l,l,n)
y=np.linspace(-l,l,n)
X,Y=np.meshgrid(x,y)
U,V=genVelocity(mu,X,Y)
vel=(U**2 + V**2)**0.5
lw=4*vel/np.max(vel)

fig=plt.figure(figsize=(6,6))
ax=plt.gca()
stream=ax.streamplot(X,Y,U,V,
              arrowsize=1,
              arrowstyle='->',
              density=(1,1),
              color=vel, #'xkcd:lightblue',
              linewidth=1,
              cmap='jet'
             )
# plt.colorbar(stream.lines)

# savefig
plt.tight_layout()
plt.savefig('Lecture2_11_streamplot.pdf')

plt.savefig('sciviz-streamplot_preview.png', bbox_inches='tight', dpi=110)
plt.close('all')


fig=plt.figure(figsize=(5,5))
ax=plt.gca()
interval=10
skip=(slice(None, None,interval),slice(None, None, interval)) # slice(start, stop, step)
q=ax.quiver(X[skip],Y[skip],U[skip],V[skip],
          vel[skip],
          units='xy',angles='xy',scale=25,pivot='tip',
          color='k',
          cmap='rainbow'
         )
# ax.quiverkey(q, X=0.3, Y=1.05, U=100,label='Quiver key, length = 10', labelpos='E',coordinates='axes',clip_on=False)
ax.scatter(X[skip],Y[skip],color='r',s=0.5)
# savefig
plt.tight_layout()
plt.savefig('Lecture2_11_quiver.pdf')

plt.savefig('sciviz-streamplot_preview_2.png', bbox_inches='tight', dpi=110)
plt.close('all')

# 1. 读取nc
data=Dataset('data/streamplot/globalWind.nc')
# print(data.variables) #查看变量
lon=data.variables['longitude'][:]
lat=data.variables['latitude'][:]
u=data.variables['u100'][:]
v=data.variables['v100'][:]
U=u.reshape((u.shape[1],u.shape[2]))
V=v.reshape((v.shape[1],v.shape[2]))
vel=(U**2 + V**2)**0.5
# 构建网格
X, Y = np.meshgrid(lon, lat)
# 绘制等值线
fig=plt.figure(figsize=(8,4))
ax=plt.gca()
# ax.streamplot(X,Y,u,v)
interval=10
skip=(slice(None, None,interval),slice(None, None, interval)) # slice(start, stop, step)
# q=ax.quiver(X[skip],Y[skip],U[skip],V[skip],
#           vel[skip],
#           units='xy',angles='xy',scale=2,pivot='tip',
#           color='k',
#           cmap='rainbow'
#          )

stream=ax.streamplot(X[skip],Y[skip],U[skip],V[skip],
              arrowsize=0.5,
              arrowstyle='->',
              density=(3,3),
              color=vel[skip], #'xkcd:lightblue',
              linewidth=0.5,
              cmap='jet'
             )
# 设置等值文字标注
ax.set_xlabel('Longitude (degree)')
ax.set_ylabel('Latitude (degree)')
ax.set_title('Global wind velocity field at 0:00 on 2020/01/01')
ax.set_xlim(np.min(lon),np.max(lon))
ax.set_ylim(np.min(lat),np.max(lat))
# colorbar
caxis = inset_axes(ax, width="100%", height="100%", loc='lower left',
                   bbox_to_anchor=(1.02, 0., 0.02, 1), bbox_transform=ax.transAxes, borderpad=0,)
cb = plt.colorbar(stream.lines, cax = caxis,format='%.0f')  
cb.set_label('Velocity (m/s)')

whspace=0.06
plt.subplots_adjust(wspace=whspace,hspace=whspace,bottom=0.13,left=0.08,right=0.9,top=0.92)
# savefig
plt.savefig('Lecture2_11_example1.pdf')
plt.savefig('sciviz-streamplot_preview_3.png', bbox_inches='tight', dpi=110)
plt.close('all')


# 1. 读取nc
data=Dataset('data/streamplot/globalWind.nc')
# print(data.variables) #查看变量
lon=data.variables['longitude'][:]
lat=data.variables['latitude'][:]
u=data.variables['u100'][:]
v=data.variables['v100'][:]
U=u.reshape((u.shape[1],u.shape[2]))
V=v.reshape((v.shape[1],v.shape[2]))
vel=(U**2 + V**2)**0.5
# 构建网格
X, Y = np.meshgrid(lon, lat)
# 绘制等值线
fig=plt.figure(figsize=(8,4))
ax=plt.gca()
# ax.streamplot(X,Y,u,v)
interval=10
skip=(slice(None, None,interval),slice(None, None, interval)) # slice(start, stop, step)
q=ax.quiver(X[skip],Y[skip],U[skip],V[skip],
          vel[skip],
          units='xy',angles='xy',scale=3,pivot='tip',
          color='k',
          cmap='inferno',
          width=0.2
         )
# 设置等值文字标注
ax.set_xlabel('Longitude (degree)')
ax.set_ylabel('Latitude (degree)')
ax.set_title('Global wind velocity field at 0:00 on 2020/01/01')
ax.set_xlim(np.min(lon),np.max(lon))
ax.set_ylim(np.min(lat),np.max(lat))
# colorbar
caxis = inset_axes(ax, width="100%", height="100%", loc='lower left',
                   bbox_to_anchor=(1.02, 0., 0.02, 1), bbox_transform=ax.transAxes, borderpad=0,)
cb = plt.colorbar(q, cax = caxis,format='%.0f')  
cb.set_label('Velocity (m/s)')

whspace=0.06
plt.subplots_adjust(wspace=whspace,hspace=whspace,bottom=0.13,left=0.08,right=0.9,top=0.92)
# savefig
plt.savefig('Lecture2_11_example2.pdf')
plt.savefig('sciviz-streamplot_preview_4.png', bbox_inches='tight', dpi=110)
plt.close('all')

