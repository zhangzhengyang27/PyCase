// tool-schemas-games.ts：Pygame 游戏实验室（game-*/pygame-* 系列归并单页）。
// 生成**原生 pygame** 代码：运行弹出游戏窗口实时游玩，ESC/关窗结束。
// 5 个玩法的实现忠实移植 bulk_games 与 showcase 游戏源码，差异参数（速度/窗口/目标分/砖阵）全部页面化。
// 画廊路由专用注册。
import type { FieldSpec, InteractiveToolSchema } from './interactive-tools'

const GAMES_HEAD = `import random
import sys

import pygame

random.seed(42)
`

export interface GameType {
  value: string
  label: string
  description: string
  fields: FieldSpec[]
  body: (v: Record<string, unknown>) => string
}

const P = (key: string, label: string, def: number, help?: string) => ({
  key, label, type: 'number' as const, default: def, width: 'half' as const, ...(help ? { help } : {})
})

const gamesFamily = (
  value: string,
  label: string,
  description: string,
  fields: FieldSpec[],
  body: (v: Record<string, unknown>) => string
): GameType => ({ value, label, description, fields, body })

export const GAME_TYPES: GameType[] = [
  gamesFamily('snake', '贪吃蛇',
  '网格贪吃蛇：吃食物变长，撞墙/自身结束（game-snake 全变体的速度与窗口全部参数化）。',
  [P('speed', '速度（FPS）', 7), P('cell', '格子大小', 24), P('cols', '横向格数', 24), P('rows', '纵向格数', 18)],
  (v) => `CELL = max(12, ${Math.max(12, Math.trunc(Number(v.cell) || 24))})
COLS = max(8, ${Math.max(8, Math.trunc(Number(v.cols) || 24))})
ROWS = max(8, ${Math.max(8, Math.trunc(Number(v.rows) || 18))})
SPEED = max(2, ${Math.max(2, Math.trunc(Number(v.speed) || 7))})
BODY_COLOR = (60, 200, 100)

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
            pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            turn = {pygame.K_UP: (0, -1), pygame.K_DOWN: (0, 1),
                    pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0)}.get(event.key)
            if turn and (turn[0] != -direction[0] or turn[1] != -direction[1]):
                direction = turn

    head = (snake[0][0] + direction[0], snake[0][1] + direction[1])
    if head[0] < 0 or head[0] >= COLS or head[1] < 0 or head[1] >= ROWS or head in snake:
        print(f"游戏结束，得分 {score}")
        break
    snake.insert(0, head)
    if head == food:
        score += 1
        food = (random.randrange(COLS), random.randrange(ROWS))
    else:
        snake.pop()

    screen.fill((16, 18, 24))
    for x, y in snake:
        pygame.draw.rect(screen, BODY_COLOR, (x * CELL, y * CELL, CELL - 2, CELL - 2), border_radius=4)
    pygame.draw.rect(screen, (230, 90, 90), (food[0] * CELL, food[1] * CELL, CELL - 2, CELL - 2), border_radius=8)
    screen.blit(font.render(f"Score: {score}", True, (240, 240, 240)), (8, 6))
    pygame.display.flip()
    clock.tick(SPEED)
pygame.quit()`),
  gamesFamily('pong', '双人弹球',
  'W/S 与方向键控制球拍对打，先到目标分获胜（game-pong 全变体的窗口与目标分参数化）。',
  [P('first-to', '目标分', 3), P('width', '窗口宽', 640), P('height', '窗口高', 440), P('paddle-speed', '球拍速度', 6)],
  (v) => `W = max(320, ${Math.max(320, Math.trunc(Number(v.width) || 640))})
H = max(240, ${Math.max(240, Math.trunc(Number(v.height) || 440))})
WIN = max(1, ${Math.max(1, Math.trunc(Number(v['first-to']) || 3))})
PADDLE_SPEED = max(2, ${Math.max(2, Math.trunc(Number(v['paddle-speed']) || 6))})

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Pong")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 32)
paddle_h, speed = 88, PADDLE_SPEED
left = pygame.Rect(16, H // 2 - paddle_h // 2, 12, paddle_h)
right = pygame.Rect(W - 28, H // 2 - paddle_h // 2, 12, paddle_h)
ball = pygame.Rect(W // 2 - 6, H // 2 - 6, 12, 12)
ball_v = [4.0, 2.8]
score = [0, 0]

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
pygame.quit()`),
  gamesFamily('catch', '接水果',
  '左右移动篮子接水果，漏接扣命（game-catch 全变体的落速与生成间隔参数化）。',
  [P('drop', '水果落速', 3.4), P('spawn', '生成间隔ms', 560), P('lives', '生命数', 3)],
  (v) => `W, H = 560, 480
DROP = max(0.5, ${Number(v.drop) || 3.4})
SPAWN_MS = max(80, ${Math.max(80, Math.trunc(Number(v.spawn) || 560))})
LIVES = max(1, ${Math.max(1, Math.trunc(Number(v.lives) || 3))})

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("接水果")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 30)

basket = pygame.Rect(W // 2 - 44, H - 60, 88, 26)
fruits = []
lives, caught, spawn_ms = LIVES, 0, 0
PALETTE = ["#e74c3c", "#f39c12", "#f1c40f"]

while True:
    dt = clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit(); sys.exit()
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]: basket.x -= 7
    if keys[pygame.K_RIGHT]: basket.x += 7
    basket.clamp_ip((0, 0, W, basket.height))
    spawn_ms += dt
    if spawn_ms > SPAWN_MS:
        spawn_ms = 0
        fruits.append(pygame.Rect(random.randint(0, W - 22), -22, 22, 22))
    for f in fruits[:]:
        f.y += DROP
        if f.colliderect(basket):
            fruits.remove(f); caught += 1
        elif f.y > H:
            fruits.remove(f); lives -= 1
    screen.fill((24, 28, 36))
    pygame.draw.rect(screen, (120, 200, 250), basket, border_radius=6)
    for i, f in enumerate(fruits):
        pygame.draw.circle(screen, PALETTE[i % len(PALETTE)], f.center, 11)
    screen.blit(font.render(f"接住 {caught}  生命 {lives}", True, (240, 240, 240)), (10, 8))
    pygame.display.flip()
    if lives <= 0:
        print(f"游戏结束，接住 {caught} 个")
        break
pygame.quit()`),
  gamesFamily('memory', '记忆翻牌',
  '翻牌配对状态机：点击翻开两张，相同即消除（网格与牌数参数化）。',
  [P('cols', '列数', 4, '偶数网格'), P('rows', '行数', 4), P('cell', '牌尺寸', 92)],
  (v) => `COLS = max(2, ${Math.max(2, Math.trunc(Number(v.cols) || 4))})
ROWS = max(2, ${Math.max(2, Math.trunc(Number(v.rows) || 4))})
if (COLS * ROWS) % 2:
    ROWS += 1  # 牌数必须为偶数才能两两配对
CELL = max(48, ${Math.max(48, Math.trunc(Number(v.cell) || 92))})

pygame.init()
screen = pygame.display.set_mode((COLS * CELL, ROWS * CELL))
pygame.display.set_caption("记忆翻牌")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 52)

deck = list(range(1, COLS * ROWS // 2 + 1)) * 2
random.shuffle(deck)
cards = {"value": deck, "open": [False] * (COLS * ROWS), "matched": [False] * (COLS * ROWS)}
first_pick = None

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit(); sys.exit()
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
    for i in range(COLS * ROWS):
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
pygame.quit()`),
  gamesFamily('breakout', '打砖块',
  '球拍反弹消砖（砖阵行列与球速参数化）。',
  [P('brick-rows', '砖行数', 5), P('brick-cols', '砖列数', 9), P('ball-speed', '球速', 3.6)],
  (v) => `W, H = 560, 480
BRICK_ROWS = max(2, ${Math.max(2, Math.trunc(Number(v['brick-rows']) || 5))})
BRICK_COLS = max(4, ${Math.max(4, Math.trunc(Number(v['brick-cols']) || 9))})
SPEED = max(1.0, ${Number(v['ball-speed']) || 3.6})

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("打砖块")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 30)

paddle = pygame.Rect(W // 2 - 40, H - 40, 80, 12)
ball = pygame.Rect(W // 2 - 6, H // 2, 12, 12)
ball_v = [SPEED, -SPEED * 1.05]

bricks = []
bw = (W - 48) / BRICK_COLS - 6
for row in range(BRICK_ROWS):
    for col in range(BRICK_COLS):
        bricks.append(pygame.Rect(24 + col * (bw + 6), 50 + row * 26, bw, 20))

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
    palette = [(230, 90, 90), (240, 160, 70), (250, 210, 90), (120, 210, 130), (110, 170, 250)]
    for i, b in enumerate(bricks):
        pygame.draw.rect(screen, palette[(i // BRICK_COLS) % len(palette)], b, border_radius=4)
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
pygame.quit()`)
]

