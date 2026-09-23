#! /usr/bin/python3
# coding=utf-8
from random import choice

import pygame
from settings import *
from pytmx.util_pygame import load_pygame
from support import *


class SoilTile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z = LAYERS['soil']


class WaterTile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z = LAYERS['soil water']


class Plant(pygame.sprite.Sprite):
    def __init__(self, plant_type, groups, soil, check_watered):
        super().__init__(groups)

        # 基础设置
        self.hitbox = None
        self.plant_type = plant_type  # 植物类型
        self.frames = import_folder(f'../graphics/fruit/{plant_type}')  # 加载植物生长阶段的图片帧
        self.soil = soil  # 关联的土壤对象
        self.check_watered = check_watered  # 检查是否浇水的函数

        # 植物生长相关属性
        self.age = 0  # 当前生长阶段
        self.max_age = len(self.frames) - 1  # 最大生长阶段
        self.grow_speed = GROW_SPEED[plant_type]  # 生长速度
        self.harvestable = False  # 是否可收获

        # 精灵设置
        self.image = self.frames[self.age]  # 当前显示的图片
        self.y_offset = -16 if plant_type == 'corn' else -8  # 玉米和其他植物的垂直偏移量不同
        self.rect = self.image.get_rect(midbottom=soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))  # 设置位置
        self.z = LAYERS['ground plant']  # 设置图层

    def grow(self):
        # 检查土地是否已浇水
        if self.check_watered(self.rect.center):
            self.age += self.grow_speed  # 增加生长阶段

            # 当植物开始生长(age>0)时
            if int(self.age) > 0:
                self.z = LAYERS['main']  # 更改图层
                self.hitbox = self.rect.copy().inflate(-26, -self.rect.height * 0.4)  # 创建碰撞盒

            # 检查是否达到最大生长阶段
            if self.age >= self.max_age:
                self.age = self.max_age
                self.harvestable = True  # 标记为可收获

            # 更新植物图像和位置
            self.image = self.frames[int(self.age)]
            self.rect = self.image.get_rect(midbottom=self.soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))


