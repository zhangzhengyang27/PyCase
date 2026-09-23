#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将扁平化章节按主题分组到子目录，子目录内连续编号 NN-标题.py。
用法：python3 regroup.py [--dry]"""
import os, re, sys

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "python-basics")
DRY = "--dry" in sys.argv

# 章节 -> {子目录: [关键词列表]} 以及每个文件归类依据：保留原标题(去掉 hm_NN_ 前缀)
CHAPTERS = {
    "04-字符串&列表&元祖": {
        "字符串": ["认识字符串","字符串的输出","字符串的输入","下标","切片","体验切片","字符串之查找","字符串之修改","字符串之非重点","字符串之判断","判断是否存在","查找"],
        "列表": ["列表增加数据","列表删除数据","列表修改数据","列表复制数据","列表的循环遍历","列表嵌套","随机分配办公室"],
        "元组": ["体验元组","定义元组","元组常见操作","元组数据的修改操作"],
    },
    "05-代码": {
        "字典": ["字典","提取字典","合并列表为字典"],
        "集合": ["集合"],
        "公共操作": ["公共操作","公共方法"],
        "推导式": ["列表推导式","字典推导式","集合推导式","带if的列表推导式","多个for实现列表推导式","数据类型的转换"],
    },
    "06-函数": {
        "函数基础": ["体验函数","函数的注意事项","多函数执行流程","函数的嵌套调用","函数嵌套调用应用","体验函数的返回值"],
        "参数": ["函数的参数","位置参数","关键字参数","缺省参数","不定长参数"],
        "返回值": ["返回值","return的特点","返回值作为参数传递","函数返回值的应用","函数的返回值"],
        "变量作用域": ["局部变量","访问全局变量","修改全局变量","引用","了解引用","交换变量的值"],
        "其他": ["func_test","zodiac_v3"],
    },
    "07-函数进阶": {
        "递归": ["递归"],
        "lambda": ["lambda","列表数据排序"],
        "高阶函数": ["高阶函数","abs和round","map","reduce","filter"],
    },
    "09-面向对象": {
        "类基础": ["体验面向对象","类里面的self","一个类创建多个对象","类外面添加和获取对象属性","类里面获取对象属性"],
        "类属性": ["设置和访问类属性","修改类属性"],
        "继承": ["体验继承","单继承","多继承","多层继承","子类重写父类","子类调用父类","super方法"],
        "属性权限": ["私有权限","获取和修改私有属性"],
        "魔法方法": ["魔法方法init","带参数的init","str","del"],
        "多态": ["多态"],
        "综合案例": ["烤地瓜","搬家具"],
        "其他": ["class_test","demo1","类方法","静态方法","拓展_mro"],
    },
}

def classify(filename, kws):
    name = filename.lower()
    stem = re.sub(r"^hm_\d+_", "", os.path.splitext(filename)[0]).lower()
    for kw in kws:
        if kw.lower() in name or kw.lower() in stem:
            return True
    return False

def new_title(filename):
    # 去掉 hm_NN_ 前缀，保留中文标题
    stem = os.path.splitext(filename)[0]
    title = re.sub(r"^hm_\d+_", "", stem)
    return title

total = 0
for ch, groups in CHAPTERS.items():
    chdir = os.path.join(BASE, ch)
    files = [f for f in os.listdir(chdir) if f.endswith(".py")]
    assigned = set()
    for gname, kws in groups.items():
        picked = [f for f in files if classify(f, kws) and f not in assigned]
        picked.sort(key=lambda x: os.path.splitext(x)[0])
        for i, f in enumerate(picked, 1):
            assigned.add(f)
            title = new_title(f)
            newname = f"{i:02d}-{title}.py"
            dest = os.path.join(chdir, gname, newname)
            total += 1
            print(f"[{'DRY' if DRY else 'MV'}] {ch}/{f} -> {gname}/{newname}")
            if not DRY:
                os.makedirs(os.path.join(chdir, gname), exist_ok=True)
                if os.path.exists(dest):
                    print(f"[冲突] 目标已存在，跳过: {ch}/{gname}/{newname}")
                    continue
                os.rename(os.path.join(chdir, f), dest)
    unassigned = [f for f in files if f not in assigned]
    if unassigned:
        print(f"[警告] {ch} 未归类: {unassigned}")
print(f"\n{'[DRY] ' if DRY else ''}共 {total} 个文件待移动。")
