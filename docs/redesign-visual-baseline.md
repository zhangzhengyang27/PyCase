# PyCase 视觉基线 v2（A1 交付物）

> 状态：A1 评审中（门禁 = 代表页稿评审）｜ 日期：2026-09-29 ｜ 基线提交：8847a16
> 评审物：[代表页稿](a1-visual-baseline.html)（平台 × 外观 × 强调色实时切换，5 块审阅板）
> 上游：D1「系统原生感」与验收标准见[重设计方案](redesign-plan.md)；问题编号 B1–B12 沿用[现状审计报告](redesign-audit.md)
> 关系：页稿 HTML 是**可视真值**，本文件是**数值与规则真值**；两者由 `scripts/check_contrast.py` 绑定（token 一改，脚本与 §4 矩阵必须同步）。
> 证据图例（沿用审计报告）：R = electron-prototype/electron/src/renderer；E = electron-prototype/electron；M = electron-prototype/electron/src/main。

## 1. 设计原则（可检验）

1. **原生优先**：几何、材质、动效、窗口装饰按平台原生惯例分别定值，不做跨平台统一皮肤（macOS 为主平台，Windows 走 Fluent 映射，见 §6）。
2. **层次靠表面，不靠装饰**：卡片与面板用圆角 + 1px 细线 + 阴影分层；渐变、极光、光晕在 v2 归零。
3. **状态 = 圆点 + 中性文字**：不用色底徽章。v1 的 14% 同色底在浅色面实测 4.4–4.5:1 贴线，且与 macOS 原生语言不符；仅 Windows 弹窗保留 Fluent 语义底色（原生 InfoBar 配对）。
4. **单一图标语言**：Lucide 线性图标，stroke 1.5 @16px；emoji 与文本字形（▶ ↑↓ ↵）归零。
5. **克制**：危险操作用红色**文字**按钮而非红色填充；终端与代码区跟随主题切换（不恒暗、不反色）；强调色只出现在选中态、主操作与焦点。
6. **可机器验真**：颜色只经 token；对比度由脚本复算（§8），不靠肉眼与截图。

## 2. 三层绑定架构

| 层 | 决定 | 落点 | 取值数 |
|---|---|---|---|
| 平台层 | 字体栈 / 控件高度 / 行高 / 圆角 / 字阶 / 动效档 / 窗口装饰 / 焦点环 / 选中语义 | html[data-platform] | 2（mac、win） |
| 主题层 | 表面 / 文字 / 线条 / 阴影 | html[data-theme] | 4（mac 深、mac 浅、win 深、win 浅） |
| 强调色层 | 填充 / hover / pressed / 文字 / 光晕 | html[data-accent] | 2（系统默认、品牌靛） |

- 级联顺序：基础块（mac 深）→ 浅色块 → Windows 块 → Windows 浅色块；同层后块覆盖前块，未重定义的沿用（脚本按同一顺序解析）。
- 主题层**不含**强调色与状态色；状态色随主题/平台取不同值（§3.4），强调色随外观取不同值（§3.3）。
- 组件层颜色字面量 = 0（v2 目标，B3 落地时校验）；light 覆写只允许出现在 token 层。

## 3. Token 规格（终值）

### 3.1 平台层

| token | macOS | Windows |
|---|---|---|
| --font-ui | -apple-system, BlinkMacSystemFont, "SF Pro Text", "PingFang SC", sans-serif | "Segoe UI Variable Text", "Segoe UI", "Microsoft YaHei UI", sans-serif |
| --font-code | ui-monospace, "SF Mono", Menlo | "Cascadia Mono", Consolas |
| --fs-caption / body / title / page | 11 / 13 / 15 / 17 px | 12 / 14 / 20 / 28 px |
| --ctrl-sm / md / lg | 20 / 24 / 28 px | 24 / 32 / 40 px |
| --row-h（列表行） | 28 px | 40 px |
| --r-control / card / overlay | 6 / 10 / 12 px | 4 / 8 / 8 px |
| --sidebar-w | 224 px | 240 px |
| --titlebar-h / toolbar-h / statusbar-h / pane-head-h | 44 / 44 / 22 / 44 px | 32 / 48 / 28 / 48 px |
| --titlebar-lead / trail | 72 px / 0 | 12 px / 138 px |
| --dur-fast / base / panel | 100 / 160 / 220 ms | 150 / 200 / 250 ms |
| --ease-std | cubic-bezier(.25,.1,.25,1) | cubic-bezier(.8,0,.2,1) |
| --ease-emph | cubic-bezier(.32,.72,0,1) | cubic-bezier(.1,.9,.2,1) |
| --focus-shadow | 0 0 0 1px accent, 0 0 0 4px halo | 0 0 0 1px focus-inner, 0 0 0 3px focus-outer |
| --side-sel-bg / fg | accent / on-accent | bg-subtle / text-primary |
| --nav-indicator | none（选中 = 强调填充） | block（选中 = 中性填充 + 3×16px 强调条） |

