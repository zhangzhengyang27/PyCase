# 山谷农场模拟游戏

基于 Pygame 的 2D 农场模拟游戏（Sprout Land），支持耕种、浇水、种植、砍树等农场操作。

## 文件结构

- `code/main.py` — 游戏主入口，初始化 Pygame 并启动游戏循环
- `code/level.py` — 关卡管理，加载 Tiled 地图、创建精灵与相机系统
- `code/player.py` — 玩家控制：移动、工具切换（锄头/斧头/浇水）、种子种植、碰撞检测
- `code/soil.py` — 土壤系统：耕种、浇水、植物生长与收获
- `code/sky.py` — 天气系统（雨天效果）
- `code/overlay.py` — HUD 叠加层（工具与种子显示）
- `code/sprites.py` — 通用精灵类（树木、水面、装饰物等）
- `code/settings.py` — 游戏配置（分辨率、图层、生长速度、价格等）
- `code/timer.py` — 计时器工具类
- `code/transition.py` — 场景过渡动画
- `code/support.py` — 资源加载工具函数
- `data/map.tmx` — Tiled 地图数据
- `graphics/` — 角色动画、环境贴图、果实、土壤等图片资源
- `audio/` — 背景音乐与音效
- `font/` — 游戏字体

## 操作方式

| 按键 | 功能 |
| --- | --- |
| 方向键 | 移动角色 |
| 空格 | 使用当前工具 |
| Q | 切换工具（锄头→斧头→浇水） |
| E | 切换种子（玉米→番茄） |
| 左Ctrl | 种植种子 |
| 回车 | 交互（如睡觉结束当天） |

## 运行方式

```bash
cd code
python main.py
```

## 依赖

- pygame
- pytmx（解析 Tiled 地图文件）
