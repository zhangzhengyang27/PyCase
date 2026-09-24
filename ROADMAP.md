# ROADMAP

> 版本节奏见 README 功能列表；本节 1 记录当前待办，节 2 记录已交付内容（按 tag 与提交对账）。

## 1. Now / Next（当前待办）

基线：架构勘察时 HEAD `2668eb5`；示例总量 **1496**（topics 1286 / tools 163 / projects 47）。

### P0 — 工程健康度（2026-09-24 架构勘察提出）

- [x] 删除死入口与构建残留：根目录 PyQt6 旧入口 main.py（其依赖的 app/ui 全历史从未存在）、
      electron 目录下 CJS 旧主进程 main.js、两份 egg-info、venv 里两份失效 editable
      安装、5 个空产物目录
- [x] 修复被截断的 `.github/workflows/ci.yml`（原文件缺 `name/on/jobs`，CI 从未生效）
- [x] 安装 pytest，让 `tests/*.py` 真正可执行
- [x] 补装 `requirements.txt` 中声明但缺失的 `selenium` / `playwright` / `ffmpeg`
- [x] 清理死渲染层：`src/` 中 14 个旧 TS 模块（ai/app/args-form/assets/detail/facets/
      favorites/gallery/history/main/monaco-editor/output/runner/state）与 `src/renderer/vue/`
      脚手架、旧原型页 `renderer/index.html`、误复制的 21M `node_modules`；
      同步收窄 `electron.vite.config.ts` 的 MPA 入口、`tsconfig.web.json` 改为覆盖 Vue 组件
- [x] 统一版本号：pyproject 与 sidecar 自报版本对齐到 `0.10.0`（与 Electron 一致）
- [x] 校正过期基线文档：`docs/audit-examples.md` 重跑审计改写为当前数据
      （1496 个示例 / 5 条问题记录，其中 4 条依赖缺失是本地模块误报），
      旧的 1187 条时点记录压缩为「历史快照」存档段

### P1 — 质量缺口

- [x] 补上 Vue 层 `store.ts` 的测试：新增 `tests/test_store.mjs`（**93 项断言**），
      经 renderer-loader 加载真实 store.ts —— `vue` 从 node_modules 真实加载（真响应式），
      仅以替身替换 `./toast` 与 `./src/sidecar-client` 两个副作用依赖；覆盖画廊/工具箱
      互补池、排序、收藏、筛选重置、芯片反向应用、下钻范围互斥、loadAll 成功/失败/
      脏偏好拒绝、搜索防抖、facet 计数口径、运行超时持久化、高危确认门、必填门禁。
      顺带修掉加载器的缓存命中 bug（返回 module 外壳而非 module.exports）
- [x] 27 个 Vue 组件补齐渲染层测试：新增 Vitest + jsdom 组件测试基建
      （`electron-prototype/electron/vitest.config.ts`、`vitest.setup.ts`、`npm test`），
      5 个 spec 覆盖全部组件共 **236 项断言**（base 8 个 / cards 7 个 / browse 3 个 /
      detail 4 个 / panels 5 个）。与 `tests/*.mjs` 分层：纯逻辑模块走 `node --test`
      （零 bundler），需要 SFC 编译与 DOM 的组件走 Vitest；Vitest 与 `electron.vite.config.ts`
      共用 `@vitejs/plugin-vue`，编译链与真实构建一致。jsdom 的四处缺口
      （`PointerEvent` / `IntersectionObserver` / `Blob.arrayBuffer` / `matchMedia`）
      与跨用例自动卸载统一在 setup 兜底，单个 spec 不再重复补桩。
      有效性经**变异测试**验证：向 5 个 spec 各注入一处真实回归，5/5 全部被捕获
- [x] `requirements.txt` 含无效包名 `ternary-new`（`ternary_new` 是科研绘图示例内嵌的
      本地模块，被迁移脚本误猜成 PyPI 包，会让整份 requirements 安装失败）：
      已加入 `gen_shared_requirements.py` 的 `EXCLUDED_PKGS` 并重新生成，
      46 个包 `uv pip install --dry-run` 全部可解析
- [x] 清完 `scripts/` 的 23 处 lint 债（F401 / F811 / E402 / E731 / E741 / F841），
      CI 门禁恢复为 `ruff check app scripts tests`；重跑 gen_bulk / gen_real_projects
      生成的 JSON 与提交版逐字节一致，确认属纯重构