密度的平台差异（mac 紧凑 / win 宽松）是**原生惯例**而非随意缩放：macOS 侧栏行高 28、控件 20–28；Windows 列表行高 40、控件 24–40。

实现注记（A2）：等宽栈在实现层命名为 `--font-code`——Tailwind 的 `--font-mono` 是 `@theme` 命名空间变量，同名会构成自引用而取值失效。根字号固定 16px（rem 基准），正文 13px 只给 `body`：此前 `html, body { font-size: var(--fs-body) }` 把根字号也压到 13px，**全部 rem 计工具类尺寸缩到 81%**（h-8 实测 26px 而非 32px），A2 已修正并纳入走查（`body` 13 / `html` 16 由探针断言）。

### 3.2 主题层（4 组合）

| token | mac 深 | mac 浅 | win 深 | win 浅 |
|---|---|---|---|---|
| --bg-window | #1E1E1E | #FFFFFF | #202020 | #F3F3F3 |
| --bg-chrome | #2A2A2A | #F2F2F2 | #202020 | #F3F3F3 |
| --bg-card | #2C2C2E | #FFFFFF | rgba(255,255,255,.051) | #FFFFFF |
| --bg-card-hover | #323236 | #FAFAFC | rgba(255,255,255,.07) | #FBFBFB |
| --bg-inset | rgba(0,0,0,.22) | rgba(0,0,0,.05) | rgba(255,255,255,.06) | rgba(0,0,0,.04) |
| --bg-hover | rgba(255,255,255,.06) | rgba(0,0,0,.05) | rgba(255,255,255,.06) | rgba(0,0,0,.037) |
| --bg-pressed | rgba(255,255,255,.10) | rgba(0,0,0,.09) | rgba(255,255,255,.03) | rgba(0,0,0,.024) |
| --bg-subtle（选中底） | rgba(255,255,255,.10) | rgba(0,0,0,.08) | rgba(255,255,255,.09) | rgba(0,0,0,.06) |
| --bg-sidebar（材质） | rgba(44,44,46,.60) | rgba(246,246,248,.62) | #242424（实色） | #EEEEEE（实色） |
| --bg-sidebar-fallback | #2B2B2D | #F2F2F4 | #242424 | #EEEEEE |
| --bg-console（终端/代码区） | #1A1A1A | #FFFFFF | #1A1A1A | #FFFFFF |
| --text-primary | #F5F5F7 | #1D1D1F | #FFFFFF | #1B1B1B |
| --text-secondary | #B6B6BD | #58585E | #C9C9C9 | #575757 |
| --text-tertiary | #A0A0A6 | #696970 | #A2A2A2 | #696969 |
| --text-quaternary | #71717A | #99999F | #7A7A7A | #939393 |
| --text-console | #D6D6D6 | #1D1D1F | #D6D6D6 | #1D1D1F |
| --text-gutter（行号，装饰） | #6E6E76 | #8E8E94 | #6E6E76 | #8E8E94 |
| --code-kw / str / num / cmt / fn | #569CD6 / #CE9178 / #B5CEA8 / #6A9955 / #DCDCAA | #0550AE / #A31515 / #0B6A3F / #1F7A3A / #795E26 | 同 mac 深 | 同 mac 浅 |
| --line-hairline | rgba(255,255,255,.10) | rgba(0,0,0,.10) | rgba(255,255,255,.07) | rgba(0,0,0,.06) |
| --line-strong | rgba(255,255,255,.20) | rgba(0,0,0,.18) | rgba(255,255,255,.14) | rgba(0,0,0,.14) |
| --shadow-card | 0 1px 2px rgba(0,0,0,.30) | 0 1px 3px rgba(0,0,0,.10) | 0 2px 4px rgba(0,0,0,.28) | 0 2px 4px rgba(0,0,0,.12) |
| --shadow-overlay | 0 12px 40px rgba(0,0,0,.55) | 0 12px 40px rgba(0,0,0,.18) | 0 8px 16px rgba(0,0,0,.28) | 0 8px 16px rgba(0,0,0,.14) |
| --focus-inner / outer | #0A0A0A / #FFFFFF | #0A0A0A / #FFFFFF | #0A0A0A / #FFFFFF | #FFFFFF / #0A0A0A |

