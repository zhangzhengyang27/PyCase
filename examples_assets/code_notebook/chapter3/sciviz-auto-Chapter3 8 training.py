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
from wordcloud import WordCloud,ImageColorGenerator
from PIL import Image
from scipy.ndimage import gaussian_gradient_magnitude

# Create a list of word
text=("Python Python Python Matplotlib Matplotlib Seaborn Network Plot Violin Chart Pandas Datascience Wordcloud Spider Radar Parrallel Alpha Color Brewer Density Scatter Barplot Barplot Boxplot Violinplot Treemap Stacked Area Chart Chart Visualization Dataviz Donut Pie Time-Series Wordcloud Wordcloud Sankey Bubble")

wc = WordCloud(width=300,height=200,colormap='rainbow',font_path='Arial')
wc.generate(text)

plt.imshow(wc,interpolation='bilinear')
wc.to_file('test.png')
plt.savefig('sciviz-auto-Chapter3 8 training_preview.png', bbox_inches='tight', dpi=110)
plt.close('all')

def plotWordCloud(wc, dpi=100,ratio=1.39,bkcolor='w'):
    array_wc=wc.to_array()
    ratio_fontsize=ratio/(dpi/100)
    figwidth,figheight=array_wc.shape[1],array_wc.shape[0]
    fig=plt.figure(figsize=(figwidth/dpi, figheight/dpi),dpi=dpi,facecolor=bkcolor)
    ax=plt.gca()
    ax.axis('scaled')
    ax.set_xlim(0,figwidth)
    ax.set_ylim(0,figheight)
    ax.invert_yaxis()
    plt.subplots_adjust(left=0,top=1,right=1,bottom=0)
    
    for layout in wc.layout_:
        text0=layout[0][0]
        x,y=layout[2]
        fontsize=layout[1]
        angle=layout[3]
        if(angle==None):
            angle=0
        else:
            angle=90
        color=np.array(layout[4].split('(')[-1].split(')')[0].split(','),dtype=int)/255
        ax.text(y,x, text0, fontsize=fontsize/ratio_fontsize,va='top',ha='left',rotation=angle,color=color)
    return ax

ax=plotWordCloud(wc,bkcolor='w')
# ax.axis('off')
plt.savefig('test.pdf',facecolor='k')
plt.savefig('sciviz-auto-Chapter3 8 training_preview_2.png', bbox_inches='tight', dpi=110)
plt.close('all')

text=open('Data/wordcloud/alice.txt').read()
mask=np.array(Image.open('Data/wordcloud/alice_mask.png'))

wc=WordCloud(mask=mask, colormap='jet', max_words=2000, font_path='Arial')
wc.generate(text)

ax=plotWordCloud(wc,bkcolor='w')
ax.axis('off')

text=open('Data/wordcloud/Trump.txt').read()
mask_bird=np.array(Image.open('Data/wordcloud/parrot-by-jose-mari-gimenez2.jpg'))
mask_bird=mask_bird[::3, ::3]
mask=mask_bird.copy()
mask[mask_bird.sum(axis=2) == 0] = 255

wc=WordCloud(mask=mask, colormap='jet', max_words=2000, font_path='Arial')
wc.generate(text)

image_colors = ImageColorGenerator(mask_bird)
wc.recolor(color_func=image_colors)

ax=plotWordCloud(wc,bkcolor='k')
ax.axis('off')