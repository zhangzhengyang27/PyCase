#! /usr/bin/python3
# coding=utf-8

from pathlib import Path

import pygame


def import_folder(path):
    """
    从指定路径递归导入所有图片文件并转换为 pygame surface 列表
    参数:path: 图片文件夹路径
    返回:surface_list: 包含所有已加载图片的 surface 列表
    """
    surface_list = []

    # 遍历指定路径下的所有图片文件(含子目录),按路径排序保证加载顺序稳定
    for image_path in sorted(Path(path).rglob('*.png')):
        # 加载图片并转换为带透明通道的 surface
        image_surf = pygame.image.load(str(image_path)).convert_alpha()
        # 将加载的图片 surface 添加到列表中
        surface_list.append(image_surf)

    return surface_list


def import_folder_dict(path):
    """
    从指定路径递归导入所有图片文件并转换为 pygame surface 字典
    参数:path: 图片文件夹路径
    返回:surface_dict: 以文件名(不含扩展名)为键,surface为值的字典
    """
    surface_dict = {}

    # 遍历指定路径下的所有图片文件(含子目录),按路径排序保证加载顺序稳定
    for image_path in sorted(Path(path).rglob('*.png')):
        # 加载图片并转换为带透明通道的 surface
        image_surf = pygame.image.load(str(image_path)).convert_alpha()
        # 以文件名(不含扩展名)为键,存储对应的surface
        surface_dict[image_path.stem] = image_surf

    return surface_dict