材质说明：mac 侧栏毛玻璃 blur(34px) saturate(160%)；win 窗口 Mica 近似 = 基色 88% 叠桌面 + blur(64px) saturate(118%)，侧栏为实色（Fluent 侧栏本就是 Mica 上的实色层）。材质不可用时回退 --bg-sidebar-fallback；**对比度按回退实色验收**（桌面透出内容不可控）。

终端/代码区说明：**跟随主题**（浅色主题下为浅底深字），不采用"恒暗"。理由：浅色界面里嵌一块黑区在 mac/win 原生应用中都属异类（Xcode/Terminal 自身也会随外观切换），且与"跟随平台"的密度决策口径一致。语法高亮取两套：深色沿用 VS Code Dark+ 家族，浅色用 AA 达标的深色变体（见上表 code-* 行）——**不用同一组色在两个底色上硬套**。

win 浅色组合需注意级联顺序：`html[data-platform="win"]` 块**不得**再声明 --bg-console，否则会覆盖浅色块（这是评审中实际踩到的缺陷，见 §8 判别性测试）。

### 3.3 强调色层

| 组合 | 填充 | on-accent | hover | pressed | 文字 | 光晕 |
|---|---|---|---|---|---|---|
| mac 深 · 系统 | #0A84FF | #FFFFFF | #2E96FF | #0071E3 | #4DA2FF | rgba(10,132,255,.35) |
| mac 深 · 品牌 | #5E6AD2 | #FFFFFF | #6E79DB | #4F5ABF | #A0A4FF | rgba(94,106,210,.40) |
| mac 浅 · 系统 | #007AFF | #FFFFFF | #0071E3 | #0063CC | #0063CC | rgba(0,122,255,.30) |
| mac 浅 · 品牌 | #4F51C0 | #FFFFFF | #5A5CCB | #4345AD | #4143AE | rgba(79,81,192,.30) |
| win 深 · 系统 | #60CDFF | #0A0A0A | #7BD4FF | #4BC3F5 | #6CCBFF | rgba(96,205,255,.35) |
| win 深 · 品牌 | #8B8DFF | #0A0A0A | #9B9DFF | #7A7CFF | #A7A9FF | rgba(139,141,255,.35) |
| win 浅 · 系统 | #005FB8 | #FFFFFF | #196FC0 | #0067C0 | #005FB8 | rgba(0,95,184,.30) |
| win 浅 · 品牌 | #4F51C0 | #FFFFFF | #5A5CCB | #4345AD | #4143AE | rgba(79,81,192,.30) |

系统默认 = 平台系统强调色（mac 蓝 / Fluent 蓝）；品牌靛 = 项目既有 #5E6AD2 家族，浅色与 win 深色下向 AA 靠拢取值。**默认值 = 系统默认**（评审已决，见 §9）；品牌靛作为用户可选项长期保留。

### 3.4 状态色层

| 令牌 | mac 深 | mac 浅 | win 深 | win 浅 |
|---|---|---|---|---|
| --status-green | #30D158 | #1F7835 | #6CCB5F | #0E700E |
| --status-red | #FF6961 | #C80014 | #FF99A4 | #B4281A |
| --status-amber | #FFB340 | #A94C00 | #FCE100 | #8D5400 |
| --status-info-bg | transparent | transparent | #433519 | #FFF4CE |

状态色只用于圆点、图标与文字（浅色主题整体加深一档以过 AA）。--status-info-bg 仅 Windows 弹窗作 InfoBar 底色；mac 用「图标 + 中性文字」平面表达。预留：错误语义底配对（win 深 #FF99A4 on #442726 = 6.61；win 浅 #B4281A on #FDF3F4 = 5.92），待错误类 InfoBar 落地时启用。

### 3.5 字阶与字重

| 档 | mac | win | 用途 |
|---|---|---|---|
| caption | 11px | 12px | 计数、标签、辅助说明、kbd |
| body | 13px | 14px | 正文与列表标题 |
| title | 15px | 20px | 弹窗与分区标题（600） |
| page | 17px | 28px | 页面主标题（600） |

字重仅 400 / 500 / 600；v2 不再设 badge/control 独立字号（并入 caption），避免 6 档字号碎片。

### 3.6 动效

| 档 | mac | win | 用途 |
|---|---|---|---|
| fast | 100ms | 150ms | hover、焦点、颜色变化 |
| base | 160ms | 200ms | 选中、展开 |
| panel | 220ms | 250ms | 弹窗、命令面板、侧栏 |

缓动：标准 = 平台 --ease-std（mac 平滑进出、win 快出慢入）；强调 = --ease-emph（弹层入场）。全量动画在 prefers-reduced-motion 下降级为无位移（B3 落地并纳入走查）。

