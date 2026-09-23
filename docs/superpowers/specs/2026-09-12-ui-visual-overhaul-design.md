# UI 视觉重构设计：深邃层次（Linear 精修）

- 日期：2026-09-12
- 范围：`electron-prototype/electron/src/renderer`（纯渲染层）
- 状态：设计定稿，待实施

## 1. 背景与目标

用户对现有界面的三点不满（按优先级）：

1. **布局与信息架构不舒服**——层级与跳转感不对
2. **卡片与列表样式粗糙**——单薄、间距字号不精致
3. **细节质感不足**——动效、阴影、圆角生硬

目标：在**不改动任何功能逻辑**的前提下，通过设计令牌升级与布局精修解决以上三点。参考气质：Linear / Raycast。

**非目标**：不加新功能；不做删除/备份/撤销类功能（用户已明确拒绝）；不动 sidecar、store 业务逻辑、键盘快捷键、命令面板行为。

## 2. 决策记录

| 决策点 | 结论 | 否决项 |
| --- | --- | --- |
| 布局骨架 | A · 精修现有三视图（画廊/工具箱/运行器平级 + 分区落地页） | B 一体化工作台（详情抽屉）；C 三栏资源管理器 |
| 视觉风格 | 1 · 深邃层次（深色靛蓝基因 + 渐变表面 + 高光边） | 2 HF 清爽橱窗（浅色默认）；3 Vercel 硬核终端 |
| 画廊结构 | **保留**总览→下钻两级：总览橱窗、下钻态 = 面包屑 + 左侧筛选栏 + 结果区 | 曾做「取消下钻、筛选条上置」的替代稿，用户对比后定回两级结构 |
| 主题 | 深/浅/跟随系统三态保留；深色为默认气质，浅色同步重做 | — |

## 3. 视觉语言规范（设计令牌）

以下值写入 `theme.css` 的 `:root` / `[data-theme="light"]`；`@theme` 映射方式不变。

### 3.1 表面层次

深色（默认）：

| 令牌 | 现值 | 新值 | 说明 |
| --- | --- | --- | --- |
| `--bg-marketing`（page） | `#08090a` | `#0a0b0d` | 页面底色带一丝冷蓝相 |
| `--bg-panel` | `#0f1011` | `#0e0f12` | 侧栏/工具栏 |
| `--bg-level3`（card） | `#191a1b` | `#15171c` | 卡片静态底（配合渐变使用） |
| `--bg-inset` | `#0a0b0c` | `#08090a` | 终端内嵌底 |
| `--bg-hover` | 0.04 白 | `rgba(255,255,255,0.05)` | 微调 |

卡片「深邃层次」由公共类 `.surface-card` 提供（新增，`main.css`）：

- 背景：`linear-gradient(180deg, #1c1e26, #16181f)`
- 边框：`1px solid rgba(255,255,255,0.07)`，**顶边高光** `border-top-color: rgba(255,255,255,0.11)`
- hover：`transform: translateY(-1px)`，顶边高光提至 `0.18`，阴影升为 `0 6px 18px rgba(0,0,0,0.4)`
- 圆角：`--radius-card: 9px`（新增）

浅色：page `#f6f7f8`、panel `#ffffff`、card `#ffffff` + `border: 1px solid #e7e8ea`（顶边不改）+ 阴影 `0 2px 8px rgba(24,28,34,0.06)`，hover 阴影 `0 6px 18px rgba(24,28,34,0.10)`；渐变在浅色上不使用。

### 3.2 分类与分区色相体系

用 CSS 变量 + `color-mix` 驱动（Electron 33 / Chromium 130 支持），避免为每个分区写死类名：

- 分类徽章（`category-meta.ts`）：`topics` 靛蓝、`tools` 绿、`projects` 琥珀、`user` 青——替换现有的 4 组语义类。
- 分区色相（`overview.ts` 新增 `SECTION_HUES` 常量，按分区 key 映射，纯数据不动逻辑）：

