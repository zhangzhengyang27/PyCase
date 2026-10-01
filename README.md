# Python 示例仓库管理器

一个 **Electron 壳 + Python sidecar** 的桌面应用：内置 **1493 条 Python 示例**，可浏览、筛选、
编辑，并在共享虚拟环境里隔离运行，实时查看输出与生成的图片。

两条贯穿全局的设计：

- **数据契约 v2**：真相源 = 清单（只存元数据，14 个集合、1493 条）+ 真实 `.py` 源码树；
  启动零写盘，运行/上传先进**按需工作区**（`.json_examples_cache/v2/`），编辑保存写回真实文件
  （可恢复：每次覆盖前自动留快照，详情页可看差异并还原）。
- 全项目共用仓库根一份 `.venv`，依赖按项目级 `requirements.txt`（由 `python -m app.facts_cli
  requirements` 从清单与派生 import 分析汇总）一次装齐，示例本身不单独建环境；
  首启装包优先读 `requirements.lock.txt`（`uv pip compile` 生成的全钉锁，CI 有新鲜度门禁），
  可复现且不随 PyPI 上新漂移。

## 技术栈

| 层 | 位置 | 技术 |
|---|---|---|
| 桌面壳 | `electron-prototype/electron/src/main/index.ts` | Electron 33 + electron-vite（mac 原生 chrome / Windows 自绘标题栏） |
| 渲染层 | `electron-prototype/electron/src/renderer/` | Vue 3 + Tailwind 4（CSS-first token 三层）+ Monaco + Lucide（无头行为层 reka-ui + 自研皮肤，无样式化 UI 框架） |
| 后端 | `electron-prototype/sidecar/server.py` | 纯标准库 + asyncio，stdio JSON-RPC 2.0（25 个方法，方法表见 `electron-prototype/shared/protocol.json`） |
| 核心逻辑 | `app/` | Python 命名空间包：契约存储 / 烘焙事实 / 迁移 / 安全 / 评分 / 环境 |
| 示例运行环境 | 仓库根 `.venv` | Python 3.13，依赖见 `requirements.txt` |

## 快速开始

```bash
cd electron-prototype/electron
npm install
npm run dev          # = electron-vite dev；sidecar 由主进程自动 spawn，无需手动起
```

首次启动会显示首启引导页，后台创建并预热 `.venv`（数分钟，按 `requirements.txt` 装依赖；
可视化进度、失败可重试/查看日志）。

常用命令（均在 `electron-prototype/electron` 下）：

```bash
npm run typecheck            # tsc + vue-tsc（两个 tsconfig 均 noImplicitAny）
npm run lint                 # ESLint + stylelint
npm run format:check         # Prettier 校验（format 为写入）
npm test                     # Vitest + jsdom 组件测试
npm run smoke                # 真实 Electron 走查（含性能与失败恢复探针）
npm run sidecar              # 冻结 Python sidecar 并冒烟（打包链第一步）
npm run dist:mac / dist:win  # 出包（electron-builder；sidecar 自动先冻结）
```

## 测试

```bash
# Python 侧（共享 venv，需 pytest）
.venv/bin/python -m pytest tests/ -q

# 前端纯函数（经 tests/renderer-loader.mjs 加载真实 TS 源码）
node tests/test_filter_engine.mjs
node tests/test_renderer_utils.mjs
node tests/test_overview.mjs
node tests/test_filter_chips.mjs
node tests/test_toolbox_groups.mjs

# 主题令牌 ↔ 组件类名一致性（@theme 漏映射即红，审计 P1 回归网）
node tests/test_theme_tokens.mjs

# shared/paths 数据根契约（openLog 双模式路径的单一来源）
node tests/test_shared_paths.mjs

# 渲染层状态编排与行级差异（加载真实 store 域与 diff.ts，vue 走真实响应式，IPC 用桩）
node tests/test_store.mjs
node tests/test_diff.mjs

# Vue 组件渲染层（Vitest + jsdom，真实 SFC 编译，需先在 electron-prototype/electron 下 npm ci）
cd electron-prototype/electron && npm test
```