### 3.7 图标

Lucide 单一来源（stroke 1.5，round cap/join），尺寸三档 14 / 16 / 20px；颜色只取 currentColor。分区不再用 emoji + 色相，改用语义 Lucide 图标 + 中性 chip 底（§7.1 第 2 条）。

## 4. 对比度矩阵（WCAG 2.1）

### 4.1 口径

- 信息性文字阈值 **4.5:1**（WCAG 1.4.3 AA）；装饰/禁用（圆点、禁用文字、行号、占位提示）按 **2.5:1** 记录口径，且不承载唯一信息（WCAG 1.4.3 disabled 豁免 + 1.4.11 非文本）。
- 侧栏是材质面：按回退实色评估（mac 深 #2B2B2D / mac 浅 #F2F2F4 / win 深 #242424 / win 浅 #EEEEEE）。**规则：材质面上的信息性文字一律 ≥ tertiary**（计数徽章、kbd 提示已按此从 quaternary 提到 tertiary）。
- 强调填充上的文字按组件级 **3.0:1** 评估；未达文字 AA 的条目在下方偏差表记录，不隐瞒。
- 终端/代码区按各主题实际底色评估（深色 #1A1A1A / 浅色 #FFFFFF），语法色与正文同阈 4.5；行号按装饰 2.5。

**偏差表（记录，非通过）**

| 条目 | 比值 | 说明 |
|---|---|---|
| mac 深 · 系统强调填充 + 白字 | 3.65 | Apple 系统蓝原值，白字未达文字 AA 4.5；评审已决「默认系统强调色」，本条作为已知偏差长期记录（品牌靛可消除，见 §9） |
| mac 浅 · 系统强调填充 + 白字 | 4.02 | 同上（浅色系统蓝 #007AFF） |
| 代码行号 · 深（#6E6E76 on #1A1A1A） | 3.44 | 装饰级：行号不承载唯一信息（代码本身有序），且 user-select: none |
| 代码行号 · 浅（#8E8E94 on #FFFFFF） | 3.26 | 同上 |

品牌靛填充在四个组合均 ≥ 4.70（达文字 AA）——若未来改选品牌靛为默认，可完全消除上表前两行。

### 4.2 四组合实测

脚本 `scripts/check_contrast.py` 从页稿 token 源复算，共 142 项（mac 各 35 / win 各 36，差一项为 win 独有的 InfoBar 语义底），0 失败。下表为压缩视图（文字类 4.5 阈；quaternary 与行号为 2.5 记录阈）。

**macOS 深色**

| 检查 | 值 | 窗口 | 工具栏 | 侧栏 | 卡片 |
|---|---|---|---|---|---|
| text.primary | #F5F5F7 | 15.31 | 13.18 | 12.98 | 12.80 |
| text.secondary | #B6B6BD | 8.27 | 7.12 | 7.01 | 6.91 |
| text.tertiary | #A0A0A6 | 6.41 | 5.52 | 5.43 | 5.36 |
| text.quaternary（装饰） | #71717A | 3.45 | 2.97 | 2.92 | 2.88 |
| 终端正文 | #D6D6D6 on #1A1A1A | 11.97 | | | |
| 终端行号（装饰） | #6E6E76 on #1A1A1A | 3.44 | | | |
| 语法 kw / str / num / cmt / fn | 5.90 / 6.59 / 10.24 / 5.22 / 12.32 | | | | |
| 强调填充标签 · 系统 | #FFFFFF on #0A84FF | 3.65（偏差表） | | | |
| 强调填充标签 · 品牌 | #FFFFFF on #5E6AD2 | 4.70 | | | |
| 强调文字 · 系统 | #4DA2FF | 6.29 | | | 5.26 |
| 强调文字 · 品牌 | #A0A4FF | 7.34 | | | 6.14 |
| status.green | #30D158 | 8.25 | | | 6.89 |
| status.red | #FF6961 | 5.91 | | | 4.94 |
| status.amber | #FFB340 | 9.35 | | | 7.81 |

**macOS 浅色**