| 分区 key | 色相值 |
| --- | --- |
| viz | `#5e6ad2` 靛蓝 |
| turtle | `#2fa866` 绿 |
| games | `#9a6bf2` 紫 |
| opencv | `#3d8fe0` 蓝 |
| images | `#e0566a` 玫红 |
| tag:basics | `#64748b` 石板 |
| tag:advanced | `#d9a03d` 琥珀 |
| tag:crawling | `#e07840` 橙 |
| tag:webapp | `#38a8e0` 天蓝 |
| tag:office | `#8a7dd8` 藕紫 |
| tag:database | `#2fb8a6` 青 |
| tag:testing | `#7fb846` 青柠 |
| tag:algo | `#5f8dd9` 钢蓝 |
| projects | `#d471a8` 粉 |
| others | 中性灰（不配色相） |

区头图标徽章样式：`background: color-mix(in srgb, var(--hue) 14%, transparent)`、`border: 1px solid color-mix(in srgb, var(--hue) 35%, transparent)`。前景：深色主题 `color-mix(in srgb, var(--hue) 70%, white 30%)`；浅色主题 `color-mix(in srgb, var(--hue) 55%, black 45%)`（向黑压暗以对 14% tint 底达 AA 4.5:1，实现后按 §8 抽检校准混合比，若不达标调深一档）。卡片内的分类图标徽章同语法。相邻分区色相需错开（按上表顺序目视校验）。

### 3.3 圆角

新增 `--radius-card: 9px`；badge 3px / control 5px / panel 8px 不变；药丸仍限收藏与质量分 pill。

### 3.4 阴影

- 卡片静态：`0 1px 2px rgba(0,0,0,0.25)`
- 卡片 hover：`0 6px 18px rgba(0,0,0,0.4)`
- 主按钮：`0 2px 8px rgba(94,106,210,0.35)`，hover `0.45`
- elev-2/3（弹窗）不变

### 3.5 主按钮（BaseButton variant="primary"）

- 深色：`background: linear-gradient(180deg, #6a79e0, #5662c8)`；`border: 1px solid rgba(255,255,255,0.16)`，顶边 `rgba(255,255,255,0.30)`；文字白；hover 背景提亮一档 + glow 加深；active 轻内凹（translateY 0.5px）
- 浅色：实色 `#4f51c0` + 轻 glow，不用渐变
- 禁用态保持现有 opacity 语义

### 3.6 排版

字号阶梯不变（badge 10 / caption 11 / control 12 / body 13 / title 15 / page 17）。调整：

- 页面标题（示例库/工具箱）：`font-weight 650`、`letter-spacing -0.02em`
- 总览统计：升级为 chips——mono 数字 + caption 文字，底 `rgba(255,255,255,0.045)` + 边 `rgba(255,255,255,0.07)`；可运行率为绿色 tint 变体
- Hero 背景加靛蓝极光：两条 `radial-gradient`（13% / 7% 透明度），仅总览页头区，浅色主题降为 6% / 3%

## 4. 界面规范

### 4.1 画廊总览（GalleryOverview）

- 结构不变：固定页头 + 分区横向带滚动。
- 页头：标题 + 统计 chips 行（`1199 个示例 · 6 大主题 · 92% 可运行 · ★ 23 收藏`）+ 右侧「浏览全部」「★ 我的收藏（primary）」。
- 区头：色相图标徽章（18px）+ 分区名（title 字重 650）+ 计数 + 右侧「查看全部 →」。
- 卡片行：预览 8 张 + 「还有 N 个」虚线卡，保留横向滚动。

### 4.2 下钻浏览态（GalleryView + FilterSidebar + BrowseToolbar)

- **面包屑返回条**（新增，26px 高）：`← 示例库 / {结果标题}`；结果标题由筛选派生（主题名 / 标签组名「综合项目」/「全部示例」/「我的收藏」），右侧显示结果数；点「←」或「示例库」回总览。
- FilterSidebar 精修：顶部「筛选」小标改 `11px`、`#5b6068`、加宽字距；组头/行结构、折叠、计数徽标逻辑全保留；激活行 `bg-accent/15`。
- BrowseToolbar：筛选芯片改 accent-tint 底 + accent-strong 文字（已有）+ 可移除 ×；排序、密度切换保留。

### 4.3 详情页（DetailPage + OutputPanel）

- 头部 44px 结构不变；标题下新增**路径副标题**：`{category} / {id 相对路径}`，mono 10px、ink-faint（数据源 `ex.category` + `ex.id`/`ex.name`，纯前端拼接）。
- 右栏 tab 行改**分段控件**：容器 inset 底 + `rounded-control`，激活段 `bg-card` + 边框 + 微阴影；role=tablist 语义保留。
- 终端输出包**终端容器**：`bg-inset` + `rounded-panel` + 内边框 + 8px 内边距，状态点与「清空」移到容器外右角。资源/历史两 tab 同容器包裹，视觉统一。

