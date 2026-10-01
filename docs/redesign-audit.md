# 大厂级重设计 · 现状审计报告（M0）

> 状态：M0 已对稿（2026-09-29）｜ 日期：2026-09-29 ｜ 基线提交：8847a16
> 方法：三路并行只读取证（渲染层工艺 / Python 与工程化 / 产品与信息架构）+ 关键证据逐项实测复核。
> 未启动应用、未运行测试套件；运行类结论来自代码与仓库内历史实测记录。
> 配套文档：[重设计方案](redesign-plan.md)

**证据图例**（行号为审计时点实测）：
R = electron-prototype/electron/src/renderer；M = electron-prototype/electron/src/main；
S = electron-prototype/sidecar；E = electron-prototype/electron；A = app；T = tests。

**级别定义**：P0 = 不修不成立（正确性 / 数据 / 信任 / 交付阻塞）；P1 = 显著低于大厂基线；P2 = 一致性与打磨。

## 0. 事实基线

| 项 | 数值 | 项 | 数值 |
|---|---|---|---|
| 示例规模 | 1496 条 / 14 集合 | 物化缓存 | 3151 项 / 118MB（无淘汰） |
| Python 行数 | 16454（app 2189 / sidecar 1390 / scripts 11327 / tests 1548） | 主进程 + preload | 1137 行 |
| 渲染层 | 28 个 .vue + store.ts 1112 行 | 组件/契约测试 | 5 spec 3767 行；pytest 106 例 |
| CI | 3 job（python / frontend / electron-smoke），无打包/覆盖率 | git tag | 0 个 |
| 版本 | 0.10.0（package.json / pyproject / sidecar 三处手写） | RPC 面 | 15 方法 / 7 通知 |

## 1. 产品与信息架构（A1–A12）

| 编号 | 级别 | 问题（含影响） | 证据 |
|---|---|---|---|
| A1 | P0 | 首次运行环境准备是黑箱：预热仅打 stderr，UI 只有连接状态，用户数分钟内无反馈、被误判卡死；README 承诺"后台预热"界面上不可见 | S/server.py:411-418、1173-1185；R/App.vue:254-261；README.md:30 |
| A2 | P0 | 失败路径无出口：崩溃/熔断事件主进程已发出但渲染层零订阅者；参数解析失败被静默吞掉后参数区整块消失（用户以为无参数，运行必败） | M/index.ts:194,878,894；R/App.vue:139-143；R/store.ts:536-542；R/components/DetailPage.vue:211 |
| A3 | P0 | 缺依赖无修复路径：只有一句 tooltip，全应用无"安装依赖"动作，错误以原始 traceback 呈现——"体检"承诺不闭环 | R/src/utils.ts:98-99；R/components/OutputPanel.vue:50 |
| A4 | P1 | 术语漂移：导航「示例画廊」vs 页头/空态「示例库」；「运行状态」与「可运行性」共用"运行"二字；返回按钮写死「返回画廊」 | R/App.vue:98；R/components/GalleryOverview.vue:50；R/components/FilterSidebar.vue:81-95；R/components/DetailPage.vue:117 |
| A5 | P1 | 搜索口径三套（侧栏=名称/标签/代码、⌘K=名称/标题/标签、运行器=仅名称），无处解释差异 | R/components/FilterSidebar.vue:191；R/components/CommandPalette.vue:117；R/store.ts:697-701 |
| A6 | P1 | 偏好散落四处（主题循环键、AI/超时/安全弹窗、viewPrefs、收藏历史各自为政）；帮助与快捷键页不存在 | R/App.vue:58-59,86-90；R/components/AISettingsModal.vue:104-184；R/store.ts:249-272 |
| A7 | P1 | 「可运行%」以静态推定当卖点展示；唯一实跑基线显示真实通过率 51.7%（该基线自标过期） | R/components/GalleryOverview.vue:16-20；R/store.ts:181-183；docs/run-status-baseline.md:27-36；docs/json-examples.md:141 |
| A8 | P1 | 收藏/清空语义分裂：clearFilters 不含收藏与搜索词、clearAllFilters 才含；两处"清空"文案与行为不同 | R/store.ts:290-299 vs :344-350 |
| A9 | P1 | 数据安全与可恢复性：AI 外发仅一次性 confirm、同意状态不可复核；内置示例编辑永久回写，无备份/diff/恢复 | R/store.ts:1042-1050；R/store.ts:577-606 |
| A10 | P2 | 文档漂移：README 仍写 v0.7 界面（实际 0.10.0）；README 描述的全局历史/导出 .log 无实现；7 份 docs 过期（json-examples.md 路径与数字失真）；electron-prototype/README 仍是原型期内容 | README.md:101,89-94；docs/{regression-baseline,run-status-baseline,release,v0.6-ia-redesign,json-examples,frontend-refactor-plan,v0.5-plan}.md；electron-prototype/README.md |
| A11 | P2 | 交付面缺位：git tag 0 个而 ROADMAP 声称按 tag 对账并引用不存在的 tag；release.md 停在 v0.5.0；无更新机制 | 实测 git tag=0；ROADMAP.md:3,122,142；docs/release.md:9-23 |
| A12 | P2 | 运行器→详情断链（仅提示文字）；工具箱继承画廊隐藏筛选但无芯片/侧栏、无清除入口 | R/components/RunnerView.vue:95-97；R/store.ts:114-121；R/components/GalleryView.vue:87 vs R/components/ToolboxView.vue:119-202 |

