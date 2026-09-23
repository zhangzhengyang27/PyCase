from random import randint

import pygame
from settings import *
from player import Player
from overlay import Overlay
from sprites import Generic, Water, Tree, WildFlower, Interaction
from pytmx.util_pygame import load_pygame

from support import import_folder
from sky import Rain
from soil import SoilLayer
from transition import Transition

# 调试模式:为 True 时绘制玩家的碰撞矩形与工具目标点
DEBUG = False


class Level:
    def __init__(self):
        # 获取显示对象
        self.player = None
        self.display_surface = pygame.display.get_surface()

        # 创建精灵组用于管理所有游戏精灵
        self.all_sprites = CameraGroup()
        self.collision_sprites = pygame.sprite.Group()  # 碰撞精灵组
        self.tree_sprites = pygame.sprite.Group()  # 树木精灵组
        self.interaction_sprites = pygame.sprite.Group()  # 交互精灵组

        self.soil_layer = SoilLayer(self.all_sprites, self.collision_sprites)
        self.setup()
        self.overlay = Overlay(self.player)
        self.transition = Transition(self.reset, self.player)

        # 雨天
        self.rain = Rain(self.all_sprites)
        self.raining = randint(0, 10) > 3
        self.soil_layer.raining = self.raining

    def setup(self):
        tmx_data = load_pygame('../data/map.tmx')

        # 加载地图,并创建精灵组用于管理所有游戏精灵
        for layer in ['HouseFloor', 'HouseFurnitureBottom']:
            for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
                Generic((x * TILE_SIZE, y * TILE_SIZE), surf, self.all_sprites, LAYERS['house bottom'])

        for layer in ['HouseWalls', 'HouseFurnitureTop']:
            for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
                Generic((x * TILE_SIZE, y * TILE_SIZE), surf, self.all_sprites)

        # 添加栅栏
        for x, y, surf in tmx_data.get_layer_by_name('Fence').tiles():
            Generic((x * TILE_SIZE, y * TILE_SIZE), surf, [self.all_sprites, self.collision_sprites])

        # 添加水
        water_frames = import_folder('../graphics/water')
        for x, y, surf in tmx_data.get_layer_by_name('Water').tiles():
            Water((x * TILE_SIZE, y * TILE_SIZE), water_frames, self.all_sprites)

        # 添加树木
        for obj in tmx_data.get_layer_by_name('Trees'):
            Tree(
                pos=(obj.x, obj.y),
                surf=obj.image,
                groups=[self.all_sprites, self.collision_sprites, self.tree_sprites],
                name=obj.name,
                player_add=self.player_add)

        # 添加装饰物
        for obj in tmx_data.get_layer_by_name('Decoration'):
            WildFlower((obj.x, obj.y), obj.image, [self.all_sprites, self.collision_sprites])

        # 添加碰撞精灵
        for x, y, surf in tmx_data.get_layer_by_name('Collision').tiles():
            Generic((x * TILE_SIZE, y * TILE_SIZE), pygame.Surface((TILE_SIZE, TILE_SIZE)), self.collision_sprites)

        # 创建玩家
        for obj in tmx_data.get_layer_by_name('Player'):
            if obj.name == 'Start':
                self.player = Player(
                    pos=(obj.x, obj.y),
                    group=self.all_sprites,
                    collision_sprites=self.collision_sprites,
                    tree_sprites=self.tree_sprites,
                    interaction=self.interaction_sprites,
                    soil_layer=self.soil_layer
                )

            if obj.name == 'Bed':
                Interaction((obj.x, obj.y), (obj.width, obj.height), self.interaction_sprites, obj.name)

        Generic(
            pos=(0, 0),
            surf=pygame.image.load('../graphics/world/ground.png').convert_alpha(),
            groups=self.all_sprites,
            z=LAYERS['ground'])

    def player_add(self, item):
        self.player.item_inventory[item] += 1

    def reset(self):
        # plants
        self.soil_layer.update_plants()

        # soil
        self.soil_layer.remove_water()
        self.raining = randint(0, 10) > 3
        self.soil_layer.raining = self.raining
        if self.raining:
            self.soil_layer.water_all()

        # apples on the trees
        for tree in self.tree_sprites.sprites():
            for apple in tree.apple_sprites.sprites():
                apple.kill()
            tree.create_fruit()

    def run(self, dt):
        self.display_surface.fill('black')  # 使用黑色填充显示表面
        self.all_sprites.custom_draw(self.player)  # 在显示表面上绘制玩家
        self.all_sprites.update(dt)  # 更新所有精灵的状态
        self.overlay.display()  # 显示工具和种子

        # 雨天
        if self.raining:
            self.rain.update()

        if self.player.sleep:
            self.transition.play()


class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()  # 获取显示对象
        self.offset = pygame.math.Vector2()  # 偏移量

    def custom_draw(self, player):
        # 计算相机偏移量,使玩家保持在屏幕中心
        # 偏移量x = 玩家中心x坐标 - 屏幕宽度/2
        # 偏移量y = 玩家中心y坐标 - 屏幕高度/2
        self.offset.x = player.rect.centerx - SCREEN_WIDTH / 2
        self.offset.y = player.rect.centery - SCREEN_HEIGHT / 2

        # 按图层 z 将所有精灵分组(一次遍历),替代逐图层对全部精灵排序的做法
        layer_sprites = {}
        for sprite in self.sprites():
            layer_sprites.setdefault(sprite.z, []).append(sprite)

        # 按图层顺序绘制所有精灵
        for layer in LAYERS.values():
            # 遍历当前图层中的所有精灵,图层内部按 y 坐标排序
            for sprite in sorted(layer_sprites.get(layer, []), key=lambda sprite: sprite.rect.centery):
                # 复制精灵的矩形区域
                offset_rect = sprite.rect.copy()
                # 根据相机偏移量调整精灵位置
                offset_rect.center -= self.offset
                # 将精灵图像绘制到显示表面
                self.display_surface.blit(sprite.image, offset_rect)

                # 调试模式下绘制玩家的碰撞矩形与工具目标点
                if DEBUG and sprite == player:
                    pygame.draw.rect(self.display_surface, 'red', offset_rect, 5)
                    hitbox_rect = player.hitbox.copy()
                    hitbox_rect.center = offset_rect.center
                    pygame.draw.rect(self.display_surface, 'green', hitbox_rect, 5)
                    target_pos = offset_rect.center + PLAYER_TOOL_OFFSET[player.status.split('_')[0]]
                    pygame.draw.circle(self.display_surface, 'blue', target_pos, 5)
