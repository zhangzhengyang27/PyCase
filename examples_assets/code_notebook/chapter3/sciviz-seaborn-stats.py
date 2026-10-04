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

import matplotlib

vegetables = ["cucumber", "tomato", "lettuce", "asparagus",
              "potato", "wheat", "barley"]
farmers = ["Farmer Joe", "Upland Bros.", "Smith Gardening",
           "Agrifun", "Organiculture", "BioGoods Ltd.", "Cornylee Corp."]

harvest = np.array([[0.8, 2.4, 2.5, 3.9, 0.0, 4.0, 0.0],
                    [2.4, 0.0, 4.0, 1.0, 2.7, 0.0, 0.0],
                    [1.1, 2.4, 0.8, 4.3, 1.9, 4.4, 0.0],
                    [0.6, 0.0, 0.3, 0.0, 3.1, 0.0, 0.0],
                    [0.7, 1.7, 0.6, 2.6, 2.2, 6.2, 0.0],
                    [1.3, 1.2, 0.0, 0.0, 0.0, 3.2, 5.1],
                    [0.1, 2.0, 0.0, 1.4, 0.0, 1.9, 6.3]])

fig=plt.figure(figsize=(6,6))
ax=plt.gca()
interp=None
im = ax.imshow(harvest,cmap='plasma',interpolation=interp) #mitchell

ax.set_xticks(np.arange(len(farmers)))
ax.set_yticks(np.arange(len(vegetables)))
ax.set_xticklabels(farmers)
ax.set_yticklabels(vegetables)

plt.setp(ax.get_xticklabels(), rotation=45, ha="right",rotation_mode="anchor")

for i in range(len(vegetables)):
    for j in range(len(farmers)):
        text = ax.text(j, i, harvest[i, j],
                       ha="center", va="center", color="w")

ax.set_title("Harvest of local farmers (in tons/year)")
ax.set_ylim(-0.5,len(vegetables)-0.5)

plt.tight_layout(pad=0.)

fname_fig=str('Lecture3_3_basic_%s.pdf'%(interp))
plt.savefig(fname_fig)
plt.savefig('sciviz-seaborn-stats_preview.png', bbox_inches='tight', dpi=110)
plt.close('all')

data=harvest
# 分级色阶
minlevel,maxlevel=int(np.min(data)),int(np.max(data))
nlevel=int(maxlevel-minlevel)+1
norm = matplotlib.colors.BoundaryNorm(np.linspace(minlevel-0.5,maxlevel+0.5, nlevel+1), nlevel) # 划重点
# plot
fig=plt.figure(figsize=(6,6))
ax=plt.gca()
im = ax.imshow(harvest,cmap=plt.get_cmap("Paired", nlevel), norm=norm) #mitchell 
cbar_kw=dict(ticks=np.arange(minlevel,maxlevel+1))
ax_cb=ax.inset_axes([1.02,0,0.05,1],transform=ax.transAxes)
cbar = plt.colorbar(im, cax=ax_cb,label='Harvest',**cbar_kw)
# grid
ax.set_xticks(np.arange(data.shape[1]+1)-.5, minor=True)
ax.set_yticks(np.arange(data.shape[0]+1)-.5, minor=True)
ax.grid(which="minor", color="w", linestyle='-', linewidth=3)
ax.tick_params(which="minor", bottom=False, left=False)
# -------------------------------------------------------
ax.set_xticks(np.arange(len(farmers)))
ax.set_yticks(np.arange(len(vegetables)))
ax.set_xticklabels(farmers)
ax.set_yticklabels(vegetables)

plt.setp(ax.get_xticklabels(), rotation=45, ha="right",rotation_mode="anchor")

for i in range(len(vegetables)):
    for j in range(len(farmers)):
        text = ax.text(j, i, harvest[i, j],
                       ha="center", va="center", color="k")

ax.set_title("Harvest of local farmers (in tons/year)")
ax.set_ylim(-0.5,len(vegetables)-0.5)

plt.tight_layout()

fname_fig='Lecture3_3_basic2.pdf'
plt.savefig(fname_fig)

plt.savefig('sciviz-seaborn-stats_preview_2.png', bbox_inches='tight', dpi=110)
plt.close('all')