### 4.4 工具箱（ToolboxView）

- 头区/统计/搜索收藏排序结构不变；区头图标徽章换色相 chip（按 `PROJECT_ICONS` 键固定映射，与 3.2 同语法）；卡片换 `.surface-card` 语言。

### 4.5 运行器（RunnerView）

- 轻改：搜索列表、输出区对齐新令牌；输出区使用同一终端容器样式。

### 4.6 全局件

- 导航激活项：改 `.surface-card` 渐变胶囊 + 高光边（替换现有 bg-card + 左缘条；左缘强调条保留）。
- 命令面板、AppModal、Toast、SkeletonCard、AppEmpty：换新表面值与高光边；弹窗加顶边高光。结构不动。

## 5. 动效规范

| 场景 | 参数 |
| --- | --- |
| 卡片 hover | `translateY(-1px)` + 阴影，`160ms var(--ease-standard)` |
| 卡片/列表行入场 | opacity 0→1 + `translateY(4px)`，每个 stagger `20ms`；**仅每屏前 8 项做 stagger**（index≥8 延迟为 0），总延迟封顶 160ms |
| 视图切换（画廊/工具箱/运行器/详情） | `200ms` fade + `translateY(4px)`，用 `<Transition mode="out-in">` 包裹（需把 v-show 切换改为动态组件或 key 切换） |
| 弹窗/命令面板 | 保留现有 `modal-in`（ease-panel） |

约束：只动 `opacity` / `transform`；不加弹簧过冲（克制、Linear 式）；`prefers-reduced-motion` 的全局 0.01ms 降级已存在，新增动效自动被覆盖，无需额外处理。

## 6. 兼容与无障碍约束

- 现有全部 aria/role/focus-trap 管理保留；面包屑与分段控件补 aria（`aria-current`、tablist 语义沿用）。
- 对比度：新色相前景对其 14% tint 底 ≥ 4.5:1（深色用 mix 白 30% 前景，浅色加深色相值）；实现后抽检 4 个代表色（viz/images/basics/testing）。
- `content-visibility` 长列表优化保留；Monaco 的 accent-violet 语法色不动。
- `viewPrefs`/`safetyPrefs`/`runPrefs` 等持久化键不动。

## 7. 实施范围（文件清单）

均在 `electron-prototype/electron/src/renderer` 下：

- `src/theme.css`——令牌值更新；新增 `--radius-card`、卡片渐变/高光、色相 mix 规则
- `src/main.css`——`.surface-card` 公共类、入场动画 keyframes
- `src/category-meta.ts`——分类色相化
- `src/overview.ts`——`SECTION_HUES` 常量（纯数据）
- `App.vue`——导航激活胶囊
- `components/GalleryOverview.vue`——统计 chips、区头色相徽章、hero 极光
- `components/GalleryView.vue`——面包屑条、视图切换过渡
- `components/FilterSidebar.vue` / `BrowseToolbar.vue`——样式精修
- `components/ExampleCard.vue` / `ExampleListItem.vue`——`.surface-card`、hover 抬升、入场 stagger
- `components/DetailPage.vue`——路径副标题、分段控件、终端容器
- `components/OutputPanel.vue`——终端容器
- `components/ToolboxView.vue` / `RunnerView.vue`——令牌对齐
- `components/base/BaseButton.vue`（primary 渐变）、`AppModal.vue`、`SkeletonCard.vue`、`CommandPalette.vue`、`AppToast.vue`——小调

**明确不动**：`store.ts` 业务逻辑、`monaco.ts`、sidecar、smoke/e2e 脚本、快捷键映射。

## 8. 验收标准

1. `npm run typecheck`、`npm run build`、`npm run smoke`、E2E 全部通过。
2. 深/浅两主题抽检文字对比度 ≥ 4.5:1（新色相前景、激活行、筛选芯片）。
3. `prefers-reduced-motion` 下无位移动画。
4. 1199 个示例画廊滚动流畅度无回归（content-visibility 保留）。
5. 渲染层无新增 console 错误（smoke 脚本口径）。