| 检查 | 值 | 窗口 | 工具栏 | 侧栏 | 卡片 |
|---|---|---|---|---|---|
| text.primary | #1D1D1F | 16.83 | 15.03 | 15.05 | 16.83 |
| text.secondary | #58585E | 7.06 | 6.31 | 6.32 | 7.06 |
| text.tertiary | #696970 | 5.45 | 4.87 | 4.87 | 5.45 |
| text.quaternary（装饰） | #99999F | 2.83 | 2.53 | 2.53 | 2.83 |
| 终端正文 | #1D1D1F on #FFFFFF | 16.83 | | | |
| 终端行号（装饰） | #8E8E94 on #FFFFFF | 3.26 | | | |
| 语法 kw / str / num / cmt / fn | 7.59 / 7.85 / 6.67 / 5.38 / 6.10 | | | | |
| 强调填充标签 · 系统 | #FFFFFF on #007AFF | 4.02（偏差表） | | | |
| 强调填充标签 · 品牌 | #FFFFFF on #4F51C0 | 6.42 | | | |
| 强调文字 · 系统 | #0063CC | 5.74 | | | 5.74 |
| 强调文字 · 品牌 | #4143AE | 7.96 | | | 7.96 |
| status.green | #1F7835 | 5.53 | | | 5.53 |
| status.red | #C80014 | 6.06 | | | 6.06 |
| status.amber | #A94C00 | 5.64 | | | 5.64 |

**Windows 深色**

| 检查 | 值 | 窗口 | 工具栏 | 侧栏 | 卡片 |
|---|---|---|---|---|---|
| text.primary | #FFFFFF | 16.29 | 16.29 | 15.52 | 14.09 |
| text.secondary | #C9C9C9 | 9.84 | 9.84 | 9.37 | 8.51 |
| text.tertiary | #A2A2A2 | 6.38 | 6.38 | 6.08 | 5.52 |
| text.quaternary（装饰） | #7A7A7A | 3.80 | 3.80 | 3.62 | 3.28 |
| 终端正文 | #D6D6D6 on #1A1A1A | 11.97 | | | |
| 终端行号（装饰） | #6E6E76 on #1A1A1A | 3.44 | | | |
| 语法 kw / str / num / cmt / fn | 5.90 / 6.59 / 10.24 / 5.22 / 12.32 | | | | |
| 强调填充标签 · 系统 | #0A0A0A on #60CDFF | 11.01 | | | |
| 强调填充标签 · 品牌 | #0A0A0A on #8B8DFF | 6.93 | | | |
| 强调文字 · 系统 | #6CCBFF | 9.02 | | | 7.80 |
| 强调文字 · 品牌 | #A7A9FF | 7.57 | | | 6.55 |
| status.green | #6CCB5F | 8.03 | | | 6.94 |
| status.red | #FF99A4 | 8.03 | | | 6.94 |
| status.amber | #FCE100 | 12.34 | | | 10.67 |
| status.amber on status-info-bg | #FCE100 on #433519 | 9.03（InfoBar） | | | |

**Windows 浅色**

| 检查 | 值 | 窗口 | 工具栏 | 侧栏 | 卡片 |
|---|---|---|---|---|---|
| text.primary | #1B1B1B | 15.52 | 15.52 | 14.85 | 17.22 |
| text.secondary | #575757 | 6.51 | 6.51 | 6.23 | 7.23 |
| text.tertiary | #696969 | 4.95 | 4.95 | 4.73 | 5.49 |
| text.quaternary（装饰） | #939393 | 2.77 | 2.77 | 2.65 | 3.07 |
| 终端正文 | #1D1D1F on #FFFFFF | 16.83 | | | |
| 终端行号（装饰） | #8E8E94 on #FFFFFF | 3.26 | | | |
| 语法 kw / str / num / cmt / fn | 7.59 / 7.85 / 6.67 / 5.38 / 6.10 | | | | |
| 强调填充标签 · 系统 | #FFFFFF on #005FB8 | 6.31 | | | |
| 强调填充标签 · 品牌 | #FFFFFF on #4F51C0 | 6.42 | | | |
| 强调文字 · 系统 | #005FB8 | 5.68 | | | 6.31 |
| 强调文字 · 品牌 | #4143AE | 7.17 | | | 7.96 |
| status.green | #0E700E | 5.66 | | | 6.28 |
| status.red | #B4281A | 5.81 | | | 6.44 |
| status.amber | #8D5400 | 5.57 | | | 6.18 |
| status.amber on status-info-bg | #8D5400 on #FFF4CE | 5.61（InfoBar） | | | |

## 5. 原生组件语言（平台语义）