- [x] 示例运行回归：修好 CI 中的 Electron 冒烟 job（原 45s 超时导致**必然失败**）
      **① 冒烟链路已本地跑通（首次）**：`[smoke] 全部通过` / `EXIT=0`，7 个探针全绿
      （sidecar ready → ping → list_examples 1496 个/14 集合 → history → favorites →
      facets → gallery → ai → 用户集合导入/删除）。
      本地复现需要两个环境绕行（**与代码无关，是运行环境限制**）：
      - `ELECTRON_RUN_AS_NODE` 必须清掉。该变量被设置时 Electron 以纯 Node 运行，
        `require('electron')` 返回二进制路径字符串 → `electron.app` 为 undefined →
        主进程首行 `electron.app.isPackaged` 直接抛错。
      - 嵌套沙箱内 Chromium 起不来（`Failed to initialize sandbox` + GPU/network
        service 崩溃 → 渲染进程 `crashed`），需 `--no-sandbox --disable-gpu` 才跑得动。
        正常 CI runner 无此问题。
      **② 45s 超时是硬缺陷（已修）**：实测（1496 个示例）首次 `list_examples` ≈17s、
      `import_examples` ≈13s、每次 `delete_example` ≈13s —— 仅「导入/删除」三步就 40s+，
      再叠加渲染层加载与末尾 8s 观察窗，**在原样跑通之前必然超时**。
      已把超时改为默认 180s 并支持 `SMOKE_TIMEOUT_MS` 覆盖；同时给超时信息加上
      「卡在哪一步」（原来只报一句「45s 内未完成」，无从定位）。
      **③ 超时会留下残留（已修一半）**：`import_examples` 建的 `user_examples/smoke_import.json`
      与物化缓存 `.json_examples_cache/smoke_*` 会留在开发机上，而 `user_examples/`
      在 `.gitignore:41` 里 → **CI 与 `git status` 都看不见，会持续累积**。
      已加 `finally` 兜底删除本步导入的示例（删空后集合文件自动移除）。
      ⚠️ 仍未覆盖「deadline 硬超时」路径：`app.exit(1)` 直接退出，async 流程的 `finally`
      不会执行——彻底解决需把 deadline 改成可中断信号，属后续改进。
      **④ CI 无 `.venv` 也能跑**：`electron-smoke` job 不建 `.venv`，
      `resolveSidecarCommand` 回退 `python3`；索引链路（`_ensure_store`）纯标准库，
      不依赖 opencv/pygame 等重包，故 `list_examples` 可用。
      **未验证项**：`macos-latest` runner 上的实际表现（本地沙箱只能跑到「渲染层崩溃」，
      本机是靠 `--no-sandbox` 绕行才完整跑通的）

### P2 — 组件测试期间发现的问题（4 项均已核读源码 / 实测确认，且已全部修复）

- [x] **`CommandPalette` 键盘双触发（已修）**：`onMounted` 用捕获阶段在 window 注册
      `onKeydown`，搜索框上又挂了 `@keydown="onKeydown"`；面板打开即聚焦搜索框，于是
      同一个按键被处理两次（捕获一次 + 目标一次）。实测：在聚焦的搜索框上按一次 ↓，
      高亮从 0 跳到 **2**（正常应为 1）；Enter / Esc 各 emit 两次 `close`，⌘+Enter 会发起
      两次 `runFromCard`。已删掉搜索框上的冗余监听（window 捕获监听本就覆盖全文档），
      并补两条按**真实派发目标（input）**断言的回归用例——此前的用例把事件派发到
      window，恰好绕过了 input 那一环，所以一直没暴露
- [x] **`ToolboxView` 空态死路（已修）**：页头（搜索框 + 收藏筛选 + 排序）整块位于 `v-else`
      分支内，工具池为空时被 `AppEmpty` 整体替换。用户在工具池打开「只看收藏」且尚无收藏时
      会落进空态，而关闭该开关的唯一入口已随页头消失——被永久困住。已把空态挪进滚动层内部，
      页头始终保留；并把空态文案改为按成因归因（有搜索词→提示改搜索词；`favOnly` 且无收藏
      →提示点星标恢复），不再一律怪搜索词。补 4 条用例，含「点星标即恢复列表」的端到端验证
- [x] **`DetailPage` 状态徽章口径不一致（已修）**：卡片用 `statusBadge` 显式排除
      `runnable` / `risky`，`utils.ts:66-68` 注释亦写明「runnable 无需徽章、risky 由高危徽章
      承担」；但 `DetailPage` 直接以 `v-if="runStatusLabel(ex.run_status)"` 判定，而
      `runStatusLabel` 对 `runnable` 返回「可运行」、对 `risky` 返回「高危」——详情页因此多出
      一个卡片刻意不显示的「可运行」徽章，`risk_high` 示例还会出现两个「高危」。
      已改为与卡片同源的 `statusBadge` computed，并补用例覆盖两个分支
