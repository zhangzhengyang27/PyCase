"""接水果：移动与碰撞。运行后弹出游戏窗口，按窗口关闭键或 ESC 退出。"""
import random
import sys

import pygame

W, H = 560, 480
pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("接水果")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 30)

basket = pygame.Rect(W // 2 - 44, H - 60, 88, 26)
fruits = []
lives, caught, spawn_ms = 3, 0, 0

while True:
    dt = clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        basket.x -= 7
    if keys[pygame.K_RIGHT]:
        basket.x += 7
    basket.clamp_ip((0, 0, W, basket.height))

    spawn_ms += dt
    if spawn_ms > 520:
        spawn_ms = 0
        fruits.append(pygame.Rect(random.randint(0, W - 22), -22, 22, 22))

    for f in fruits[:]:
        f.y += 4
        if f.colliderect(basket):
            fruits.remove(f)
            caught += 1
        elif f.y > H:
            fruits.remove(f)
            lives -= 1

    screen.fill((24, 28, 36))
    pygame.draw.rect(screen, (120, 200, 250), basket, border_radius=6)
    for f in fruits:
        pygame.draw.circle(screen, (240, 120, 120), f.center, 11)
    screen.blit(font.render(f"接住 {caught}  生命 {lives}", True, (240, 240, 240)), (10, 8))
    pygame.display.flip()
    if lives <= 0:
        print(f"游戏结束，接住 {caught} 个")
        break
