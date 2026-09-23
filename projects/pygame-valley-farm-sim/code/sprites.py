#! /usr/bin/python3
# coding=utf-8

from random import randint, choice
import pygame
from settings import *
from timer import Timer


class Generic(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups, z=LAYERS['main']):
        # 调用父类 pygame.sprite.Sprite 的构造函数，将精灵添加到指定的精灵组中
        super().__init__(groups)

        # 设置精灵的图像surface
        self.image = surf

        # 获取图像的矩形区域，并设置其左上角位置
        self.rect = self.image.get_rect(topleft=pos)

        # 设置精灵的图层深度，默认为主图层
        self.z = z

        self.hitbox = self.rect.copy().inflate(-self.rect.width * 0.2, -self.rect.height * 0.75)


class Interaction(Generic):
    def __init__(self, pos, size, groups, name):
        surf = pygame.Surface(size)
        super().__init__(pos, surf, groups)
        self.name = name


class Water(Generic):
    def __init__(self, pos, frames, groups):
        # 设置动画帧列表和当前帧索引
        self.frames = frames
        self.frame_index = 0

        # 调用父类构造函数，设置精灵的基本属性
        super().__init__(
            pos=pos,
            surf=self.frames[self.frame_index],
            groups=groups,
            z=LAYERS['water'])

    def animate(self, dt):
        # 更新帧索引，实现动画效果
        self.frame_index += 5 * dt
        # 当帧索引超出范围时重置为0
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        # 更新当前显示的图像
        self.image = self.frames[int(self.frame_index)]

    def update(self, dt):
        # 每帧更新时调用动画方法
        self.animate(dt)


class WildFlower(Generic):
    def __init__(self, pos, surf, groups):
        # 初始化野花精灵，继承自Generic类
        super().__init__(pos, surf, groups)
        self.hitbox = self.rect.copy().inflate(-20, -self.rect.height * 0.9)


class Particle(Generic):
    def __init__(self, pos, surf, groups, z, duration=200):
        super().__init__(pos, surf, groups, z)
        # 记录粒子创建的时间戳
        self.start_time = pygame.time.get_ticks()
        # 设置粒子的持续时间(毫秒)
        self.duration = duration

        # 创建粒子的白色轮廓效果
        # 从原始图像创建遮罩
        mask_surf = pygame.mask.from_surface(self.image)
        # 将遮罩转换为新的surface
        new_surf = mask_surf.to_surface()
        # 设置黑色为透明色
        new_surf.set_colorkey((0, 0, 0))
        # 使用新的surface替换原图像
        self.image = new_surf

    def update(self, dt):
        # 获取当前时间戳
        current_time = pygame.time.get_ticks()
        # 如果粒子存在时间超过持续时间则销毁
        if current_time - self.start_time > self.duration:
            self.kill()


class Tree(Generic):
    def __init__(self, pos, surf, groups, name, player_add):
        # 初始化树木精灵，继承自 Generic 类
        super().__init__(pos, surf, groups)

        self.health = 5  # 树木生命值
        self.alive = True  # 树木存活状态

        # 根据树木大小加载对应的树桩图像
        # 根据树木大小选择对应的树桩图片路径
        stump_size = "small" if name == "Small" else "medium"
        stump_path = f'../graphics/objects/stump_{stump_size}.png'
        # 加载并转换树桩图片,提高性能
        self.stump_surf = pygame.image.load(stump_path).convert_alpha()
        self.invul_timer = Timer(200)  # 无敌时间计时器

        # 苹果相关属性
        self.apple_surf = pygame.image.load('../graphics/fruit/apple.png')  # 加载苹果图像
        self.apple_pos = APPLE_POS[name]  # 获取苹果位置列表
        self.apple_sprites = pygame.sprite.Group()  # 创建苹果精灵组
        self.create_fruit()  # 初始化时创建苹果

        self.player_add = player_add

    def damage(self):
        # 对树木造成伤害,减少生命值
        self.health -= 1

        # 随机移除一个苹果
        if len(self.apple_sprites.sprites()) > 0:
            random_apple = choice(self.apple_sprites.sprites())
            Particle(
                pos=random_apple.rect.topleft,
                surf=random_apple.image,
                groups=self.groups()[0],
                z=LAYERS['fruit'])
            self.player_add('apple')
            random_apple.kill()

    def check_death(self):
        # 检查树木是否死亡
        if self.health <= 0:
            Particle(self.rect.topleft, self.image, self.groups()[0], LAYERS['fruit'], 300)
            # 树木死亡后变为树桩
            self.image = self.stump_surf
            self.rect = self.image.get_rect(midbottom=self.rect.midbottom)
            self.hitbox = self.rect.copy().inflate(-10, -self.rect.height * 0.6)
            self.alive = False
            self.player_add('wood')

    def update(self, dt):
        # 每帧更新时检查树木状态
        if self.alive:
            self.check_death()

    def create_fruit(self):
        # 在指定位置随机生成苹果
        for pos in self.apple_pos:
            if randint(0, 10) < 8:  # 约73%的概率生成苹果(randint(0,10) 取 0~7)
                # 计算苹果的绝对位置
                x = pos[0] + self.rect.left
                y = pos[1] + self.rect.top
                # 创建苹果精灵
                Generic(
                    pos=(x, y),
                    surf=self.apple_surf,
                    groups=[self.apple_sprites, self.groups()[0]],
                    z=LAYERS['fruit']
                )