- [x] **`store.requiredArgsMissing` 必填门禁是死代码（已修）** —— 这条比原先记的更严重，
      根因有两层，实测确认：
      **① `null` / `undefined` 口径错（致命）**：sidecar 的 `parse_args` 对「没有默认值」的
      参数序列化为 `"default": null`（不是省略字段、也不是 `undefined`），而门禁判的是
      `a.default === undefined` —— 对真实数据**永远为假**。也就是说整条必填门禁
      （`ArgsForm` 的提示文案与字段红框、`runFromCard` 的拦截）从未生效过，全是死代码。
      实测：`printf '{"jsonrpc":"2.0","id":1,"method":"parse_args",...}' | .venv/bin/python
      electron-prototype/sidecar/server.py` → `"default": null`。
      **② 门禁读不到表单值**：表单值在 `ArgsForm` 局部的 `values.list` 里，store 侧不可见，
      故门禁无法随用户填入而重算——修好①之后若不解决②，会让必填示例**永久无法运行**。
      **交互语义（用户裁定）**：必填项**可以有默认值**——`required` 只表示「必须有一个值」，
      不表示「必须由用户输入」；有 `default` 即视为已满足。
      **修法**：`store.ts` 新增 `isRequiredArgUnset()`（同时判 `undefined` 与 `null`，
      并排除 `store_true` / `store_false` 布尔开关）；新增 `registerArgsValidator()`，
      由 `ArgsForm` 反向注册一个读 `values.list` 的校验器（`shallowRef` 持有，
      组件卸载时注销），`requiredArgsMissing` 优先用它、未注册时回退纯 spec 判定；
      `runFromDetail` 补上门禁。`ArgsForm.isMissing` 同步修掉 `null` 口径。
      **回归护栏**：组件层 +2 条（`default: null` 按缺失处理；必填有默认值不拦不标红），
      store 层 +13 条（无默认值/`null`/有默认值/布尔/非必填/校验器优先与注销/
      `runFromCard` 两个分支）。**变异测试 4/4 全部被捕获**：① 去掉 store 的 `null` 判定
      ② 去掉 `ArgsForm` 的 `null` 判定 ③ 去掉反向注册的校验器 ④ 去掉 `runFromDetail` 门禁

## 2. Done（已交付，按 tag 与提交对账）

### v0.10.0（画廊/工具箱信息架构重设计，tag v0.10.0）

- **画廊两级浏览**：落地页改为主题分区总览（头区统计 + 五大主题横向卡片带 +
  「还有 N 个」下钻卡），点进分区进入筛选浏览态——从 1187 条无差别平铺改为
  「先看结构、再看条目」（分区成员互斥分配，`src/renderer/src/overview.ts` 纯函数）。
- **浏览态结果条升级**：返回总览 + 范围标题 + 可移除筛选芯片（当前生效筛选一目了然，
  `src/renderer/src/filter-chips.ts`）+ 排序 + 网格/清单密度切换（两视图各自记忆持久化）。
- **工具箱清单化**：34 个工具从卡片墙改为一行一工具的清单默认形态，补齐排序。
- **侧栏降噪**：五个筛选组可折叠（主题/质量分默认收起 + 组头激活数徽标），标签 TopN 15→10。

### v0.10.0 后续（工具箱分区 / 画廊互斥 / 宽侧栏，已提交待发版）

- **工具箱按工具项目分区**：`source_dir` 字段贯通（models → loader → sidecar → 渲染层类型），
  34 个工具按目录结构分 8 区（7 个项目 + 独立工具），区头 Lucide 图标 + 卡片网格，
  大组默认预览 6 张一键展开（`toolbox-groups.ts` 纯函数 + 单测；取代 v0.10.0 的清单形态）。
- **画廊与工具箱互斥**：画廊池排除 `tools`，总览分区 / 浏览筛选 / 侧栏 facet / 状态栏计数
  同口径；冒烟新增「画廊池 = 全集 − tools」探针，收藏链路取样改为画廊可见示例。
- **导航栏重设计**：顶部挤压条 → 176px Linear 式宽侧栏——图标文字同行、行式激活态
  （卡片底胶囊 + 左缘强调条动画）、⌘K 键位提示、品牌行嵌入红绿灯头区、状态栏兼作拖拽面。

### v0.9.0（示例库与应用解耦，tag v0.9.0）

- **导入自己的示例**：顶栏三步导入向导（选目录 → 预览 → 导入），用户集合存于
  `userData/user_examples/`，与内置库并存展示；id 对全库去重防冲突；依赖自动猜测
  （与可运行性判定同源的模块索引）。
- **用户集合管理**：详情页删除（内置集合受保护）、原子写回、物化缓存清理、索引即时重建。