## 2. 视觉与交互工艺（B1–B12）

| 编号 | 级别 | 问题（含影响） | 证据 |
|---|---|---|---|
| B1 | P0 | 设计系统双真值且旧真值已死：electron 目录下 tailwind.config.js 无 @config 引用、content 不含 .vue（实测死文件）；R/src/style.css 163 行无 import 且令牌值与真值分叉——重设计最易"改错文件" | E/tailwind.config.js:5-8；R/src/style.css；真值仅 R/src/theme.css |
| B2 | P0 | 幽灵依赖：element-plus ^2.14.6 声明在案但 src 内 0 引用、无主题覆写层、构建产物 0 命中；白付约 60MB 且误导协作者 | E/package.json:78；实测 grep 0 命中；R/components/base/AppModal.vue:2、R/toast.ts:1（自建替代注释） |
| B3 | P1 | 图标三套语言并存：主题 emoji vs Lucide 线性图标 vs 文本字形（▶ ↑↓ ↵）；toolbox-groups.ts 的 icon 字段无消费者 | R/src/themes.ts:19,32,42,52,62；R/src/overview.ts:125-128；R/components/FilterSidebar.vue:59-65；R/components/CommandPalette.vue:183-185；R/src/toolbox-groups.ts:10,16-25 |
| B4 | P1 | 字重自相矛盾：注释声明只用 400/500，实测 47 处非标字重（590×31、510×11、650×5）——苹方合成加粗发虚；无字重阶梯 token | R/App.vue:182-183；实测 47 处 / 20 文件 |
| B5 | P1 | 主题靠 9 处手写 light 覆盖块 + 组件层约 68 处颜色字面量（.vue 11 / .ts 25 / main.css 32）；透明度 5 档无层级语义 | R/main.css:92-202；R/components/ToolboxView.vue:63-74；R/src/overview.ts:84-97 |
| B6 | P1 | 原生 window.confirm 三处打断（未保存切换、关闭详情、AI 首次外发告知）——已有带焦点陷阱的 AppModal 却不用 | R/store.ts:520,554,1044（实测） |
| B7 | P1 | 静默失败：偏好/收藏/超时写盘失败被 catch 吞掉零感知；错误态仅画廊/工具箱有，详情/运行器/历史/资源面板全无 | R/store.ts:817-818,271,281,636,659；R/components/GalleryView.vue:72-75；R/components/ToolboxView.vue:127-130 |
| B8 | P1 | 表单错误与输入框无 ARIA 关联（error 无 id、input 无 aria-describedby），读屏只知"非法"不知原因 | R/components/base/BaseInput.vue:55-78；R/components/ArgsForm.vue:160,167 |
| B9 | P2 | 焦点与对比度：选中态阴影压过全局焦点环（作者自认）；命令面板关闭不归还焦点；quaternary 文字只对单一底色验证（卡片面 4.48:1 ✗、收藏星标 2.89:1 ✗） | R/main.css:95-97；R/components/CommandPalette.vue:97-104；R/src/theme.css:43,111；R/components/ExampleCard.vue:69 |
| B10 | P2 | 壳层硬编码 macOS：pl-[72px] 红绿灯留白写死；仅 darwin 设 hiddenInset（注释自认未实测其它平台）；渲染层拿不到平台信息 | R/App.vue:160；M/index.ts:297；E/src/preload 无 platform |
| B11 | P2 | 首帧白闪与底色三处真值（无 backgroundColor/ready-to-show；index.html / main.ts / App.vue 各写一份 #08090a） | M/index.ts:289-304；R/index.html:13；R/main.ts:14；R/App.vue:76 |
| B12 | P2 | 性能面：5000 行输出全量 v-for 无虚拟化；1496 条靠 content-visibility 缓解无回收；动效时长 120/150/180 三套并存、--duration-fast 零引用 | R/store.ts:409；R/components/OutputPanel.vue:50；R/components/ExampleCard.vue:39 |

