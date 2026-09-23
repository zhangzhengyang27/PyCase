#! /usr/bin/python3
# coding=utf-8

import pygame
from settings import *


class Transition:
    def __init__(self, reset, player):
        # 初始化过渡效果

        self.display_surface = pygame.display.get_surface()  # 获取游戏显示表面
        self.reset = reset  # 重置函数引用
        self.player = player  # 玩家对象引用

        # 创建覆盖图层
        # 创建一个与屏幕大小相同的表面
        self.image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.color = 255  # 初始颜色值(用于淡入淡出效果)
        self.speed = -2  # 颜色变化速度

    def play(self):
        # 更新过渡效果
        # 改变颜色值
        self.color += self.speed

        # 当颜色值降至0时(完全黑屏)
        if self.color <= 0:
            # 反转速度方向(开始淡入)
            self.speed *= -1
            self.color = 0
            # 触发重置
            self.reset()

        # 当颜色值超过255时(完全显示)
        if self.color > 255:
            self.color = 255
            # 结束玩家睡眠状态
            self.player.sleep = False
            # 重置速度为负值(为下次淡出做准备)
            self.speed = -2

        # 使用当前颜色值填充覆盖层
        self.image.fill((self.color, self.color, self.color))
        # 使用混合模式将覆盖层绘制到显示表面
        self.display_surface.blit(self.image, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
