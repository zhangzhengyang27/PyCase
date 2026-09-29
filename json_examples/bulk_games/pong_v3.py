"""双人弹球·先得5分
Pygame 小游戏。W/S 与方向键控制球拍对打。
运行后弹出游戏窗口；ESC 或关闭窗口退出。
"""
import random
import sys

import pygame

W, H = 720, 440
pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Pong")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 32)
paddle_h, speed = 72, 8
left = pygame.Rect(16, H // 2 - paddle_h // 2, 12, paddle_h)
right = pygame.Rect(W - 28, H // 2 - paddle_h // 2, 12, paddle_h)
ball = pygame.Rect(W // 2 - 6, H // 2 - 6, 12, 12)
ball_v = [5.0, 3.5999999999999996]
score = [0, 0]
WIN = 5

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit(); sys.exit()
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]: left.y -= speed
    if keys[pygame.K_s]: left.y += speed
    if keys[pygame.K_UP]: right.y -= speed
    if keys[pygame.K_DOWN]: right.y += speed
    left.clamp_ip((0, 0, W, H)); right.clamp_ip((0, 0, W, H))
    ball.x += int(ball_v[0]); ball.y += int(ball_v[1])
    if ball.top <= 0 or ball.bottom >= H: ball_v[1] *= -1
    if ball.colliderect(left) or ball.colliderect(right): ball_v[0] *= -1.05
    if ball.left <= 0: score[1] += 1; ball.center = (W // 2, H // 2)
    if ball.right >= W: score[0] += 1; ball.center = (W // 2, H // 2)
    screen.fill((16, 20, 28))
    pygame.draw.rect(screen, (240, 240, 240), left)
    pygame.draw.rect(screen, (240, 240, 240), right)
    pygame.draw.rect(screen, (255, 200, 80), ball)
    screen.blit(font.render(f"{score[0]} : {score[1]}", True, (240, 240, 240)), (W // 2 - 40, 10))
    pygame.display.flip(); clock.tick(60)
    if WIN in score:
        print(f"比赛结束 {score[0]}:{score[1]}")
        break
