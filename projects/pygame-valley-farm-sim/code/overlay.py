#! /usr/bin/python3
# coding=utf-8

import pygame
from settings import *


class Overlay:
    def __init__(self, player):
        # general setup
        self.display_surface = pygame.display.get_surface()  # 获取显示对象
        self.player = player

        overlay_path = '../graphics/overlay/'  # overlay 图片路径

        # 加载工具图片
        self.tools_surf = {}
        for tool in player.tools:
            tool_image = pygame.image.load(f'{overlay_path}{tool}.png')
            self.tools_surf[tool] = tool_image.convert_alpha()

        # 加载种子图片
        self.seeds_surf = {}
        for seed in player.seeds:
            seed_image = pygame.image.load(f'{overlay_path}{seed}.png')
            self.seeds_surf[seed] = seed_image.convert_alpha()

    def display(self):
        # tool
        tool_surf = self.tools_surf[self.player.selected_tool]  # 获取工具图片
        tool_rect = tool_surf.get_rect(midbottom=OVERLAY_POSITIONS['tool'])  # 获取工具图片位置
        self.display_surface.blit(tool_surf, tool_rect)  # 在显示表面上绘制工具图片

        # seeds
        seed_surf = self.seeds_surf[self.player.selected_seed]  # 获取种子图片
        seed_rect = seed_surf.get_rect(midbottom=OVERLAY_POSITIONS['seed'])  # 获取种子图片位置
        self.display_surface.blit(seed_surf, seed_rect)  # 在显示表面上绘制种子图片
