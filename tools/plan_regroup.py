#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""规划：将扁平化的章节按主题分组到子目录，子目录内连续编号 NN-标题.py。
仅打印计划，不实际移动。"""
import os, re

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "python-basics")

CHAPTERS = {
    "04-字符串&列表&元祖": {
        "字符串": ["认识字符串","字符串的输出","字符串的输入","下标","切片","体验切片","字符串之查找","字符串之修改","字符串之非重点","字符串之判断","判断是否存在"],
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
        "函数基础": ["体验函数","函数的注意事项","多函数执行流程","函数的嵌套调用","函数嵌套调用应用"],
        "参数": ["函数的参数","位置参数","关键字参数","缺省参数","不定长参数"],
        "返回值": ["返回值","return的特点","返回值作为参数传递","函数的返回值"],
        "变量作用域": ["局部变量","访问全局变量","修改全局变量","引用","了解引用"],
        "说明文档": ["说明文档"],
        "拆包": ["拆包"],
    },
    "07-函数进阶": {
        "递归": ["递归"],
        "lambda": ["lambda","带判断的lambda","列表数据排序"],
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
        "其他": ["类方法","静态方法","拓展_mro","class_test","demo1","zodiac_v3","func_test"],
    },
}

def match_group(filename, keywords):
    name = filename.lower()
    stem = re.sub(r"^hm_\d+_", "", os.path.splitext(filename)[0]).lower()
    for kw in keywords:
        if kw.lower() in name or kw.lower() in stem:
            return True
    return False

for ch, groups in CHAPTERS.items():
    chdir = os.path.join(BASE, ch)
    files = [f for f in os.listdir(chdir) if f.endswith(".py")]
    print(f"\n########## {ch} ({len(files)} 个)")
    assigned = set()
    for gname, kws in groups.items():
        picked = [f for f in files if match_group(f, kws) and f not in assigned]
        for f in picked:
            assigned.add(f)
        print(f"  [{gname}] ({len(picked)}):")
        for f in picked:
            print(f"    - {f}")
    unassigned = [f for f in files if f not in assigned]
    if unassigned:
        print(f"  [未归类] ({len(unassigned)}):")
        for f in unassigned:
            print(f"    - {f}")
