"""打砖块 Breakout。运行后弹出游戏窗口，按窗口关闭键或 ESC 退出。"""
import sys

import pygame

W, H = 560, 480
pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("打砖块")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 30)

paddle = pygame.Rect(W // 2 - 40, H - 40, 80, 12)
ball = pygame.Rect(W // 2 - 6, H // 2, 12, 12)
ball_v = [3.6, -3.8]

bricks = []
for row in range(5):
    for col in range(9):
        bricks.append(pygame.Rect(24 + col * 58, 50 + row * 26, 52, 20))

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        paddle.x -= 6
    if keys[pygame.K_RIGHT]:
        paddle.x += 6
    paddle.clamp_ip((0, 0, W, H))

    ball.x += int(ball_v[0])
    ball.y += int(ball_v[1])
    if ball.left <= 0 or ball.right >= W:
        ball_v[0] *= -1
    if ball.top <= 0:
        ball_v[1] *= -1
    if ball.colliderect(paddle) and ball_v[1] > 0:
        ball_v[1] *= -1
    for b in bricks[:]:
        if ball.colliderect(b):
            bricks.remove(b)
            ball_v[1] *= -1
            break

    screen.fill((20, 22, 30))
    colors = [(230, 90, 90), (240, 160, 70), (250, 210, 90), (120, 210, 130), (110, 170, 250)]
    for i, b in enumerate(bricks):
        pygame.draw.rect(screen, colors[i // 9], b, border_radius=4)
    pygame.draw.rect(screen, (240, 240, 240), paddle, border_radius=6)
    pygame.draw.circle(screen, (255, 210, 120), ball.center, 6)
    pygame.display.flip()
    clock.tick(60)

    if not bricks:
        print("全部消除，你赢了！")
        break
    if ball.top > H:
        print("球落底，游戏结束")
        break
