# ROADMAP

> 版本节奏见 README 功能列表；本节 1 记录当前待办，节 2 记录已交付内容（按 tag 与提交对账）。

## 1. Now / Next（当前待办）

基线：HEAD `2668eb5`，示例总量 **1496**（topics 1286 / tools 163 / projects 47）。

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
- [ ] 校正过期基线文档（`docs/audit-examples.md` 仍写 1187 条）

### P1 — 质量缺口

- [ ] Vue 层 `store.ts`（1086 行）与 22 个组件零测试
- [ ] `scripts/` 下 23 处历史 lint 债（F401 / F811 / E402 / E731 / E741 / F841），
      多为一次性生成脚本；CI 门禁暂只覆盖 `app tests`
- [ ] `requirements.txt` 含无效包名 `ternary-new`（PyPI 不存在，由迁移脚本的
      `IMPORT_TO_PKG` 猜测产生），会让 `pip install -r requirements.txt` 整体失败；
      需在 `scripts/gen_shared_requirements.py` 加拒绝名单后重新生成
- [ ] 示例运行回归：补全 CI 中的 Electron 冒烟 job（仅 macOS 验证过）

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