测试规模（2026-10-01 实测）：pytest **206**（覆盖率门禁 ≥70%，覆盖率参数只在 CI）、Vitest **293**、
mjs 纯函数 **9 份**、
真实 Electron 走查（`npm run smoke`，含壳/画廊/详情/全局层/首启/资源/A6 产品化/性能段）
与 E2E 全链路、双平台打包矩阵（CI）。

前端测试分两层，各自有明确的适用面：

| 层 | 运行器 | 位置 | 适用 |
|---|---|---|---|
| 纯逻辑模块 | `node --test`（`tests/renderer-loader.mjs` 转译 TS） | `tests/test_*.mjs` | filter-engine / utils / overview / store 等无 DOM、无 SFC 的模块，零 bundler、启动快 |
| Vue 组件 | Vitest + jsdom | `electron-prototype/electron/src/renderer/components/__tests__/*.spec.ts` | 需要 SFC 编译与 DOM 的 `.vue` 组件；与 `electron.vite.config.ts` 共用 `@vitejs/plugin-vue`，编译链与真实构建一致 |

组件的 jsdom 环境缺口（`PointerEvent` / `IntersectionObserver` / `Blob.arrayBuffer` / `matchMedia`）
与跨用例清理统一由 `electron-prototype/electron/vitest.setup.ts` 兜底，单个 spec 不必重复补桩。

门禁（CI 全绿才算过）：ruff（app/scripts/tests/sidecar）· mypy（app + sidecar，渐进注解）·
文档引用防漂移 `scripts/check_doc_refs.py` · 对比度 `scripts/check_contrast.py` ·
派生数据门禁 `python -m app.facts_cli check / requirements --check` · 版本一致性
`scripts/sync_version.py --check` · ESLint/stylelint/Prettier · tsc/vue-tsc · 覆盖率 ≥70%。
提交前钩子见 `.pre-commit-config.yaml`。

## 项目结构

| 路径 | 职责 |
|---|---|
| `app/` | Python 核心包：契约存储（`contract_store.py`）、烘焙事实（`facts.py`）、迁移（`migration*.py`）、安全/评分/环境 |
| `electron-prototype/electron/` | Electron 主进程 + preload + Vue 渲染层（store 分 10 域，见 `src/renderer/src/store/`） |
| `electron-prototype/sidecar/` | Python 后端：JSON-RPC 接口、运行器、环境准备（纯标准库） |
| `electron-prototype/shared/` | 跨语言单一来源：`protocol.json`（RPC 方法表）+ `protocol.ts`（客户端类型） |
| `json_examples/` | 真相源：14 份清单（元数据）+ `<集合>/` 真实源码树 + `facts.json`（烘焙事实） |
| `topics/ tools/ projects/` | 原位示例源码（清单 `file` 以 `../` 指回这里），**不可删** |
| `examples_assets/` | 目录型示例（科研绘图 notebook）的源码与数据兄弟，随包分发 |
| `scripts/` | 门禁与工具：`check_contrast.py` / `check_doc_refs.py` / `sync_version.py` / `build_sidecar.py` / 抽样回归等 |
| `tests/` | pytest（Python 侧 + 护栏 G1–G8）+ node --test（前端纯函数与状态域） |
| `docs/` | 设计与基线文档，其中 `docs/json-examples.md` 讲透了 JSON 真相源机制 |

## 功能