| 场景 | macOS | Windows |
|---|---|---|
| 侧栏选中 | 强调色填充 + on-accent 文字；无指示条 | 中性填充（bg-subtle）+ 600 加粗 + 左侧 3×16 强调条 |
| 命令面板选中行 | 强调色填充（白字） | 中性填充 + 强调文字（不整行着色） |
| 分段控件 | 抬起段（bg-pressed + 主文字） | 强调文字 + 底部 2px 强调下划线 |
| 状态表达 | 6px 圆点 + 中性文字 | 同左；弹窗额外用 Fluent 语义底 InfoBar |
| 危险操作 | 红色文字按钮（不做红色填充） | 同左 |
| 对话框按钮序 | 右对齐，主操作最右 | 左对齐，主操作最左（Fluent ContentDialog 惯例） |
| 焦点 | 双环：1px accent + 4px halo | 双色矩形：1px 白 + 3px 黑（高对比环境可见） |
| 键盘提示 | ⌘K | Ctrl K |
| 窗口装饰 | 交通灯 12px、标题栏 44px、lead 72px | 标题栏 32px、左上图标+PyCase、右上 46×32 最小化/最大化/关闭、关闭 hover #C42B1C |
| 终端/代码 | 跟随主题（深 #1A1A1A / 浅 #FFFFFF，语法色两套） | 同左 |

## 6. Windows 映射策略（D1 引申，评审点）

| 维度 | 策略 | 依据 |
|---|---|---|
| 字体 | Segoe UI Variable Text + Cascadia Mono | Fluent 原生栈；中文回退 Microsoft YaHei UI |
| 密度 | 行高 40 / 控件 24–40 / 状态栏 28 | Windows 触控友好惯例，非 mac 数值缩放 |
| 圆角 | 4 / 8 / 8（控件/卡片/弹层） | Fluent 圆角阶梯（mac 为 6 / 10 / 12） |
| 材质 | Mica 近似（基色 88% + blur 64 + saturate 118%），侧栏实色 | Win11 原生层次；不做亚克力堆叠 |
| 选中 | 中性填充 + 强调条/下划线（不用整块强调填充） | Fluent 选中语义与 mac 相反 |
| 焦点 | 双色矩形 | Fluent 高对比可见性要求 |
| 信息条 | InfoBar 语义底色（#433519/#FFF4CE 警示，错误配对预留） | 唯一保留色底的状态表达，且只用原生配对色 |
| 窗口按钮 | 自绘标题栏按钮 46×32，关闭 hover 系统红 | Win11 caption button 规格 |
| 字阶 | title 20 / page 28（mac 15 / 17） | Windows 标题层级更大 |

## 7. v1 → v2 迁移清单

### 7.1 Kill list（v1 语言退役）

| # | 退役项 | v1 证据（实测行号） | v2 处置 |
|---|---|---|---|
| 1 | 渐变与极光装饰 | R/main.css:185-193（.aurora-hero 径向渐变）、R/main.css:77（卡片渐变 --card-grad-top/bottom）、R/main.css:105、163、170（按钮渐变）；使用点 R/components/GalleryOverview.vue:47 | 归零：层次 = 表面 + 细线 + 阴影 |
| 2 | emoji + 分区色相徽章 | R/main.css:117-124（.hue-chip 14% 色相底 + 35% 边框）；数据 R/src/overview.ts:124,131-137；使用 R/components/ExampleCard.vue:23,63、R/components/ExampleListItem.vue:53-54、R/components/DetailPage.vue:122-124,133 | 归零：Lucide 语义图标 + 中性 chip-ic 底 |
| 3 | 非标字重 590/510/650 | 47 处 / 20 文件（590×31、510×11、650×5）；R/main.css:140、R/src/style.css:152、R/App.vue:182-183 | 归零：仅 400/500/600 |
| 4 | 状态 14% 同色底徽章 | R/src/theme.css:106-108（--status-green-bg/red-bg/amber-bg） | 圆点 + 中性文字；仅 win 弹窗保留 Fluent 语义底 |
| 5 | 双真值 / 幽灵文件 | E/tailwind.config.js（无 @config 引用、content 不含 .vue）、R/src/style.css（163 行无 import、令牌值与真值分叉）；B1/B2 | 单一 token 源；实现期删除死文件 |
| 6 | 组件层颜色字面量与 light 覆写块 | 9 处手写 [data-theme='light'] 覆写（R/main.css:92,110,123,143,156,173,179,190 + R/src/style.css:63）；约 68 处颜色字面量（B5） | 收敛为 4 个主题组合块，组件层字面量 = 0 |
| 7 | 字体栈双写 | R/src/theme.css:210-211（@theme 与 :root 各一份） | 单源（平台层 token） |
| 8 | 三套动效时长并存 | R/src/theme.css:100-103（fast 120 / panel 180）与 150 三值并存、--duration-fast 零引用（B12） | 三档 token + reduced-motion 降级 |
| 9 | 硬编码 macOS 壳假设 | R/App.vue:160（pl-[72px] 红绿灯留白写死）、M/index.ts:297（仅 darwin 设 hiddenInset）、主进程未向渲染层暴露 platform（B10） | html[data-platform] 驱动全部平台差异；主进程平台信息进 preload |
| 10 | 原生 confirm 打断 | R/store.ts:520,554,1044（B6） | 全部走自绘对话框（板 4 规格） |