// ---------------------------------------------------------------------------
// 游戏实验室：5 玩法归并单页（类型选择器 + 动态参数表单）
// ---------------------------------------------------------------------------
const GAME_TYPE_FIELD: FieldSpec = {
  key: 'type',
  label: '游戏',
  type: 'select',
  default: 'snake',
  width: 'full',
  options: GAME_TYPES.map((t) => ({ value: t.value, label: t.label }))
}

export const gamesLabSchema: InteractiveToolSchema = {
  id: 'interactive:games-lab',
  title: 'Pygame 游戏实验室',
  description: '贪吃蛇 / 双人弹球 / 接水果 / 记忆翻牌 / 打砖块：运行弹出原生 pygame 窗口实时游玩（ESC 或关窗结束），速度/窗口/目标分全部可调。',
  tags: ['pygame', '游戏'],
  fields: (v) => {
    const t = GAME_TYPES.find((x) => x.value === v.type) ?? GAME_TYPES[0]!
    return [GAME_TYPE_FIELD, ...t.fields]
  },
  computeVia: 'sidecar',
  compute: (v) => ({ rows: [{ label: '游戏', value: String(v.type ?? 'snake') }] }),
  pyCode: (v) => {
    const t = GAME_TYPES.find((x) => x.value === v.type) ?? GAME_TYPES[0]!
    return `${GAMES_HEAD}\n${t.body(v)}`
  }
}
