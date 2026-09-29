"""贪吃蛇：网格移动 + 事件循环。运行后弹出游戏窗口，按窗口关闭键或 ESC 退出。"""
import random
import sys

import pygame

CELL, COLS, ROWS = 24, 26, 20
pygame.init()
screen = pygame.display.set_mode((COLS * CELL, ROWS * CELL))
pygame.display.set_caption("贪吃蛇")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 28)

snake = [(COLS // 2, ROWS // 2)]
direction = (1, 0)
food = (random.randrange(COLS), random.randrange(ROWS))
score = 0

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            turn = {pygame.K_UP: (0, -1), pygame.K_DOWN: (0, 1),
                     pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0)}.get(event.key)
            if turn and (turn[0] != -direction[0] or turn[1] != -direction[1]):
                direction = turn

    head = (snake[0][0] + direction[0], snake[0][1] + direction[1])
    if (head[0] < 0 or head[0] >= COLS or head[1] < 0 or head[1] >= ROWS
            or head in snake):
        print(f"游戏结束，得分 {score}")
        break
    snake.insert(0, head)
    if head == food:
        score += 1
        food = (random.randrange(COLS), random.randrange(ROWS))
    else:
        snake.pop()

    screen.fill((18, 18, 24))
    for x, y in snake:
        pygame.draw.rect(screen, (80, 220, 120), (x * CELL, y * CELL, CELL - 2, CELL - 2), border_radius=4)
    pygame.draw.rect(screen, (230, 90, 90), (food[0] * CELL, food[1] * CELL, CELL - 2, CELL - 2), border_radius=8)
    screen.blit(font.render(f"Score: {score}", True, (240, 240, 240)), (8, 6))
    pygame.display.flip()
    clock.tick(8)
