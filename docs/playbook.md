# 工程手册（Playbook）

> 本文沉淀 2026-09/10 三轮全面体检 + 交互化战役中**复犯率高、代价大**的经验。
> 架构与数据流见 [../ARCHITECTURE.md](../ARCHITECTURE.md)；只讲「怎么做不出错」。

## 交付纪律：每批改动三件事缺一不可

1. **注册可达**：新页面/工具 grep 导入链确认进 registry；死代码连编译期引用检查都不触发
   （历史上四个 SCHEMAS 数组全库零导入、整批页面不可达）。
2. **测试钉住结构**：映射表引用的每个 id 必须已注册、类型必须存在于实验室选项——用测试断言结构，
   而非人眼。
3. **真实执行取证**：pyCode/语料逐条真跑 + **产物内容级校验**（图验非均匀、turtle 数画布端点、
   stdout 非空）。「文件存在」级校验抓不出空图/空产物；「超时阻塞 + stderr 干净」验不出空窗
   （turtle dot=零长度 line，图元数少≠没画全，要数端点）。常备工具：`scripts/verify_corpus.py`。

## 数字钉点：一律派生，禁止手写

语料 1464→395 大转向当晚，手写计数（README/CI/smoke/release.yml）四处必红。规矩：
- 条数类断言从 facts.json 派生（`build_sidecar._expected_examples`、`shared/gallery-counts` 先例）；
- 结构类断言用不变量（分区成员合计=池大小），不随增删漂移；
- facts 冒出新主题/新键时，派生方必须显式失败点名（棘轮），不许静默跳过。

## 自播种：先分清三类语义再动手

用户跑不出结果 ≠ 工具坏了：
- **需数据** → 自播种（生成演示数据 → 继续原逻辑），比删示例或报错引导都好；
- **需参数** → 占位引导文案（UI 不可达的越档输入不算 bug）；
- **GUI 阻塞** → 弹窗是既定行为（turtle/pygame/cv2.imshow），验证时按超时+源码 import 识别。

## 命令与管道陷阱（反复踩）

- **管道吞退出码**：`cmd | tail` 的 `$?` 是 tail 的——必须 `set -o pipefail` 或直接读输出文本判定。
  build_sidecar 缺装、vitest 单测失败都曾被 exit 0 假象盖过。
- **mjs 纯函数测试不在 pytest/vitest 射程内**：本地容易漏跑，用 `scripts/gate.sh` 汇总跑。
- **批量文本改造用 Node 脚本（.cjs）**，别用 python heredoc：三引号嵌套、TS1005、锚点漂移三次未命中
  的教训。prettier 会重排源码——锚点用运行时提取的文本，不用旧源码记忆。
- **.format 模板的花括号**：字面花括号 `{{}}`；过度转义 `{{top}}` 会 NameError；非 format 模板里
  `{{}}` 反而是 set-dict TypeError。
- **改坏文件直接 `git checkout --` 恢复**，比手工修补可靠。
- **工作目录漂移**：cd 过一次后相对路径全错——每条命令显式带绝对路径。
- **后台任务/长命令**：验收必须读输出文本本身，超时 ≠ 通过。

## 生成器与派生文件

- **所有清单生成器重跑前有退役对账守卫**（`scripts/generator_guard.py`）：复活/丢失条目即中止，
  `--force` 显式豁免。新增条目走「改生成器源码 + 人工复核差异」，不靠重跑兜底。
- **派生文件必须在最后一轮 prettier 之后重生成**，否则新鲜度门禁再红。
- 生成器 JSON 与 prettier 循环打架时，新鲜度测试用**语义比对**（json.loads 相等），锁内容不锁格式。

## 测试与验收

- vitest 用 esbuild 不查类型——**改 spec 后必须重跑 typecheck**，否则误报全绿。
- vi.mock 工厂引用外部绑定必须 `vi.hoisted`（TDZ 曾让整个 spec 静默脱队）。
- store 状态跨用例泄漏三连：favOnly、toolSearchQuery 防抖、分类过滤——用 `getTestApi().resetViewFilters()`。
- 文本断言 ≠ 可见性：`textContent` 匹配也可能被画成背景色（隐形墨水事故），视觉验证查计算样式/截图。
- 交付归并类改动时，同时汇报**三个口径**：页面数、入口/卡片数、库里对象数——归并度偏差立刻显形。

## 工作流纪律

- 逐任务提交在「用户逐节批准的既定工作流内」视为已授权；**工作流外一律停在工作区等确认**；
  推送永不擅自（GitHub 需走代理 `git -c http.proxy=http://127.0.0.1:7890 push`）。
- facts.json 是原子烘焙产物：改任何语料/清单文件都必须重烘后一起提交，无法与无关改动拆分——
  动 facts 前先看工作区有没有别人的未提交改动。
- 跑 smoke 前先清孤儿 Electron：`pkill -9 -f PyCase/electron`，否则首屏预算假阳性。