# 数据随包内联（原课件读 Data/mtcars/mtcars.csv；工作区不携带 Data/ 目录，内联后随处可跑）
MTCARS_CSV = """model,mpg,cyl,disp,hp,drat,wt,qsec,vs,am,gear,carb
Mazda RX4,21,6,160,110,3.9,2.62,16.46,0,1,4,4
Mazda RX4 Wag,21,6,160,110,3.9,2.875,17.02,0,1,4,4
Datsun 710,22.8,4,108,93,3.85,2.32,18.61,1,1,4,1
Hornet 4 Drive,21.4,6,258,110,3.08,3.215,19.44,1,0,3,1
Hornet Sportabout,18.7,8,360,175,3.15,3.44,17.02,0,0,3,2
Valiant,18.1,6,225,105,2.76,3.46,20.22,1,0,3,1
Duster 360,14.3,8,360,245,3.21,3.57,15.84,0,0,3,4
Merc 240D,24.4,4,146.7,62,3.69,3.19,20,1,0,4,2
Merc 230,22.8,4,140.8,95,3.92,3.15,22.9,1,0,4,2
Merc 280,19.2,6,167.6,123,3.92,3.44,18.3,1,0,4,4
Merc 280C,17.8,6,167.6,123,3.92,3.44,18.9,1,0,4,4
Merc 450SE,16.4,8,275.8,180,3.07,4.07,17.4,0,0,3,3
Merc 450SL,17.3,8,275.8,180,3.07,3.73,17.6,0,0,3,3
Merc 450SLC,15.2,8,275.8,180,3.07,3.78,18,0,0,3,3
Cadillac Fleetwood,10.4,8,472,205,2.93,5.25,17.98,0,0,3,4
Lincoln Continental,10.4,8,460,215,3,5.424,17.82,0,0,3,4
Chrysler Imperial,14.7,8,440,230,3.23,5.345,17.42,0,0,3,4
Fiat 128,32.4,4,78.7,66,4.08,2.2,19.47,1,1,4,1
Honda Civic,30.4,4,75.7,52,4.93,1.615,18.52,1,1,4,2
Toyota Corolla,33.9,4,71.1,65,4.22,1.835,19.9,1,1,4,1
Toyota Corona,21.5,4,120.1,97,3.7,2.465,20.01,1,0,3,1
Dodge Challenger,15.5,8,318,150,2.76,3.52,16.87,0,0,3,2
AMC Javelin,15.2,8,304,150,3.15,3.435,17.3,0,0,3,2
Camaro Z28,13.3,8,350,245,3.73,3.84,15.41,0,0,3,4
Pontiac Firebird,19.2,8,400,175,3.08,3.845,17.05,0,0,3,2
Fiat X1-9,27.3,4,79,66,4.08,1.935,18.9,1,1,4,1
Porsche 914-2,26,4,120.3,91,4.43,2.14,16.7,0,1,5,2
Lotus Europa,30.4,4,95.1,113,3.77,1.513,16.9,1,1,5,2
Ford Pantera L,15.8,8,351,264,4.22,3.17,14.5,0,1,5,4
Ferrari Dino,19.7,6,145,175,3.62,2.77,15.5,0,1,5,6
Maserati Bora,15,8,301,335,3.54,3.57,14.6,0,1,5,8
Volvo 142E,21.4,4,121,109,4.11,2.78,18.6,1,1,4,2
"""
data_cars=pd.read_csv(io.StringIO(MTCARS_CSV))
df = data_cars.set_index('model')
df.index.name = None

clustermap=sns.clustermap(df, z_score=1,cmap='magma')  #dendrogram_row.linkage
clusterdata=clustermap.data2d
plt.close()

models=clusterdata.index
values=np.array(clusterdata.values,dtype=float)
# values_norm=values/values.max(axis=0)
names=clusterdata.columns.values
print(len(models),len(names),values.shape)


fig=plt.figure(figsize=(6,6))
ax=plt.gca()
x = np.arange(values.shape[1] + 1)
y = np.arange(values.shape[0] + 1)
# 第一种方式
# im = ax.imshow(values,cmap='magma',aspect='auto') #mitchell 
# 第二种方式
ax.pcolormesh(x,y,values,cmap='magma')

# set axes
ax.set_xlim(x.min(),x.max())
ax.set_xticks(x[:-1]+0.5)
ax.set_xticklabels(names)
ax.set_ylim(y.min(),y.max())
ax.set_yticks(y[:-1]+0.5)
ax.set_yticklabels(models)
ax.invert_yaxis()

plt.tight_layout()

fname_fig='Lecture3_3_example1.pdf'
plt.savefig(fname_fig)

plt.savefig('sciviz-seaborn-stats_preview_3.png', bbox_inches='tight', dpi=110)
plt.close('all')