**A2 落地进度**（本批只退役与「壳 + token 层」直接相关的项）：

已退役：
- **#1 渐变与极光装饰 → 全清**。`R/main.css` 的 `.surface-card`/`.surface-raised`/`.btn-primary-deep` 改为平面填充；`.aurora-hero`、`.edge-highlight-top` 类与三处用法删除；全渲染层 `linear-gradient`/`radial-gradient`/`--card-grad-*` 计数 = 0（`grep -rn "linear-gradient\|radial-gradient\|card-grad" R/` 无输出）。
- **#4 状态 14% 色底 → 中性 chip**。`--status-*-bg` 删除，`bg-ok-bg`/`bg-danger-bg`/`bg-warn-bg` 三个工具类别名改指 `--chip-bg`（中性）；类名保留到 A3/A4 重写各页面时一并改掉。
- **#5 幽灵样式文件 → 已删**。`R/src/style.css`（163 行、无 import）`git rm` 删除，并清掉 `R/src/utils.ts:113` 指向它的注释；`R/tailwind.config.js` 属 B3 的单源清理范围，本批未动。
- **#6 的 light 覆写块 → 非 token 层已归零**。`R/main.css` 的 9 处 `[data-theme='light']` 全部删除；全仓非 token 层 light 覆写计数 = 0。
- **#7 字体栈双写 → 单源**：平台层 `--font-ui` / `--font-code`，`@theme` 只做映射。
- **#8 动效时长 → 三档 token**（`--dur-fast/base/panel`，新增 `dur-fast`/`dur-base`/`dur-panel` 工具类）；`--duration-*` 零引用问题随旧 token 删除消失。
- **#9 硬编码 macOS 壳**：平台信息经 preload 写入 `html[data-platform]`，`pl-[72px]` 由 `--titlebar-lead` 承担，主进程按平台分支窗口装饰。

**A3 落地进度**（画廊 / 工具箱批）：

已退役：
- **#2 emoji 与色相徽章 → 画廊侧归零**。删掉 `themes.ts` / `overview.ts` / `toolbox-groups.ts` / `category-meta.ts` 里的 emoji 字段与 `SECTION_HUES`，图标收敛到新文件 `R/src/section-icons.ts`（分区 key → Lucide 单一映射）；v0.10 遗留的 `getToolIcon`（emoji 体系）与 `THEME_STATUS_CLS`（硬编码色）作为无调用方死代码一并删除。渲染层 emoji 仅剩 2 处、均在注释里（`R/components/ExampleCard.vue:3`、`R/src/types.ts:25`）。
- **#3 字重（画廊/工具箱/筛选栏）**：`font-[510/590/650]` 在该批组件内清零，卡片标题 600、行/组头 500、正文 400；全仓非标字重由 48 处降到 26 处（余者属 A4/A5 组件）。
- **#6 组件层字面量（该批）**：卡片/列表/工具条/筛选栏/总览的颜色字面量与 `bg-accent/15`、`rounded-full`、`text-white`（强调底文字改 `text-on-accent`）全部改为 token 表达式。
- 新增可复用表面类：`.chip-ic`（语义图标 chip）、`.card-sel`、`.stat-dot`（状态圆点）、`.seg`（分段控件，mac 抬起段 / win 强调下划线）。

未退役（各有归属批次）：
- #3 余下 26 处非标字重（CommandPalette / DetailPage / OutputPanel / HistoryPanel / AIExplainPanel 等，A4/A5 重写时清除）。
- #6 的组件层字面量残量（同批 A4/A5，B3 校验归零）。
- #10 原生 confirm 三处（A5 自绘对话框批）。

### 7.2 Token 映射（v1 → v2）