- 📥 **导入自己的示例**：侧栏一键把任意本地目录的 .py 文件导入为「我的示例集合」（三步向导：选目录 → 预览 → 导入，自动猜依赖、id 防冲突），存于本机应用数据随应用存续，与内置库并存展示、详情页可删除
- ✨ **示例画廊**：侧栏「示例画廊」下挂二级分区菜单——「全部示例」+ 15 个分区（5 大主题 / 8 标签组 / 项目 / 其它，各带计数与选中态），点选即在右侧响应式网格中浏览该分区；筛选维度收成结果条上的工具栏下拉（主题 / 可运行性 / 质量分 / 运行状态 / 标签多选，每档带 facet 计数）+ 收藏开关，网格/清单双密度、触底无限加载；当前生效筛选以可移除芯片汇总在结果条，并与分区范围、全文搜索任意叠加；工具类示例只待在工具箱，画廊各层不重复展示
- 🩺 **可运行性体检**：每条示例静态判定五态（可运行 / 缺依赖 / 空壳 / 语法损坏 / 高危，另有扫描异常时的「状态未知」），卡片直接标注负面状态；缺依赖判定基于共享运行环境的真实模块索引，详情页给出一键「安装依赖」并自动重跑（按派生 import 分析装包）
- 🧰 **工具箱**：`tools` 分类工具的独立视图——按工具项目分区（依目录结构自动分组），区头 Lucide 图标 + 卡片网格，大组默认收起、一键展开；头区统计与搜索 / 收藏 / 组内排序，共用同一套筛选引擎
- 🎨 **主题维度**：Turtle 绘图 / Pygame 游戏 / OpenCV 视觉 / PIL 图像处理 / 数据可视化作为画廊筛选维度（按代码 import 特征自动归类），不再是独立页面
- 📋 **示例详情页**：点开卡片即达——Monaco 编辑（保存写回**真实源码文件**，覆盖前自动留快照：版本标签页可看行级差异并一键还原）、argparse 参数表单、运行输出与结果图片、资源上传、该示例的运行历史、AI 解释，一页走完闭环
- ⌨️ **代码运行器**：最基础的运行入口——快速查找示例、只读源码预览、单行命令行参数、运行/停止
- ⌘ **Cmd+K 全局搜索**：跨视图快速定位示例并直达运行
- ▶️ **隔离运行**：asyncio 子进程执行，stdout 实时流式回显，超时自动终止
- 🐍 **共享运行环境**：本项目即一个应用，示例是它的模块——全项目共用仓库根 `.venv` 一份环境，依赖按项目级 `requirements.txt`（`python -m app.facts_cli requirements` 从清单 requirements 与烘焙 import 分析汇总；生成器脚本已退役）一次装齐
- 🖼️ **结果图片预览**：运行结束后递归扫描工作目录，自动预览本次生成的图片，支持下载保存
- 📎 **资源上传**：向示例运行目录上传图片/文档，脚本可直接按文件名引用处理
- 🕘 **运行历史**：自动记录每次运行（示例/参数/耗时/退出码/输出），上限 500 条，支持重跑（参数回填表单）与清空，数据存本机 userData
- ⭐ **示例收藏**：卡片星标收藏，「只看收藏」与全部筛选维度可叠加
- 🏷️ **多维筛选**：自动从 import 抽取第三方库标签 + 元数据标签，运行状态（成功/失败/未运行）× 主题 × 质量分 × 标签 × 收藏 × 全文搜索可组合，纯函数引擎配单元测试；排序/主题/质量分偏好跨启动记忆
- ✨ **AI 代码解释**：详情页内一键调用 DeepSeek 兼容 API 流式解释（中文 Markdown，可自定义 Base URL 与模型名），API Key 仅存本机 userData，不进前端/git/日志；首次外发先确认，同意状态可在「设置 → 代码外发」复核与撤回
- 🗂 **存储治理**：设置中心「存储」分区显示工作区占用/上限/含资产条目、旧版缓存占用；两档清理（干净清理 / 全部清理，各自确认）与旧版缓存一键回收
- 🛟 **失败恢复**：sidecar 崩溃/熔断给出恢复出口（重启引擎 / 查看日志）；参数解析失败显式报错并可重试；运行失败可从输出直接进入「装依赖重跑」

## 界面

2026-09 完成大厂级重设计（A/B 双轨，设计稿见 `docs/redesign-visual-baseline.md`）：

- **三层绑定**：`data-platform`（mac 原生几何 / Windows 自绘标题栏）× `data-theme`（深/浅/跟随系统）
  × `data-accent`（跟随系统强调色 / 品牌色），token 单一来源 `src/renderer/src/theme.css`；
- **组件层自研**：皮肤不依赖样式化 UI 框架（Element Plus 已移除），弹窗 / 下拉 / 命令面板的行为底座
  为无头原语库 reka-ui（焦点圈定、Esc、外点关闭、aria 由它承担），图标单一 Lucide，字重仅 400/500/600，
  对比度按 AA 门禁（`scripts/check_contrast.py`）；表面色阶为统一品牌主题（Linear 表面阶梯，深/浅两套）。
- **走查脚本化**：`npm run smoke` 在真实窗口里量几何/令牌/交互语义（壳、画廊、详情、全局层、首启、
  资源链路、存储与失败恢复、性能段）——不是靠人眼看截图。