## 3. 代码与工程化（C1–C13）

| 编号 | 级别 | 问题（含影响） | 证据 |
|---|---|---|---|
| C1 | P0 | 打包/发布不可复现且未入 CI：dist 依赖手工产物（electron-prototype/sidecar-dist 实测不存在）、identity:null 未签名未公证、依赖不锁版本、CI 无打包 job——升级即黑盒 | E/package.json:14,23-27,56；.github/workflows/ci.yml（3 job 无打包）；docs/release.md:9-23；scripts/gen_shared_requirements.py:15 |
| C2 | P0 | 启动期在事件循环内同步全量物化 1496 条（首次 list_examples ≈17s，仓库内实测记录），且缓存无治理：实测 3151 项 / 118MB、无淘汰、UI 无清缓存入口 | S/server.py:268-280；A/json_examples.py:96-118,190-254；ROADMAP.md:61；缓存实测 |
| C3 | P0 | 示例子进程无生命周期兜底：sidecar 无 signal/atexit/start_new_session/killpg（实测 0 命中），退出仅 stdin EOF 或 SIGTERM——长任务在应用退出后继续跑、重开再起一份 | S/server.py:1161-1162；M/index.ts:1001-1004；实测 grep 0 |
| C4 | P1 | 桥协议健壮性：错误码被丢弃（前端无法按类型分支）、readyQueue 崩溃时不清导致重启后"幽灵请求"、超时定时器不 clear | M/index.ts:249-251,90,163-183,233-236,276-282 |
| C5 | P1 | 前端工程门禁为零：无 eslint/prettier/editorconfig（实测）；两个 tsconfig 均 noImplicitAny:false；src 内 21 处 any（sidecar-client 占 11） | tsconfig.web.json:9、tsconfig.node.json:9；R/src/sidecar-client.ts 等 |
| C6 | P1 | Python 门禁缺口：ruff 只查 app/scripts/tests——不含 sidecar 1209 行；无 mypy/pyright；16 处 noqa: BLE001 是死指令；venv_manager 类型骗值（str\|None 赋 False） | pyproject.toml（无 [tool.ruff]）；.github/workflows/ci.yml:31；S/server.py、S/ai_service.py；A/venv_manager.py:77,89 |
| C7 | P1 | 分层渗漏与双实现：run_status.compute_run_status 纯函数只被测试调用、生产另有一份实现；安全白名单机制从未接线；sidecar 穿透 store._module_index 私有属性 | A/run_status.py:153-177 vs A/json_examples.py:415-446；A/security.py:184-193、A/quality.py:34；S/server.py:156,902 |
| C8 | P1 | 安全扫描 fail-open：扫描异常即返回"无高危"，运行前高危确认弹窗静默消失——应 fail-closed 或"未知态" | A/json_examples.py:382-383 |
| C9 | P1 | 重复常量与过期注释：SKIP_DIRS×3、VALID_PKG_RE×3、版本号×3、"1349 个示例"注释（实际 1496） | A/importer.py:22、A/json_examples.py:41、scripts/gen_shared_requirements.py:50；A/json_examples.py:185 等 |
| C10 | P1 | 测试非 hermetic：模块级 fixture 直接物化到仓库根缓存、回写测试直接改写 json_examples 真相源（中断即污染唯一真相源） | T/test_core.py:23-37,61-73（已读码确认） |
| C11 | P1 | 关键路径零测试：运行/超时/取消（S/server.py:397-536）、search、ai_service（181 行）全无用例；CI 无覆盖率门禁 | 实测 T/ 无 run_example 等命中；.github/workflows/ci.yml |
| C12 | P2 | 死代码与可诊断性：app/utils.py 三函数、venv_manager.clear_all_cache 无调用；logger 的 log_file 无调用——打包版无日志文件可回收 | A/utils.py:7,37,42；A/venv_manager.py:125；A/logger.py:20 |
| C13 | P2 | 依赖安装与协议面：venv 逐包起 51 次 subprocess、无版本无哈希；RPC 方法名 4 处手写；上传限额 20MB vs 128MB 分裂；run timeout 无校验可传负数 | A/venv_manager.py:193-196；S/server.py:1094-1110；M/index.ts:348 vs S/server.py:1150；S/server.py:303-306 |

