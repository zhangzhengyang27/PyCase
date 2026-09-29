"""记忆翻牌：状态机小游戏。运行后弹出游戏窗口，按窗口关闭键或 ESC 退出。"""
import random
import sys

import pygame

COLS, ROWS = 4, 4
CELL = 92
pygame.init()
screen = pygame.display.set_mode((COLS * CELL, ROWS * CELL))
pygame.display.set_caption("记忆翻牌")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 52)

deck = list(range(1, 9)) * 2
random.shuffle(deck)
cards = {"value": deck, "open": [False] * 16, "matched": [False] * 16}
first_pick = None

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            idx = pos[1] // CELL * COLS + pos[0] // CELL
            o, m = cards["open"], cards["matched"]
            if not o[idx] and not m[idx] and first_pick is None:
                o[idx] = True
                first_pick = idx
            elif not o[idx] and not m[idx] and first_pick is not None:
                o[idx] = True
                if cards["value"][idx] == cards["value"][first_pick]:
                    m[idx] = m[first_pick] = True
                first_pick = None

    screen.fill((30, 34, 44))
    for i in range(16):
        rect = pygame.Rect(i % COLS * CELL + 6, i // COLS * CELL + 6, CELL - 12, CELL - 12)
        if cards["open"][i] or cards["matched"][i]:
            pygame.draw.rect(screen, (70, 110, 90) if cards["matched"][i] else (90, 130, 200), rect, border_radius=8)
            img = font.render(str(cards["value"][i]), True, (245, 245, 245))
            screen.blit(img, img.get_rect(center=rect.center))
        else:
            pygame.draw.rect(screen, (60, 64, 78), rect, border_radius=8)
    pygame.display.flip()
    clock.tick(30)

    if all(cards["matched"]):
        print("全部配对完成！")
        break