# 数据随包内联（原课件读 Data/190830_EGFR_immune cells/ 下的 Spearman/P-value）
SPEARMAN_CSV = """name,B_cells_naive,B_cells_memory,Plasma_cells,T_cells_CD8,T_cells_CD4_naive,T_cells_CD4_memory_resting,T_cells_CD4_memory_activated,T_cells_follicular_helper,T_cells_regulatory_(Tregs),T_cells_gamma_delta,NK_cells_resting,NK_cells_activated,Monocytes,Macrophages_M0,Macrophages_M1,Macrophages_M2,Dendritic_cells_resting,Dendritic_cells_activated,Mast_cells_resting,Mast_cells_activated,Eosinophils,Neutrophils
TCGA_HNSC,0.012007102,-0.082696923,-0.124,-0.315,0.072209341,0.323,-0.168,-0.28,-0.18,-0.175,0.098,-0.172,0.002139082,0.1,-0.119,-0.17,-0.064713389,-0.015294416,-0.128,0.169,0.071282789,0.031327261
GSE117973,-0.321,-0.050793599,-0.089213066,-0.517,0.331,-0.015593008,-0.432,-0.37,-0.127685908,-0.403,0.20514877,-0.180659009,-0.10231878,0.212262873,-0.411,-0.278,0.094159278,0.20269071,-0.382,0.299,0.14345476,0.010354974
GSE39368,0.224,-0.358,-0.278,-0.325,-0.005030505,0.176,0.041163322,-0.078833044,-0.161620534,0.137002426,0.087725366,-0.150726817,-0.271,0.125857632,-0.227,-0.22,-0.050424459,0.115617725,-0.338,0.357,-0.084408603,0.193
GSE40774,-0.446,0.162998104,-0.093850154,-0.381,0.1326896,0.297,-0.12582143,-0.47,-0.292,-0.322,0.091770745,0.09597787,0.149649087,-0.030481996,-0.357,-0.204,0.176,-0.152800727,-0.123631064,0.064332636,0.167343862,0.175
GSE65858,0.031275733,-0.215,0.021739102,-0.275,-0.059305521,0.033624315,-0.298,-0.291,-0.067435516,-0.347,0.023153859,0.021577003,0.143,0.0919416,-0.131,-0.285,0.064651911,0.084428475,-0.213,0.386,0.151,0.144
TCPA_HNSC_EGFR,-0.055747941,0.037917338,-0.074707444,-0.095479176,0.007384778,0.022938726,-0.087607222,-0.102540185,-0.059622552,-0.008945456,0.010453635,-0.112,0.092890439,-0.067091657,-0.159,-0.064548718,-0.00604317,-0.063358269,-0.080159332,0.051026138,0.065693887,-0.027442332
TCPA_HNSC_EGFR_pY1068,-0.026265175,0.073410671,-0.055704294,-0.122,0.103535516,-0.04093563,-0.040805363,-0.045439007,-0.030461655,0.051835775,-0.004848502,-0.143,0.103904227,-0.095550011,-0.141,-0.08577067,0.034865642,0.000375157,-0.067874305,0.03302313,-0.005950686,0.007474297
TCPA_HNSC_EGFR_pY1173,-0.173,0.08921614,-0.166,-0.155,0.106331701,0.138,-0.121,-0.232,-0.17,-0.047948583,0.026101173,-0.053020027,0.029201728,-0.030729013,-0.066651118,-0.114,0.013483034,0.019172664,-0.111,0.109,0.050736155,0.024714736"""
PVALUE_CSV = """name,B_cells_naive,B_cells_memory,Plasma_cells,T_cells_CD8,T_cells_CD4_naive,T_cells_CD4_memory_resting,T_cells_CD4_memory_activated,T_cells_follicular_helper,T_cells_regulatory_(Tregs),T_cells_gamma_delta,NK_cells_resting,NK_cells_activated,Monocytes,Macrophages_M0,Macrophages_M1,Macrophages_M2,Dendritic_cells_resting,Dendritic_cells_activated,Mast_cells_resting,Mast_cells_activated,Eosinophils,Neutrophils
TCGA_HNSC,0.788834306,0.064646182,0.005595373,5.26477E-13,0.106806553,1.29274E-13,0.000163043,1.72647E-10,5.11827E-05,8.37381E-05,0.027944631,0.000107557,0.961946043,0.025446668,0.007530696,0.000136423,0.148477973,0.732985004,0.004065567,0.000143,0.111391933,0.484603808
GSE117973,0.003476065,0.652473964,0.428349562,7.91848E-07,0.002529253,0.890110637,5.71805E-05,0.000679943,0.255969636,0.000190899,0.066175186,0.106533959,0.363379317,0.057117172,0.00013828,0.011859674,0.403086367,0.069562345,0.000426979,0.006733259,0.201374461,0.926897709
GSE39368,0.008366656,1.6611E-05,0.000941221,0.000100377,0.953304246,0.038466339,0.631679432,0.358050385,0.058249968,0.109080457,0.306241641,0.07762608,0.001330738,0.141318269,0.00739708,0.009627443,0.556975998,0.176894173,4.98739E-05,1.74427E-05,0.324960561,0.02318564
GSE40774,6.77115E-08,0.059867611,0.280766681,5.66013E-06,0.126420851,0.000493411,0.147447494,1.01543E-08,0.000623164,0.000145697,0.291609262,0.269955815,0.084380468,0.72661631,2.31039E-05,0.018226836,0.042073887,0.077969536,0.154680698,0.460215098,0.053279573,0.043434868
GSE65858,0.620509292,0.000576579,0.730763594,9.33327E-06,0.347490526,0.594497753,1.43231E-06,2.47503E-06,0.285280272,1.47828E-08,0.713984491,0.732694484,0.022689241,0.14476635,0.036668676,4.20149E-06,0.305678829,0.180681932,0.00064706,2.10216E-10,0.016521336,0.022226475
TCPA_HNSC_EGFR,0.311923324,0.49177836,0.175119369,0.082832155,0.893522912,0.677549414,0.111631125,0.062404282,0.279432015,0.871198861,0.849722174,0.040822823,0.091555302,0.223459607,0.003719307,0.241542481,0.9127814,0.25035101,0.145614796,0.354742131,0.233276124,0.618854528
TCPA_HNSC_EGFR_pY1068,0.633983616,0.182749851,0.312302909,0.026125295,0.05989071,0.457934511,0.459367798,0.409946051,0.580788818,0.347148936,0.929973976,0.009292761,0.058981056,0.082603236,0.010228369,0.119368767,0.527310223,0.994574771,0.21809331,0.549377192,0.914110999,0.892239986
TCPA_HNSC_EGFR_pY1173,0.001583061,0.105181285,0.0023864,0.004762528,0.053273183,0.011964427,0.027408861,2.06957E-05,0.00196722,0.384547382,0.63610373,0.336229342,0.596540514,0.57747139,0.226521231,0.038752369,0.80693232,0.728194375,0.043419714,0.046867104,0.357486943,0.654144075"""

