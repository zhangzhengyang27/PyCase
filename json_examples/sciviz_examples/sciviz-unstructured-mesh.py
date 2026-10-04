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

# —— 演示数据自播种：原始 porous1.vtu（多孔介质有限元网格）已不在数据源中，
#    改为程序化生成等效的多层非结构网格（自播种口径：生成演示数据 → 继续原逻辑）
def _demo_mesh():
    xs, ys, zs = np.linspace(0, 400, 21), np.linspace(0, 200, 11), np.array([0.0, 50.0, 100.0])
    pts = np.array([[x, y, z] for z in zs for y in ys for x in xs])
    nx, ny = len(xs), len(ys)
    tris = []
    for j in range(ny - 1):
        for i in range(nx - 1):
            a = j * nx + i
            tris += [[a, a + 1, a + nx], [a + 1, a + nx + 1, a + nx]]
    tris = np.array(tris)  # cells[0] = z0 底面三角网
    return meshio.Mesh(
        pts, [("triangle", tris)],
        point_data={"RegionId": np.array([1 + int(p[0] // 134) for p in pts])},
        cell_data={"RegionId": [np.array([1 + int(np.mean(pts[t][:, 0]) // 134) for t in tris])]},
    )

mesh = _demo_mesh()
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

# —— 演示数据自播种：原 MESH.h5 / Data_06000.h5（XDMF 仿真输出）已不在数据源中，
#    程序化生成等效的非结构三角网格与温度/速度场（自播种口径）
rng = np.random.default_rng(42)
_gx, _gy = np.linspace(-250, 250, 41), np.linspace(-100, 100, 17)
_XX0, _YY0 = np.meshgrid(_gx, _gy)
GCOORD = np.column_stack([_XX0.ravel() + rng.uniform(-4, 4, _XX0.size),
                          _YY0.ravel() + rng.uniform(-3, 3, _YY0.size)])
import scipy.spatial
_simp = scipy.spatial.Delaunay(GCOORD).simplices
EL2NOD = np.column_stack([np.arange(1, len(_simp) + 1), _simp + 1])  # 1-based，沿 XDMF 惯例
triangles = EL2NOD.reshape(-1, 4)[:, 1:4] - 1  # EL2NOD 1-based → 点索引 0-based
x = GCOORD[:, 0]
y = GCOORD[:, 1]
phaseID = np.array([1 + int(np.mean(GCOORD[t][:, 0]) > 0) + int(np.mean(GCOORD[t][:, 0]) > 120)
                    for t in triangles])
phaseID_unique = np.unique(phaseID)
print('The mesh contains', len(phaseID_unique), 'regions')

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
fieldname='T'
var = 1200 + 900 * np.exp(-((GCOORD[:, 0] / 90) ** 2)) + 40 * np.sin(GCOORD[:, 1] / 18) \
    + rng.normal(0, 5, len(GCOORD))
vx = 25 * np.sin(GCOORD[:, 1] / 28) * np.cos(GCOORD[:, 0] / 130)
vy = -18 * np.cos(GCOORD[:, 1] / 34) * np.sin(GCOORD[:, 0] / 160)  # 原 VAR['Vz']，平面流场第二分量

# 2. plot field contour
CS=ax.tricontourf(x,y,triangles,var,cmap='Spectral_r',levels=100,extend='both')
# ax.tricontour(x,y,triangles,var,linewidths=1)
# for a in CS.collections:
#     a.set_edgecolor('face')
#     a.set_linewidth(0.00)

# 3. 流场图
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