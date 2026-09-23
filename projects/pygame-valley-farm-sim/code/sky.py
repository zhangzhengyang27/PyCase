#! /usr/bin/python3
# coding=utf-8

import pygame
from settings import *
from support import import_folder
from sprites import Generic
from random import randint, choice


class Drop(Generic):
    def __init__(self, surf, pos, moving, groups, z):
        # 基础设置
        super().__init__(pos, surf, groups, z)
        # 设置雨滴的生命周期(400-500毫秒)
        self.lifetime = randint(400, 500)
        # 记录雨滴创建的时间戳
        self.start_time = pygame.time.get_ticks()

        # 移动相关属性设置
        self.moving = moving
        if self.moving:
            # 如果是移动的雨滴，设置位置向量
            self.pos = pygame.math.Vector2(self.rect.topleft)
            # 设置移动方向向量(左上到右下)
            self.direction = pygame.math.Vector2(-2, 4)
            # 随机设置移动速度(200-250)
            self.speed = randint(200, 250)

    def update(self, dt):
        # 处理雨滴移动
        if self.moving:
            # 根据方向、速度和时间更新位置
            self.pos += self.direction * self.speed * dt
            # 将计算后的位置应用到雨滴图像
            self.rect.topleft = (round(self.pos.x), round(self.pos.y))

        # 生命周期检查
        if pygame.time.get_ticks() - self.start_time >= self.lifetime:
            # 超过生命周期则销毁雨滴
            self.kill()


class Rain:
    def __init__(self, all_sprites):
        # 初始化雨滴系统
        self.all_sprites = all_sprites
        # 加载雨滴和地面水花的图片资源
        self.rain_drops = import_folder('../graphics/rain/drops/')
        self.rain_floor = import_folder('../graphics/rain/floor/')
        # 获取地面图片的尺寸作为雨滴生成的范围
        self.floor_w, self.floor_h = pygame.image.load('../graphics/world/ground.png').get_size()

    def create_floor(self):
        # 在地面随机位置创建水花效果
        Drop(
            surf=choice(self.rain_floor),
            pos=(randint(0, self.floor_w), randint(0, self.floor_h)),
            moving=False,
            groups=self.all_sprites,
            z=LAYERS['rain floor'])

    def create_drops(self):
        # 在空中随机位置创建下落的雨滴
        Drop(
            surf=choice(self.rain_drops),
            pos=(randint(0, self.floor_w), randint(0, self.floor_h)),
            moving=True,
            groups=self.all_sprites,
            z=LAYERS['rain drops'])

    def update(self):
        # 每帧更新时同时创建雨滴和地面水花
        self.create_floor()
        self.create_drops()