data_TCGA=pd.read_csv(io.StringIO(SPEARMAN_CSV))
header=data_TCGA.columns.values
names=data_TCGA[header[0]].values
cells=header[1:]
sValue=np.array(data_TCGA.values[:,1:],dtype=float)

data_pvalue=pd.read_csv(io.StringIO(PVALUE_CSV))
pValue=np.array(data_pvalue.values[:,1:],dtype=float)

# plot
fig=plt.figure(figsize=(8,4))
ax=plt.gca()
y=np.linspace(1,len(names),len(names))
x=np.linspace(1,len(cells),len(cells))
xx,yy=np.meshgrid(x,y)
factor_markersize=300
marker_size=np.abs(sValue)*factor_markersize
ind_available=(sValue<0.002)
ind_large=(pValue>0.05) 
ind_large=(ind_large & ind_available)
ind_small=(pValue<=0.05) 
ind_small = (ind_small & ind_available)
color_positive=(236/255,51/255,35/255)
color_negative=(109/255,149/255,230/255)

ax.scatter(xx[ind_small],yy[ind_small],s=marker_size[ind_small],marker='o',color=color_negative)
ax.scatter(xx[ind_large],yy[ind_large],s=marker_size[ind_large],marker='o',color=color_positive)
# plot legend
ax.scatter(-10,-10,color=color_positive,s=factor_markersize*0.5,marker='o',label='Positive')
ax.scatter(-10,-10,color=color_negative,s=factor_markersize*0.5,marker='o',label='Negative')
leg1=ax.legend(ncol=2,columnspacing=0,handletextpad=0.1,frameon=False,bbox_to_anchor=(1,0))
ax.add_artist(leg1)
marksize_legend=[0.1,0.2,0.3,0.4,0.5]
art_list=[]
label_list=[]
for i in range(0,len(marksize_legend)):
    dot=ax.scatter(-1,-1,color='k',marker='o',s=factor_markersize*marksize_legend[i])
    art_list.append(dot)
    label_list.append(str('%.1f'% marksize_legend[i]))
leg2=ax.legend(art_list,label_list,ncol=5,columnspacing=0,handletextpad=0.1,frameon=False,bbox_to_anchor=(0.5,0))
# ---------------
ax.yaxis.set_ticks(y)
ax.yaxis.set_ticklabels(names)
ax.xaxis.set_ticks(x)
ax.xaxis.set_ticks_position("top")
ax.xaxis.set_ticklabels(cells,ha='left',rotation=45)
ax.set_xlim(0.5,max(x)+0.5)
ax.set_ylim(max(y)+0.5,0.5)
# ax_legend.set_xlim(0.5,max(x)+0.5)
# ax_legend.set_ylim(0,1)
ax.yaxis.label.set_color('black')
ax.xaxis.label.set_color('black')
# 取消坐标轴但保留label
ax.tick_params(axis=u'both', which=u'both',length=0)
ax.spines['top'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()

fname_fig='Lecture3_3_example2.pdf'
plt.savefig(fname_fig)

plt.savefig('sciviz-seaborn-stats_preview_4.png', bbox_inches='tight', dpi=110)
plt.close('all')