| v1 | v2 | 说明 |
|---|---|---|
| --bg-marketing / --bg-panel | --bg-window / --bg-chrome | 表面语义不变，值按平台/主题重定 |
| --bg-level3 | --bg-card | 卡片底 |
| --bg-secondary | --bg-card-hover | v1「hover 后的次级表面」 |
| --bg-inset / --bg-hover | --bg-inset / --bg-hover | 语义保留，值改 |
| --text-primary…quaternary | 同名保留 | 值改；quaternary 收窄为装饰/禁用专用 |
| --brand-indigo / --accent-violet / --accent-hover / --accent-strong / --accent-ring | --accent-brand / --accent-brand-text / --accent-brand-hover / --accent-brand-text / --accent-brand-halo | 进强调色层，成为可选项之一 |
| --status-green/red/amber | 同名保留 | 值按 4 组合分档 |
| --status-*-bg | 删除 | 由圆点 + 中性文字替代；win 新增 --status-info-bg |
| --border-primary/secondary/tertiary / --line-tint | --line-hairline / --line-strong | 三档 + tint 收敛为两档 |
| --elevation-1…3 / --elevation-focus / --elevation-inset | --shadow-card / --shadow-overlay / --focus-shadow | 两档阴影 + 平台焦点环 |
| --font-sans | --font-ui | 平台化（mac/win 两栈） |
| --text-badge/caption/control/body/title/page | --fs-caption / body / title / page | 6 档收敛为 4 档 |
| --control-h-sm/md/lg | --ctrl-sm / md / lg | 值平台化 |
| --radius-badge/control/panel/card | --r-control / --r-card / --r-overlay | 4 档收敛为 3 档，值平台化 |
| --duration-fast/panel | --dur-fast / base / panel | 补齐中档，值平台化 |
| --ease-standard/panel | --ease-std / --ease-emph | 平台化取值 |
| （v1 无对应） | --bg-console / --text-console / --text-gutter / --code-kw·str·num·cmt·fn | 新增：终端与代码区随主题切换的完整色组；v1 硬编码深底 + 单色正文 |

## 8. 门禁与复现

- `python3 scripts/check_contrast.py`：从页稿 token 源复算 §4 全部条目（142 项），任一 FAIL 退出码 1。**判别性自查**（两次，均非恒真）：
  - 向页稿注入坏值（mac 深 --text-primary → #3A3A3A）→ 4 项 FAIL；退回原值 → 0 项。
  - 终端改造期间真实抓到 1 项：`html[data-platform="win"]` 块遗留 `--bg-console: #1A1A1A`，按级联顺序覆盖了浅色块 → win 浅色 6 项 FAIL（深底 + 深字）；删除该行后 0 项。此缺陷仅靠截图不易察觉（win 浅色板未在首轮截图清单内），**由门禁捕获**——这正是把矩阵做成脚本而非手抄的理由。
- `python3 scripts/check_doc_refs.py`：本文件中的文档引用有效性。
- 截图复核：页稿组合截图（4 组合全页 + 各板特写，2× DPR），逐板阅图确认；Board 1 的 Windows 选中指示条、mac/win 徽章与 kbd 提示已据此修正；浅色终端改动后复截 b2/b5 的 mac 浅 + win 浅并阅图确认（浅底深字、语法双套色）。
- 复审方式：改 token → 跑脚本 → 更新 §3/§4 → 重截受影响板。

## 9. 评审结论与遗留

**逐板走查（页稿）**：板 1 壳+画廊（选中语义、卡片层次、状态圆点、密度）；板 2 详情+运行（标题层级、标签、终端随主题、主/危险操作）；板 3 命令面板（选中语义、分组、键盘提示）；板 4 高危确认（mac 平面 vs win InfoBar、按钮序）；板 5 Token 规格（色板/字阶/控件/图标/动效读数）。

**决策记录（已拍板，页稿与文档均已按此实现）**

1. **强调色默认 = 系统默认**（mac 蓝 / Fluent 蓝）。代价：§4.1 偏差表前两行长期存在（mac 系统蓝填充 + 白字 3.65/4.02 未达文字 AA）；换取与宿主系统一致的原生观感。品牌靛（#5E6AD2 家族，四组合均 ≥ 4.70）保留为可选偏好，实现期从设置项切换而非默认。
2. **密度 = 跟随平台**：mac 行高 28 / 控件 20–28，win 行高 40 / 控件 24–40，不做统一缩放。
3. **终端与代码区 = 跟随主题**（推翻页稿初版「恒暗」）：浅色下浅底深字，语法高亮分深浅两套（见 §3.2）。落地要点见 §3.2 的级联顺序告警。

**遗留（截至 A2 收尾）**

- token 已落产品源（`R/src/theme.css`，A2），`scripts/check_contrast.py` 同步改指该文件（142 项 0 失败）。**脚本进 ci.yml 的步骤仍留待 B3**（当前靠本地/评审时手动跑）。
- 材质面可读性：mac 已实机走查（vibrancy 生效，侧栏随桌面透出，深浅两主题截图各一）；win 侧待 §8 真机渠道。
- 语法色浅色变体（#0550AE 家族）在 5.38–7.85 区间通过 AA，但未在真实 Python 长文上复核——详情页代码区仍是 v1 结构，A4 重设计该页时目视复核。
- win 窗口材质（Mica / `backgroundMaterial`）本批未启用：win 走不透明窗口底，避免在无法本机验证的环境里押注降级路径；真机验收渠道确定后开启并走查。