class SoilLayer:
    def __init__(self, all_sprites,collision_sprites):

        # sprite groups
        self.all_sprites = all_sprites
        self.collision_sprites = collision_sprites
        self.soil_sprites = pygame.sprite.Group()
        self.water_sprites = pygame.sprite.Group()
        self.plant_sprites = pygame.sprite.Group()

        # 天气状态(由 Level 在创建后注入实际值)
        self.raining = False

        # graphics
        self.soil_surf = pygame.image.load('../graphics/soil/o.png')
        self.soil_surfs = import_folder_dict('../graphics/soil/')
        self.water_surfs = import_folder('../graphics/soil_water')

        self.create_soil_grid()
        self.create_hit_rects()

    def create_soil_grid(self):
        ground = pygame.image.load('../graphics/world/ground.png')
        h_tiles, v_tiles = ground.get_width() // TILE_SIZE, ground.get_height() // TILE_SIZE

        # 使用列表推导式创建二维网格，每个格子初始化为空列表
        # h_tiles: 水平方向的瓦片数量
        # v_tiles: 垂直方向的瓦片数量
        self.grid = [[[] for _ in range(h_tiles)] for _ in range(v_tiles)]
        for x, y, _ in load_pygame('../data/map.tmx').get_layer_by_name('Farmable').tiles():
            self.grid[y][x].append('F')  # F: 可以耕种的

    def create_hit_rects(self):
        # 创建用于碰撞检测的矩形列表
        self.hit_rects = []

        # 遍历土壤网格的每个单元格
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                # 如果单元格包含'F'(可耕种标记)
                if 'F' in cell:
                    # 计算矩形的 x,y 坐标(以像素为单位)
                    x = index_col * TILE_SIZE
                    y = index_row * TILE_SIZE
                    # 创建一个与瓦片大小相同的碰撞矩形
                    rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                    # 将矩形添加到碰撞检测列表中
                    self.hit_rects.append(rect)

    def get_hit(self, point):
        # 遍历所有碰撞检测矩形
        for rect in self.hit_rects:
            # 检查点击位置是否在矩形内
            if rect.collidepoint(point):
                # 将像素坐标转换为网格坐标
                x = rect.x // TILE_SIZE  # 计算网格的x坐标
                y = rect.y // TILE_SIZE  # 计算网格的y坐标

                # 检查该网格是否可耕种('F')
                if 'F' in self.grid[y][x]:
                    self.grid[y][x].append('X')  # 将该网格标记为已耕种('X')
                    self.create_soil_tiles()  # 重新生成土壤瓦片精灵
                    if self.raining:
                        self.water_all()

    def water(self, target_pos):
        # 遍历所有土壤精灵
        for soil_sprite in self.soil_sprites.sprites():
            # 检查点击位置是否在土壤精灵范围内
            if soil_sprite.rect.collidepoint(target_pos):
                # 获取土壤精灵的网格坐标
                x = soil_sprite.rect.x // TILE_SIZE
                y = soil_sprite.rect.y // TILE_SIZE
                # 在网格中添加浇水标记'W'
                self.grid[y][x].append('W')

                # 在土壤精灵位置创建水精灵
                pos = soil_sprite.rect.topleft
                surf = choice(self.water_surfs)  # 随机选择一个水的表面贴图
                WaterTile(pos, surf, [self.all_sprites, self.water_sprites])

    def water_all(self):
        # 遍历整个网格
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                # 如果格子已耕种('X')但未浇水('W')
                if 'X' in cell and 'W' not in cell:
                    # 添加浇水标记
                    cell.append('W')
                    # 计算水精灵的像素坐标
                    x = index_col * TILE_SIZE
                    y = index_row * TILE_SIZE
                    # 创建水精灵
                    WaterTile((x, y), choice(self.water_surfs), [self.all_sprites, self.water_sprites])

    def remove_water(self):
        # 移除所有水精灵，遍历水精灵组中的所有精灵并销毁它们
        for sprite in self.water_sprites.sprites():
            sprite.kill()

        # 清理网格中的浇水标记，遍历整个网格,移除所有'W'(浇水)标记
        for row in self.grid:
            for cell in row:
                if 'W' in cell:
                    cell.remove('W')

    def check_watered(self, pos):
        x = pos[0] // TILE_SIZE
        y = pos[1] // TILE_SIZE
        cell = self.grid[y][x]
        is_watered = 'W' in cell
        return is_watered

    def plant_seed(self, target_pos, seed):
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(target_pos):

                x = soil_sprite.rect.x // TILE_SIZE
                y = soil_sprite.rect.y // TILE_SIZE

                if 'P' not in self.grid[y][x]:
                    self.grid[y][x].append('P')
                    Plant(seed, [self.all_sprites, self.plant_sprites, self.collision_sprites], soil_sprite,
                          self.check_watered)

    def update_plants(self):
        for plant in self.plant_sprites.sprites():
            plant.grow()

    def create_soil_tiles(self):
        # 清空现有的土壤精灵组
        self.soil_sprites.empty()
        # 遍历土壤网格的每一行和列
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                # 如果该格子被标记为已耕种('X')
                if 'X' in cell:

                    # 检查上下左右相邻格子是否也被耕种(带边界保护,避免负索引回绕)
                    t = index_row > 0 and 'X' in self.grid[index_row - 1][index_col]  # 上方格子
                    b = index_row < len(self.grid) - 1 and 'X' in self.grid[index_row + 1][index_col]  # 下方格子
                    r = index_col < len(row) - 1 and 'X' in row[index_col + 1]  # 右侧格子
                    l = index_col > 0 and 'X' in row[index_col - 1]  # 左侧格子

                    # 默认瓦片类型为单独的一块
                    tile_type = 'o'

                    # 根据相邻格子的耕种情况决定使用哪种瓦片贴图

                    # 四周都有耕种的土地
                    if all((t, r, b, l)): tile_type = 'x'

                    # 只有水平方向相邻的土地
                    if l and not any((t, r, b)): tile_type = 'r'  # 只有左边
                    if r and not any((t, l, b)): tile_type = 'l'  # 只有右边
                    if r and l and not any((t, b)): tile_type = 'lr'  # 左右都有

                    # 只有垂直方向相邻的土地
                    if t and not any((r, l, b)): tile_type = 'b'  # 只有上边
                    if b and not any((r, l, t)): tile_type = 't'  # 只有下边
                    if b and t and not any((r, l)): tile_type = 'tb'  # 上下都有

                    # 拐角形状的土地
                    if l and b and not any((t, r)): tile_type = 'tr'  # 左下角
                    if r and b and not any((t, l)): tile_type = 'tl'  # 右下角
                    if l and t and not any((b, r)): tile_type = 'br'  # 左上角
                    if r and t and not any((b, l)): tile_type = 'bl'  # 右上角

                    # T字形的土地
                    if all((t, b, r)) and not l: tile_type = 'tbr'  # 缺少左边
                    if all((t, b, l)) and not r: tile_type = 'tbl'  # 缺少右边
                    if all((l, r, t)) and not b: tile_type = 'lrb'  # 缺少下边
                    if all((l, r, b)) and not t: tile_type = 'lrt'  # 缺少上边

                    # 创建土壤瓦片精灵
                    SoilTile(
                        pos=(index_col * TILE_SIZE, index_row * TILE_SIZE),
                        surf=self.soil_surfs[tile_type],
                        groups=[self.all_sprites, self.soil_sprites]
                    )
