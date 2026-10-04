# ARCHITECTURE

> 本文是架构的**活文档**（2026-10-04 起）。历史设计过程见 `docs/redesign-plan.md`（已冻结于 09-30）
> 与 `docs/superpowers/specs/`；里程碑索引与发版口径见 [ROADMAP.md](ROADMAP.md)。

PyCase 是 **Electron 壳 + Python sidecar** 的桌面应用：内置 415 条 Python 示例（画廊 285 + 工具箱 130 个
交互工具），可浏览、筛选、编辑，并在共享虚拟环境里隔离运行、实时查看输出与产物图。

## 分层

```
electron-prototype/
├── electron/src/main/        Electron 主进程：窗口/IPC/生命周期/特权协议(pycase-img://)
│   └── smoke.ts              冒烟/E2E 走查索具（SMOKE_TEST=1 时加载，产品路径零依赖）
├── electron/src/renderer/    Vue 3 + Tailwind 4 渲染层
│   ├── store/                分域状态（gallery/detail/date-run/ai…）
│   ├── components/           画廊/详情/工具页组件 + __tests__/（vitest 全量）
│   └── …/tool-schemas-*.ts   交互工具注册表（schema 驱动：fields + compute + pyCode）
├── sidecar/server.py         Python 后端：纯标准库 asyncio，stdio JSON-RPC（25 方法，协议见 shared/protocol.json）
└── shared/                   main 与 renderer 共享的纯函数（protocol/paths/result-images/gallery-counts）

app/                          Python 契约层：contract_store（清单→运行工作区）/ facts（烘焙）/ 安全 / 评分 / 环境
json_examples/                清单（15 个 *_examples.json）+ 派生语料源文件 + facts.json（烘焙产物）
topics/ projects/             原始示例源码树与阅读资产（真实 .py，编辑保存写回这里）
scripts/                      生成器（全部带退役对账守卫）/ 数据门禁 / gate.sh / verify_corpus.py
```

## 数据流（单一真相）

```
15 个清单（元数据 + id）+ topics/ 真实源码树
        │  python -m app.facts_cli bake
        ▼
json_examples/facts.json   ←—— 唯一的派生真相（条目指纹/theme/imports/deps/static）
        │                        ⚠️ 任何「计数钉点」必须从它派生，禁止手写（见下）
        ▼
sidecar contract_store ──IPC──► renderer store ──► 画廊/工具箱/详情/交互页
```

- **启动零写盘**：运行/上传先进按需工作区（`.json_examples_cache/v2/`），编辑保存写回真实文件并留快照。
- **依赖单环境**：仓库根一份 `.venv`，`requirements.txt` 由 `python -m app.facts_cli requirements`
  从清单聚合生成（字节级可复现）；首启装包优先读 `requirements.lock.txt`（`uv pip compile`，CI 新鲜度门禁）。

## 钉点纪律（2026-10 体检后的硬规矩）

数字钉点散落手写曾导致语料大转向后 CI 四处必红。现状：

| 钉点 | 来源 | 机制 |
|---|---|---|
| 打包示例数 | facts.json items | `build_sidecar.py::_expected_examples()` 运行时派生 |
| smoke 分区计数 | facts.json theme 分布 | `shared/gallery-counts.ts` 运行时派生（与 sidecar 双实现互查） |
| 语料/清单规模 | facts.json | pytest 守卫（guard_data / guard_protocol / 语料扫描下限） |
| 版本号 | `VERSION` | `scripts/sync_version.py --check` |

**新增任何「条数」类断言，一律从 facts.json 派生或走运行时不变量（成员合计=池大小），不写死数字。**

## 交互工具框架（schema 驱动）

- `InteractiveToolSchema`：声明式 fields（含函数形态：字段随类型联动）+ compute（TS 即时计算或
  `computeVia: sidecar` 走 Python）+ pyCode（生成可运行脚本）。统一由 `InteractiveToolPage` 渲染：
  表单 → 运行 → 结果区（primary/rows/text/list 四形态）+ 代码抽屉 + 产物图预览。
- **映射路由** `interactive-mapping.ts`：工具箱 CLI 卡标题 → 交互页 id；映射完整性有测试钉住
  （引用的页面必须已注册、类型必须存在于实验室选项）。
- **实验室注册表模式**：同构变体一律进实验室的类型注册表（viz-lab 30 图族×12 数据模式、pil-lab 32、
  cv-lab 24、turtle-lab 29、sciviz-lab 15、basics-lab 7 主题、games-lab 5 玩法），不新建独立页面。
- **归并唯一形态**：画廊 = 家族卡（变体折叠），无「切回全量」入口；favOnly（收藏/历史）可浮出具体变体。

## 两大既定语义模式

1. **自播种**：示例「无输入可运行」——目录缺图/缺数据 → 先生成演示数据再继续原逻辑
   （COLLECT/SEED_FILE 序章、sciviz 程序化网格）。分辨三类语义再动手：需数据（播种）、
   需参数（占位引导）、GUI 阻塞（弹窗，既定行为）。
2. **真实执行取证**：静态可解析 ≠ 可运行。「可运行」的判定 = 真跑 exit 0 且产物非空/有 stdout。
   常备工具 `scripts/verify_corpus.py`（415 条全量真跑 + 分类 + 豁免清单）。

## 门禁矩阵

| 档位 | 内容 | 入口 |
|---|---|---|
| fast（日常迭代） | ruff + tsc/vue-tsc + eslint/stylelint + prettier + vitest + 9 份 mjs | `scripts/gate.sh fast` |
| full（推送/发版前） | fast + mypy + 5 个数据门禁 + pytest | `scripts/gate.sh full` |
| smoke | electron-vite build + 壳/画廊/详情/全局层走查（跑前 `pkill -9 -f PyCase/electron` 清孤儿） | `npm run smoke` |
| CI | 上两 job + smoke job + 双平台 packaging | `.github/workflows/ci.yml` |

工程经验与复犯率高的坑沉淀在 [docs/playbook.md](docs/playbook.md)——改代码前先读它的「高频陷阱」节。
