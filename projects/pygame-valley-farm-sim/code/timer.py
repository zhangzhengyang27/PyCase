#! /usr/bin/python3
# coding=utf-8

import pygame


class Timer:
    def __init__(self, duration, func=None):
        # 初始化定时器
        # duration: 持续时间(毫秒)
        # func: 定时结束时要执行的回调函数
        self.duration = duration
        self.func = func
        self.start_time = 0  # 开始时间
        self.active = False  # 定时器是否激活

    def activate(self):
        # 激活定时器
        self.active = True
        self.start_time = pygame.time.get_ticks()  # 获取当前时间作为开始时间

    def deactivate(self):
        # 停用定时器
        self.active = False
        self.start_time = 0  # 重置开始时间

    def update(self):
        # 更新定时器状态
        current_time = pygame.time.get_ticks()  # 获取当前时间
        if current_time - self.start_time >= self.duration:  # 检查是否超过持续时间
            if self.func and self.start_time != 0:
                self.func()  # 如果有回调函数则执行

            self.deactivate()  # 如果超时则停用定时器
