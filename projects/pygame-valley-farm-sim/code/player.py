#! /usr/bin/python3
# coding=utf-8

import pygame
from settings import *
from support import import_folder
from timer import Timer


class Player(pygame.sprite.Sprite):
    def __init__(self, pos, group, collision_sprites, tree_sprites, interaction, soil_layer):
        super().__init__(group)

        # 基础设置
        self.target_pos = None
        self.animations = None

        # 导入动画资源
        self.import_assets()
        self.status = 'left_water'  # 初始状态
        self.frame_index = 0  # 当前帧

        self.image = self.animations[self.status][self.frame_index]
        self.rect = self.image.get_rect(center=pos)  # 获取图像的矩形区域并设置中心位置
        self.z = LAYERS['main']  # 层级

        # 移动属性
        self.direction = pygame.math.Vector2()  # 移动方向向量,默认值 (0, 0)
        self.pos = pygame.math.Vector2(self.rect.center)  # 精确位置向量
        self.speed = 200  # 移动速度

        # 碰撞检测
        self.hitbox = self.rect.copy().inflate((-126, -70))
        self.collision_sprites = collision_sprites

        # timers
        self.timers = {
            'tool use': Timer(350, self.use_tool),
            'tool switch': Timer(200),
            'seed use': Timer(350, self.use_seed),
            'seed switch': Timer(200),
        }

        # 工具
        self.tools = ['hoe', 'axe', 'water']  # 工具列表
        self.tool_index = 0  # 默认工具索引
        self.selected_tool = self.tools[self.tool_index]  # 默认工具

        # 种子
        self.seeds = ['corn', 'tomato']  # 种子列表
        self.seed_index = 0  # 默认种子索引
        self.selected_seed = self.seeds[self.seed_index]  # 默认种子

        # 库存
        self.item_inventory = {
            'wood': 0,
            'apple': 0,
            'corn': 0,
            'tomato': 0
        }

        # 树木
        self.tree_sprites = tree_sprites
        self.interaction = interaction
        self.sleep = False
        self.soil_layer = soil_layer

    def use_tool(self):
        # 如果选择了锄头工具
        if self.selected_tool == 'hoe':
            self.soil_layer.get_hit(self.target_pos)

        # 如果选择了斧头工具
        if self.selected_tool == 'axe':
            # 遍历所有树木精灵
            for tree in self.tree_sprites.sprites():
                # 检查树木是否在目标位置
                if tree.rect.collidepoint(self.target_pos):
                    tree.damage()

        # 如果选择了浇水工具
        if self.selected_tool == 'water':
            self.soil_layer.water(self.target_pos)

    def get_target_pos(self):
        # 计算工具使用的目标位置，通过当前状态获取方向,并加上对应方向的偏移量
        self.target_pos = self.rect.center + PLAYER_TOOL_OFFSET[self.status.split('_')[0]]

    def use_seed(self):
        self.soil_layer.plant_seed(self.target_pos, self.selected_seed)

    def import_assets(self):
        self.animations = {'up': [], 'down': [], 'left': [], 'right': [],
                           'right_idle': [], 'left_idle': [], 'up_idle': [], 'down_idle': [],
                           'right_hoe': [], 'left_hoe': [], 'up_hoe': [], 'down_hoe': [],
                           'right_axe': [], 'left_axe': [], 'up_axe': [], 'down_axe': [],
                           'right_water': [], 'left_water': [], 'up_water': [], 'down_water': []}

        for animation in self.animations.keys():
            full_path = '../graphics/character/' + animation
            self.animations[animation] = import_folder(full_path)

    def animate(self, dt):
        self.frame_index += 4 * dt
        if self.frame_index >= len(self.animations[self.status]):
            self.frame_index = 0

        self.image = self.animations[self.status][int(self.frame_index)]

    def input(self):
        keys = pygame.key.get_pressed()  # 获取键盘输入

        if not self.timers['tool use'].active and not self.sleep:
            # 垂直方向移动
            if keys[pygame.K_UP]:
                self.direction.y = -1  # 向上移动
                self.status = 'up'
            elif keys[pygame.K_DOWN]:
                self.direction.y = 1  # 向下移动
                self.status = 'down'
            else:
                self.direction.y = 0  # 垂直方向停止

            # 水平方向移动
            if keys[pygame.K_RIGHT]:
                self.direction.x = 1  # 向右移动
                self.status = 'right'
            elif keys[pygame.K_LEFT]:
                self.direction.x = -1  # 向左移动
                self.status = 'left'
            else:
                self.direction.x = 0  # 水平方向停止

            # 使用工具
            if keys[pygame.K_SPACE]:
                self.timers['tool use'].activate()  # 激活计时器
                self.direction = pygame.math.Vector2()  # 停止移动
                self.frame_index = 0  # 重置帧

            # 如果用户按下了 "Q" 键，并且 'tool switch' 计时器没有激活
            if keys[pygame.K_q] and not self.timers['tool switch'].active:
                self.timers['tool switch'].activate()
                self.tool_index += 1  # 切换工具
                self.tool_index = self.tool_index if self.tool_index < len(self.tools) else 0
                self.selected_tool = self.tools[self.tool_index]

            # 使用种子
            if keys[pygame.K_LCTRL]:
                self.timers['seed use'].activate()  # 激活计时器
                self.direction = pygame.math.Vector2()  # 停止移动
                self.frame_index = 0  # 重置帧

            # 如果用户按下了 "E" 键，并且 'seed switch' 计时器没有激活
            if keys[pygame.K_e] and not self.timers['seed switch'].active:
                self.timers['seed switch'].activate()
                self.seed_index += 1
                self.seed_index = self.seed_index if self.seed_index < len(self.seeds) else 0
                self.selected_seed = self.seeds[self.seed_index]

            # 如果按下回车键
            if keys[pygame.K_RETURN]:
                # 检测玩家是否与交互物体发生碰撞
                collided_interaction_sprite = pygame.sprite.spritecollide(self, self.interaction, False)
                if collided_interaction_sprite:
                    # 如果碰撞的是商人
                    if collided_interaction_sprite[0].name == 'Trader':
                        pass
                    # 如果碰撞的是其他物体(比如床)
                    else:
                        self.status = 'left_idle'  # 设置玩家状态为左侧静止
                        self.sleep = True  # 设置睡眠状态为 True

    def get_status(self):
        # idle
        if self.direction.magnitude() == 0:
            self.status = self.status.split('_')[0] + '_idle'

        # tool use
        if self.timers['tool use'].active:
            self.status = self.status.split('_')[0] + '_' + self.selected_tool

    def update_timers(self):
        for timer in self.timers.values():
            timer.update()

    def collision(self, direction):
        # 遍历所有碰撞精灵
        for sprite in self.collision_sprites.sprites():
            # 检查精灵是否有碰撞盒属性
            if hasattr(sprite, 'hitbox'):
                # 如果发生碰撞
                if sprite.hitbox.colliderect(self.hitbox):
                    # 处理水平方向的碰撞
                    if direction == 'horizontal':
                        if self.direction.x > 0:  # 向右移动时
                            self.hitbox.right = sprite.hitbox.left  # 将玩家碰撞盒右边界设为障碍物左边界
                        if self.direction.x < 0:  # 向左移动时
                            self.hitbox.left = sprite.hitbox.right  # 将玩家碰撞盒左边界设为障碍物右边界
                        self.rect.centerx = self.hitbox.centerx  # 更新精灵图像位置
                        self.pos.x = self.hitbox.centerx  # 更新精确位置

                    # 处理垂直方向的碰撞
                    if direction == 'vertical':
                        if self.direction.y > 0:  # 向下移动时
                            self.hitbox.bottom = sprite.hitbox.top  # 将玩家碰撞盒底部设为障碍物顶部
                        if self.direction.y < 0:  # 向上移动时
                            self.hitbox.top = sprite.hitbox.bottom  # 将玩家碰撞盒顶部设为障碍物底部
                        self.rect.centery = self.hitbox.centery  # 更新精灵图像位置
                        self.pos.y = self.hitbox.centery  # 更新精确位置

    def move(self, dt):
        # self.direction.magnitude() 作用是计算对象 self.direction 的方向向量的模
        # 标准化向量（确保对角线移动速度不会更快）.如果同时向两个方向移动，速度会更快约 1.4 （勾股定理）
        if self.direction.magnitude() > 0:
            self.direction = self.direction.normalize()

        # 水平移动
        self.pos.x += self.direction.x * self.speed * dt  # 更新x坐标
        self.hitbox.centerx = round(self.pos.x)  # 更新碰撞检测的x位置
        self.rect.centerx = self.pos.x  # 更新精灵的x位置
        self.collision('horizontal')

        # 垂直移动
        self.pos.y += self.direction.y * self.speed * dt  # 更新y坐标
        self.hitbox.centery = round(self.pos.y)  # 更新碰撞检测的y位置
        self.rect.centery = self.pos.y  # 更新精灵的y位置
        self.collision('vertical')

    def update(self, dt):
        self.input()  # 处理输入
        self.get_status()  # 获取状态
        self.update_timers()  # 更新计时器
        self.get_target_pos()  # 获取目标位置

        self.move(dt)  # 更新位置
        self.animate(dt)  # 更新动画