## 4. 红线：必须保留的资产（重设计不得破坏）

1. 原子写纪律 + 负向测试（tmp + os.replace；含"中途写失败不损坏集合"用例）。
2. 对不可信示例的安全姿势：env 白名单、上传禁覆盖 .py、物化越界防护、下载白名单、sandbox + contextIsolation、Key 不回传明文。
3. 崩溃自愈细节：sidecar 熔断退避重启、陈旧事件防竞态、后台 Task 强引用。
4. 键盘/读屏投入：全局焦点环、AppModal 焦点陷阱与归还、卡片 role/tabindex、详情页 tablist 三件套。
5. 三态覆盖与空态归因（骨架 / 错误带重试 / 按成因文案）。
6. 动效无障碍（prefers-reduced-motion 全局降级）与 token→Monaco 取色链。
7. 画廊两级浏览 + 可移除筛选芯片 + 偏好持久化；⌘K 命令面板；详情页一站式闭环 + AI Key 不外泄。
8. 测试网与治理：组件测试 + 变异测试验证；docs 防漂移脚本；ROADMAP 以证据记录问题。

## 5. 复核记录（逐项实测，2026-09-29）

element-plus src 内 0 引用 ｜ git tag 0 个 ｜ 物化缓存 3151 项 / 118MB ｜ electron-prototype/sidecar-dist 不存在 ｜
store.ts 1112 行 ｜ 非标字重 47 处 / 20 文件 ｜ window.confirm 3 处（store.ts:520,554,1044）｜
noImplicitAny:false（两个 tsconfig）｜ CI 3 job、ruff 覆盖不含 sidecar ｜ sidecar 无 signal/atexit/killpg ｜
tests 无 run_example 用例 ｜ main.css 9 处 light 覆盖块 ｜ MAX_OUTPUT_LINES=5000（store.ts:409）｜
GalleryView 有错误态+重试（:74,:98）｜ main.ts 仅 import main.css（style.css 确为孤儿）。

## 6. 后续变更注记（画廊改造）

> 上文表格与复核行号均为 **审计时点（2026-09-29，基线 8847a16）实测**，作为历史记录保留，不随代码演进更新。

- 上文引用 `R/components/GalleryOverview.vue` 的 A3/A4 等条目对应组件已退役：画廊由「落地总览（五大主题横向卡片带 + 「还有 N 个」下钻）→ 下钻浏览态」改为 **单态浏览 + 侧栏二级分区菜单**——「示例画廊」nav 项下挂「全部示例」+ 15 个分区（5 主题 / 8 标签组 / 项目 / 其它，各带计数与选中态），点选即在右侧响应式网格中浏览。
- 页头（统计 chips + 浏览全部 / 我的收藏）抽为 `GalleryHeader.vue`，观感不变。
- 三维下钻（`activeTheme` / `activeSectionTags` / `activeCategory`）收敛为单一 `activeSectionKey`，并新增筛选引擎 `sections` 维度（OR 语义，经既有 `sectionKeyOf` 派生），`countBaseQuery` 剥离之。
- v2（同日迭代）：并排筛选栏（`FilterSidebar.vue`）退役，筛选维度收进工具栏下拉（收藏开关 + 主题 / 可运行性 / 质量分 / 运行状态 / 标签 + 排序 + 密度，flex-wrap 换行）；关键字搜索框保留在工具栏行 2（写 `searchQuery`，元数据 + 源码双通道）。上文引用 `R/components/FilterSidebar.vue` 的 A4/A5/B3 条目行号因此失效，语义已由 `BrowseToolbar.vue` / `TagFilterSelect.vue` 承接。
- 走查口径同步：画廊池 = 1333 条（`examples` 1496 中剔除 `category === 'tools'` 的 163 条），分区成员合计对的是池大小而非全库。
