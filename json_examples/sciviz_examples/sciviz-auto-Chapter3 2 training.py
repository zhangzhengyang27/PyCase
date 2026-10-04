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
print(celldata)
print(np.unique(z))
print(triangles[1:3,:])

fig=plt.figure()
ax=plt.gca()
# 分离
z1_triangles, z2_triangles, z3_triangles=z[triangles[:,0]], z[triangles[:,1]], z[triangles[:,2]]
z0=np.min(z)
ind_triangles_z0=((z1_triangles == z0) & (z2_triangles == z0) &(z3_triangles == z0))
# ax.triplot(x,y,triangles[ind_triangles_z0,:])
# 
# ax.tricontourf(x,y,triangles,pointdata)
ax.tripcolor(x,y,triangles, facecolors=celldata)
plt.savefig('sciviz-auto-Chapter3 2 training_preview.png', bbox_inches='tight', dpi=110)
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
print(len(triangles),"个三角形", len(GCOORD),'个点')
x,y=GCOORD[:,0],GCOORD[:,1]
phaseID = np.array([1 + int(np.mean(GCOORD[t][:, 0]) > 0) + int(np.mean(GCOORD[t][:, 0]) > 120)
                    for t in triangles])
phaseID_unique = np.unique(phaseID)
print(phaseID_unique)

fig=plt.figure()

ax=plt.gca()
ax.axis('scaled')
ax.set_xlim(np.min(x),np.max(x))
ax.set_ylim(np.min(y),np.max(y))
# for phaseid in phaseID_unique:
#     ax.triplot(x,y,triangles[phaseID==phaseid,:], lw=0.2,label=phaseid)
# # ax.legend(handles=(),labels=())

var = 1200 + 900 * np.exp(-((GCOORD[:, 0] / 90) ** 2)) + 40 * np.sin(GCOORD[:, 1] / 18) \
    + rng.normal(0, 5, len(GCOORD))
ax.tricontourf(x,y,triangles,var,levels=100,extend='both')
# ax.tricontour(x,y,triangles,var,colors='w')

vx = 25 * np.sin(GCOORD[:, 1] / 28) * np.cos(GCOORD[:, 0] / 130)
vy = -18 * np.cos(GCOORD[:, 1] / 34) * np.sin(GCOORD[:, 0] / 160)  # 原 VAR['Vz']，平面流场第二分量
YY,XX = np.mgrid[np.min(y):np.max(y):200j, np.min(x):np.max(x):600j]
print(YY.shape,XX.shape)
VX = scipy.interpolate.griddata((x,y),vx, (XX.reshape(-1,),YY.reshape(-1,)) , method='cubic').ravel()
VY = scipy.interpolate.griddata((x,y),vy, (XX.reshape(-1,),YY.reshape(-1,)) , method='cubic').ravel()
VX=VX.reshape(XX.shape)
VY=VY.reshape(XX.shape)
seed_x=[-200,-100,0,100,200]
seed_y=np.zeros_like(seed_x)-50
seed_points=np.array([seed_x,seed_y])

ax.streamplot(XX,YY,VX,VY,density=[4,2], start_points=seed_points.T, color='w')

plt.savefig('sciviz-auto-Chapter3 2 training_preview_2.png', bbox_inches='tight', dpi=110)
plt.close('all')