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
import meshio 
import h5py
import scipy.interpolate

mesh=meshio.read('Data/UnstructuredGrid/porous1.vtu')
print(mesh)

x,y,z=mesh.points[:,0],mesh.points[:,1],mesh.points[:,2]
triangles=mesh.cells[0].data
pointdata=mesh.point_data['RegionId']
celldata=mesh.cell_data['RegionId'][0]

fig=plt.figure(figsize=(8,8))
ax=plt.gca()
ax.axis('scaled')

# 分离出z=z0的某个面上的网格
z1_triangles,z2_triangles,z3_triangles=z[triangles[:,0]],z[triangles[:,1]],z[triangles[:,2]]
z0=np.min(z)
ind_triangles_z0=((z1_triangles==z0) & (z2_triangles==z0) &(z3_triangles==z0))

# ax.triplot(x,y,triangles[ind_triangles_z0],lw=0.1)
# ax.tricontourf(x,y,triangles[ind_triangles_z0],pointdata,cmap='rainbow')
# ax.tripcolor(x,y,triangles[ind_triangles_z0],pointdata,cmap='rainbow',edgecolor='face')  # 划重点： edgecolor='face' 避免出现白色的“幽灵线条”
ax.tripcolor(x,y,triangles[ind_triangles_z0,:],facecolors=celldata[ind_triangles_z0],edgecolor='face')

ax.set_xlim(np.min(x),np.max(x))
ax.set_ylim(np.min(y),np.max(y))
fname_fig='Lecture3_2_example1.pdf'
fig.savefig(fname_fig)

plt.savefig('sciviz-unstructured-mesh_preview.png', bbox_inches='tight', dpi=110)
plt.close('all')

meshfile='Data/UnstructuredGrid/XDMF/MESH.h5'
fieldfile='Data/UnstructuredGrid/XDMF/Data_06000.h5'
MESH=h5py.File(meshfile,'r')
VAR=h5py.File(fieldfile,'r')
print(MESH.keys(),VAR.keys())

# get points coordinate and triangles
GCOORD=MESH['GCOORD'][:]
x=GCOORD[:,0]
y=GCOORD[:,1]
triangles=MESH['EL2NOD'][:]
triangles=triangles.reshape(-1,4)
triangles=triangles[:,1:4]
phaseID=MESH['PhaseID'][:]-1
phaseID_unique=np.unique(phaseID)
print('The mesh contains',len(phaseID_unique),'regions')

# plot
fig=plt.figure(figsize=(12,4))
ax=fig.gca()
ax.axis('scaled')
ax.set_xlim(np.min(x),np.max(x))
ax.set_ylim(np.min(y),np.max(y))

# 1. plot mesh
for phaseid in phaseID_unique:
    ax.triplot(x,y,triangles[phaseID==phaseid],lw=0.1)
fname_fig='Lecture3_2_example2_mesh.pdf'

fig.savefig(fname_fig)

plt.savefig('sciviz-unstructured-mesh_preview_2.png', bbox_inches='tight', dpi=110)
plt.close('all')

# plot
fig=plt.figure(figsize=(12,4))
ax=fig.gca()
ax.axis('scaled')
ax.set_xlim(np.min(x),np.max(x))
ax.set_ylim(np.min(y),np.max(y))

# get field
# fields_name=list(VAR.keys())
fieldname='T'
var=VAR[fieldname][:]

# 2. plot field contour
CS=ax.tricontourf(x,y,triangles,var,cmap='Spectral_r',levels=100,extend='both')
# ax.tricontour(x,y,triangles,var,linewidths=1)
# for a in CS.collections:
#     a.set_edgecolor('face')
#     a.set_linewidth(0.00)

# 3. 流场图
vx=VAR['Vx'][:]
vy=VAR['Vz'][:]
v_norm = np.sqrt(vx**2 + vy**2)
# 3.1 quiver
# ax.quiver(x, y, vx/v_norm, vy/v_norm,
#           scale=100., zorder=3, color='blue',
#           width=0.004, headwidth=3., headlength=10.)
# 3.2 stream plot: interpolate to a structured grid first
YY,XX = np.mgrid[np.min(y):np.max(y):200j,np.min(x):np.max(x):200j]
VX = scipy.interpolate.griddata((x,y), vx, (XX.reshape(-1,), YY.reshape(-1,)), method='cubic').ravel()
VY = scipy.interpolate.griddata((x,y), vy, (XX.reshape(-1,), YY.reshape(-1,)), method='cubic').ravel()
VX,VY=VX.reshape(XX.shape),VY.reshape(XX.shape)
seed_x=[-200,-150, -100,-10,10, 0, 100,150, 200]
seed_points = np.array([seed_x, np.zeros_like(seed_x)-50])
ax.streamplot(XX,YY, VX,VY,density=[4, 2],linewidth=0.8,color='w',start_points=seed_points.T)

# axis lim
ax.set_xlim(np.min(x),np.max(x))
ax.set_ylim(np.min(y),np.max(y))

fname_fig=str('Lecture3_2_example2_%s.pdf'%(fieldname))
fig.savefig(fname_fig)

plt.savefig('sciviz-unstructured-mesh_preview_3.png', bbox_inches='tight', dpi=110)
plt.close('all')