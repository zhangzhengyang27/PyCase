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

# Create the wordcloud object
figwidth,figheight=900,600
wc = WordCloud(width=figwidth, height=figheight, margin=0,colormap='Dark2',font_path='Arial').generate(text)

# Display the generated image:
plt.imshow(wc, interpolation='bilinear')
plt.axis("off")
plt.margins(x=0, y=0)

fname_fig='Lecture3_8_basic1.pdf'
plt.savefig(fname_fig)

plt.savefig('sciviz-wordcloud_preview.png', bbox_inches='tight', dpi=110)
plt.close('all')

def plotWordCloud(wc,dpi=100,ratio=1.39,bkcolor='w'):
    array_wc=wc.to_array()
    figwidth,figheight=array_wc.shape[1],array_wc.shape[0]
    # 3. 绘制词云图
    ratio_fontsize=ratio/(dpi/100)
    fig=plt.figure(figsize=(figwidth/dpi,figheight/dpi),dpi=dpi,facecolor=bkcolor) #******划重点
    ax=plt.gca()
    ax.axis('scaled')
    ax.set_xlim(0,figwidth)
    ax.set_ylim(0,figheight)
    ax.invert_yaxis()
    plt.subplots_adjust(left=0,right=1,top=1,bottom=0)
    # 4. 根据词云图数据中的文字坐标、字体大小、颜色和旋转角度绘制文字
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
        ax.text(y,x,text0,fontsize=fontsize/ratio_fontsize,rotation=angle,va='top',ha='left',color=color)

    ax.set_facecolor('w')
    return ax

# 1. 字体
fontpath='Arial'
fontprop=mpl.font_manager.FontProperties(fname=fontpath)
# 2. 生成词云图数据
text=("Python Python Matplotlib Matplotlib Seaborn Network Plot Violin Chart Pandas Datascience Wordcloud Spider Radar Parrallel Alpha Color Brewer Density Scatter Barplot Barplot Boxplot Violinplot Treemap Stacked Area Chart Chart Visualization Dataviz Donut Pie Time-Series Wordcloud Wordcloud Sankey Bubble")
figwidth,figheight=600,600
wc = WordCloud(width=figwidth, height=figheight, margin=0,colormap='Dark2',font_path=fontpath).generate(text)
# 3. 绘制词云图
ax=plotWordCloud(wc,bkcolor='k')
ax.axis('off')

fname_fig='Lecture3_8_basic1.pdf'
plt.savefig(fname_fig)
plt.savefig('sciviz-wordcloud_preview_2.png', bbox_inches='tight', dpi=110)
plt.close('all')

wc.to_file('Lecture3_8_basic1.png')

text = open(os.path.join(d, 'Data/wordcloud/alice.txt')).read()
alice_mask = np.array(Image.open("Data/wordcloud/alice_mask.png"))
# 1. 字体
fontpath='Arial'
fontprop=mpl.font_manager.FontProperties(fname=fontpath)
# 2. 生成词云图数据
figwidth,figheight=wc.to_array().shape[0],wc.to_array().shape[1]
wc = WordCloud(margin=0,background_color="white", max_words=2000, mask=alice_mask,colormap='jet',
               font_path=fontpath).generate(text)

# 3. 绘制词云图
ax=plotWordCloud(wc)
ax.axis('off')
fname_fig='Lecture3_8_example1.pdf'
plt.savefig(fname_fig)
plt.savefig('sciviz-wordcloud_preview_3.png', bbox_inches='tight', dpi=110)
plt.close('all')

plt.figure()
plt.imshow(wc)
# plt.axis("off")

plt.savefig('Lecture3_8_test.png',dpi=900)

# 读取文本
text = open('Data/wordcloud/Trump.txt', encoding="utf-8").read()
# 打开mask图像
parrot_color = np.array(Image.open("Data/wordcloud/parrot-by-jose-mari-gimenez2.jpg"))
# 重采样
parrot_color = parrot_color[::3, ::3]
# 白色部分是要mask的部分
parrot_mask = parrot_color.copy()
parrot_mask[parrot_mask.sum(axis=2) == 0] = 255
# 提取图片边界
edges = np.mean([gaussian_gradient_magnitude(parrot_color[:, :, i] / 255., 2) for i in range(3)], axis=0)
parrot_mask[edges > .08] = 255
# 创建词云图对象
wc = WordCloud(max_words=2000, mask=parrot_mask, max_font_size=40, random_state=42, relative_scaling=0,font_path=fontpath)
# 生成词云图数据
wc.generate(text)
# 读取图片，提取颜色并给词云图文本重新着色
image_colors = ImageColorGenerator(parrot_color)
wc.recolor(color_func=image_colors)

# 3. 绘制词云图矢量图
ax=plotWordCloud(wc,bkcolor='k')
ax.axis('off')
fname_fig='Lecture3_8_example2.pdf'
plt.savefig(fname_fig,facecolor='k')
plt.savefig('sciviz-wordcloud_preview_4.png', bbox_inches='tight', dpi=110)
plt.close('all')

wc.to_file(fname_fig.replace('.pdf','.png'))

import linecache
# 1. 处理文本：去掉注释，括号()[]和逗号用空格替换
textin='Data/wordcloud/code_chapter1_3.txt'
textout='Data/wordcloud/code_chapter1_3_text.txt'
fpout=open(textout,'w')
alldata=linecache.getlines(textfile)
linecache.clearcache()
replacedtext=['(',')','[',']',',','.','*',"'",'+','/','=','%',':','$','{','}','^','\\','<','>','==','"','-']
for i in range(0,len(alldata)):
    line_str=alldata[i].replace('\n','').split('#')[0]
    for s in replacedtext:
        line_str=line_str.replace(s,' ')
    if(not line_str==''):
        for word in line_str.split(' '):
            fpout.write('%s\n'%word)
fpout.close()

# 绘制词云图
# 读取文本
text = open(textout, encoding="utf-8").read()
# 打开mask图像
parrot_color = np.array(Image.open(os.path.join(d, "Data/wordcloud/Matplotlib.jpg")))
# 重采样
parrot_color = parrot_color[::3, ::3]
# 白色部分是要mask的部分
parrot_mask = parrot_color.copy()
parrot_mask[parrot_mask.sum(axis=2) == 0] = 255
# 提取图片边界
edges = np.mean([gaussian_gradient_magnitude(parrot_color[:, :, i] / 255., 2) for i in range(3)], axis=0)
parrot_mask[edges > .08] = 255
# 创建词云图对象
wc = WordCloud(max_words=2000, mask=parrot_mask, max_font_size=40, random_state=42, relative_scaling=0,font_path=fontpath)
# 生成词云图数据
wc.generate(text)
# 读取图片，提取颜色并给词云图文本重新着色
image_colors = ImageColorGenerator(parrot_color)
wc.recolor(color_func=image_colors)

# 3. 绘制词云图矢量图
ax=plotWordCloud(wc,bkcolor='w')
ax.axis('off')
fname_fig='Lecture3_8_practice1.pdf'
plt.savefig(fname_fig,facecolor='k')
plt.savefig('sciviz-wordcloud_preview_5.png', bbox_inches='tight', dpi=110)
plt.close('all')

wc.to_file(fname_fig.replace('.pdf','.png'))