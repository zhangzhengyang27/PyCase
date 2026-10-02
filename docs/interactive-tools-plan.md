# 交互工具化规划：独立工具 → 页面工具（2026-10-02 调研）

> 状态：调研结论 + 框架设计 + 波次计划。首个实例「日期计算器」已交付（2026-10-02，
> 规格/计划见 `docs/superpowers/`），本文档是该模式的推广规划。
> 数据基线：工具箱全量 163 个独立工具（`category: tools`，全部无 `source_dir` 项目归属）。

## 1. 结论摘要

163 个工具**不适合全部转**，按「输入输出是否为文本/参数、是否纯计算、是否有教学联动价值」分三档：

| 档 | 数量 | 处置 |
|---|---|---|
| A·立即可做 | **23 个交互工具**（吸收现有 51 个条目） | schema 框架逐波落地，落地一批退役一批变体 |
| B·需文件管道基建 | ~20 个 | 先建 `pickFile` 桥 + 管道组件，第三波启动 |
| C·保持运行形态 | ~92 个 | 不页面化（系统/文件系统/网络/Git/一次性脚本） |

**关键架构前置**：先抽象「交互工具通用框架」（schema 驱动），再批量注册工具。
逐个手写专属页（日期计算器模式）不可持续。

## 2. 可行性判据（A 档准入标准）

1. 输入是文本/数值/选项（**不是**文件树、目录扫描、网络请求）
2. 输出是文本/结构化结果，页面可渲染（二进制产物 → B 档）
3. 计算逻辑 TS 可等价实现，或（库依赖型）可由 sidecar adhoc 运行承担计算、页面只做采集与展示
4. 无 GUI 依赖（tkinter）、无危险操作（粉碎/删除/覆写真实文件）
5. 代码联动有教学价值（`pyCode` 模板能生成与页面结果互相印证的脚本）

## 3. 逐工具清单

### 3.1 A-1 组：bulk_basics 同构变体归并（33 → 6，最高优先）

与日期计算器完全同构的故事：一组同构变体 → 一个交互工具。落地一组、退役一批
（含守卫计数锚点同步，参照 date-diff 退役流程）。

| 交互工具 | 吸收变体 | 核心字段 | 结果 / 对拍要点 |
|---|---|---|---|
| 温度换算器 | 温度×3（日常/极端/精密） | 数值、源单位(C/F/K)、目标单位、精度档 | 主结果+全部单位对照表； Kelvin 锚点换算口径；黄金用例含 -40C=−40F、绝对零度边界 |
| 进制转换器 | 进制×5 | 数值(字符串入)、源进制(2-36)、目标进制 | 各进制一览行；大数用 BigInt；与 `int(s, base)` / `format(n, 'b')` 对拍；非法字符报错文案 |
| 凯撒密码 | 凯撒×4 | 文本、移位数(-∞~∞ 归一 mod 26)、加/解密 | 密文主结果+移位轮盘预览；`chr/ord` 与 Python 对拍；保留大小写与非字母跳过口径 |
| 文本折行 | 折行×5 | 文本、列宽、断词策略(硬切/单词) | 折行结果+行数；`textwrap`（width/replace_whitespace）对拍——textwrap 口径要逐条钉 |
| 回文判定 | 回文×3 | 文本 | 判定+归一化过程（忽略大小写/标点/空白）；预处理正则与 Python 一致 |
| 月历打印 | 月历×6 | 年、月 | 月历网格（周一起始）；**与日期计算器日历 Tab 重叠——建议作为其增强而非独立页**（双月日历已有，加「任意月浏览」入口） |

退役联动：33 个条目 → 0，总条目 1488 → 1455；`test_g1_dataset_index_golden` 等三处锚点随波更新。

### 3.2 A-2 组：devtools/showcase 纯文本工具（17 个）

| 交互工具 | 来源条目 | 计算位置 | 核心字段 | 结果 / 备注 |
|---|---|---|---|---|
| 正则测试器 | 正则测试器 | 前端(JS RegExp) | pattern、flags(多选)、样本文本 | 匹配列表+分组表+高亮预览；JS/Python 正则方言差异声明（lookbehind 等），复杂语法走「运行」验证 |
| JSON 格式化校验 | JSON 格式化校验 | 前端(JSON.parse/stringify) | 输入、缩进(2/4/Tab)、动作(格式化/压缩) | 输出+错误行列号；错误定位口径与 Python json 模块不必逐字一致，声明即可 |
| JSON → dataclass | JSON → dataclass | 前端 | JSON 样本、类名、可选类型严格度 | 生成的 dataclass 代码；类型推断规则（str/int/float/bool/list/嵌套/None 判定）逐条钉 |
| CSV ↔ JSON 互转 | CSV ↔ JSON | 前端 | 输入、方向、分隔符、表头有无 | 类型推断口径（数字/布尔/null）；引号转义（RFC 4180）对拍 |
| JWT 解码器 | JWT 解码器 | 前端(atob) | token | header/payload 解码 JSON + 过期时间标注；**不验签**（明确声明，验签属安全功能另立） |
| 时间戳转换器 | 时间戳转换器 | 前端 | 秒/毫秒、日期时间输入 | 双向+本地/UTC 双显示；时区口径=本地（与 date-core 一致） |
| UUID/短 ID 生成器 | UUID/短 ID | 前端 | 模式(uuid4/短ID/序列号)、数量、大小写 | 批量列表+复制全部；uuid4 用 crypto.getRandomValues，与 Python uuid4 格式对拍（仅格式） |
| 哈希校验器（文本） | 哈希校验器 | **sidecar** | 文本、算法多选 | WebCrypto 缺 MD5 → 走 sidecar adhoc 运行 hashlib，输出进结果区；页面只采集 |
| 密码强度检查 | 密码强度检查 | 前端 | 密码、可见开关 | 强度评分+弱口令模式命中列表；评分规则与 Python 版逐条对拍 |
| gitignore 生成器 | gitignore 生成器 | 前端 | 项目类型多选 | 拼装模板文本；模板表与 Python 版共享同一来源（抽成 JSON 共享文件） |
| .env 校验器 | .env 校验器 | 前端 | .env 文本、.env.example 文本 | 缺失/多余/空值键三列表；解析口径（注释/引号/export 前缀）对拍 |
| 颜色转换器 | 颜色转换器 | 前端 | HEX/RGB/HSL 任一 | 三格式互转+色块预览+对比度(对白/黑)提示；舍入口径对拍 |
| 科学单位换算 | 科学单位换算 | 前端 | 量纲、源/目标单位、数值 | 换算系数表共享 JSON；与 Python 字典同源 |
| Markdown 目录生成 | Markdown 目录生成 | 前端 | markdown 文本、层级范围 | TOC 文本+锚点转写规则（GitHub 风格）对拍 |
| 文本规范化 | 换行符规范化 + 缩进规范化（2 条目归并） | 前端 | 文本、换行符目标、缩进(空格/Tab 互转+宽度) | 归并声明写入描述；逐项口径简单 |
| 批量查找替换（文本） | 批量查找替换 | 前端 | 文本、查找(支持正则开关)、替换、选项(大小写/整词) | 结果+命中计数；正则方言同正则测试器声明 |
| 密码生成器 | showcase 密码生成器 | 前端 | 长度、字符集多选、排除易混淆 | 生成+强度联动（复用强度检查的评分函数） |

### 3.3 B 档：文件管道型（~20，基建后启动）

图片类 10：批量缩放/格式转换/裁剪比例/缩略图拼贴/水印/主色调/亮度对比度/圆角边框/图片信息/GIF 系(2)。
Office 类 10：Excel 读取/样式/公式/排序/数据校验/两表对比/透视/跨表关联、PDF 拆分/文本提取、图片转 PDF、CSV↔Excel、SQLite↔Excel。

**前置基建**（估 1 个特性周期）：
- 桥新增 `pickFile(filters)`（现缺；`pickDirectory`/`saveTextFile`/`downloadResultImage` 已有）
- `FilePipelinePanel.vue`：选文件 → sidecar 运行（adhoc 或上传资产到示例工作区）→ stdout/产物预览 → 下载
- 产物落盘走示例工作区（`ensure_workspace`），下载走 `downloadResultImage` 泛化版

### 3.4 C 档：不做（~92，保持现有运行卡片）

- 文件系统操作 17：大文件 TopN/重复清理/空目录清扫/目录同步/粉碎器/压缩解压/临时清理/目录树/变更监听/快速查找/批量重命名/自动分类/重复查找/体积报告/打包备份/日志轮转/敏感粉碎
- 网络 9：网速/IP/端口/HTTP 头/可用性监控/URL 批量体检(联网部分)/DNS/网页正文/站点监控
- 媒体(ffmpeg 依赖) 11：视频压缩/格式转换/提取音频/裁剪/音量/截图/合并/去音轨/音频转码/批量转码/视频转GIF
- 系统只读 6：进程 Top/磁盘仪表/电池/系统信息 + Git 2（依赖当前仓库）
- 业务一次性 10：migrated.json 全部（课程课件脚本）
- 其余演示/GUI 类：番茄钟、记账本、密码保险库（安全语义复杂）、站点监控等

## 4. 通用交互工具框架（核心设计）

### 4.1 schema 类型（`renderer/src/interactive-tools.ts` 扩展）

```ts
export type FieldType = 'text' | 'textarea' | 'number' | 'select' | 'checkbox' | 'color'

export interface FieldSpec {
  key: string
  label: string
  type: FieldType
  default?: string | number | boolean
  options?: Array<{ value: string; label: string }>   // select
  placeholder?: string
  required?: boolean
  width?: 'full' | 'half'
  help?: string
}

export interface ToolResult {
  primary?: { value: string; unit?: string }              // 大数字主结果
  rows?: Array<{ label: string; value: string; copy?: boolean }>
  text?: string                                            // 大段文本结果（折行/TOC/diff）
  list?: string[]                                          // 批量生成结果
  error?: string                                           // 输入不合法的引导文案
}

export interface InteractiveToolSchema {
  id: string                    // 'interactive:temp-convert'
  title: string
  description: string
  tags: string[]
  fields: FieldSpec[]
  /** 前端计算型必填：输入 → 结构化结果（纯函数） */
  compute?: (v: Record<string, string | number | boolean | undefined>) => ToolResult
  /** 计算位置：frontend（默认）| sidecar（页面只采集，结果由运行输出承担） */
  computeVia?: 'frontend' | 'sidecar'
  /** 代码抽屉模板（复用 py-codegen 模式：纯函数拼接，产物可直接 python3 运行） */
  pyCode: (v: Record<string, string | number | boolean | undefined>) => string
}
```

### 4.2 组件与路由

```
components/interactive/
├── InteractiveToolPage.vue   # 读 schema：动态表单 + 结果区 + 复用 CodeDrawer
├── ToolField.vue             # FieldSpec → 控件（复用 base 组件与现有样式 token）
└── ToolResultPanel.vue       # ToolResult → primary/rows/text/list 渲染 + 复制
src/interactive-tools.ts      # schemas: InteractiveToolSchema[]（注册表数组化）
src/store/interactive.ts      # 扩展：currentToolId + 各工具输入值的持久化（会话内）
```

- App.vue 路由扩展：`interactive:<tool>` 前缀不变，页面组件按 schema 分派
  （`date-calculator` 保持专属页，其余走 `InteractiveToolPage`）。
- 卡片/搜索/收藏/置顶分组机制**零改动**（注册表条目仍映射为 `VExample`）。

### 4.3 一致性对拍（推广黄金用例模式）

- 每工具一份黄金用例段（共享 `interactive-golden.json` 或按工具分文件）：
  输入 → 期望 `ToolResult` 关键字段 + 期望 Python 脚本 stdout。
- pytest 侧跑「schema → pyCode → 真执行 → 输出比对」（复用 Task 7 的 adhoc 通道）；
  vitest 侧跑 `compute` 比对。两侧同一份 JSON。
- 对拍不了的（JS/Python 正则方言、WebCrypto 缺 MD5），在工具描述里显式声明差异口径。

### 4.4 参考实例：温度换算器 schema（落框架时的对齐基准）

```ts
{
  id: 'interactive:temp-convert',
  title: '温度换算器',
  description: '摄氏/华氏/开尔文互转，含全单位对照与绝对零度边界校验。',
  tags: ['换算', '交互工具'],
  fields: [
    { key: 'value', label: '温度值', type: 'number', required: true, placeholder: '36.6' },
    { key: 'from', label: '源单位', type: 'select', default: 'C',
      options: [{ value: 'C', label: '摄氏 ℃' }, { value: 'F', label: '华氏 ℉' }, { value: 'K', label: '开尔文 K' }] },
    { key: 'precision', label: '小数位', type: 'select', default: '1',
      options: [{ value: '0', label: '整数' }, { value: '1', label: '1 位' }, { value: '2', label: '2 位' }] }
  ],
  compute: ({ value, from, precision }) => {
    // Kelvin 锚点：C→K +273.15；F→K (v-459.67)×5/9；K→其余反解；K<0 → error 引导
    // 返回 primary=目标单位结果，rows=三单位对照
  },
  pyCode: ({ value, from, precision }) =>
    `# float 直算 + f-string 位数，print 三单位对照`
}
```

## 5. 波次计划

| 波 | 内容 | 退役联动 | 验收 |
|---|---|---|---|
| W1 | 框架落地（schema 类型 + 3 组件 + 路由分派）+ A-1 六组归并中先做 3 组（温度/进制/凯撒） | bulk_basics −12（1488→1476） | 框架含温度参考实例；golden 对拍双端绿；变体退役流程复刻 date-diff |
| W2 | A-1 剩余 3 组（折行/回文/月历并入日期计算器） | −21（→1455，bulk_basics 工具清零） | 同上 |
| W3 | A-2 前 9 个（正则/JSON 系/时间戳/UUID/颜色/单位） | 无（devtools 条目保留，运行卡与交互页并存） | 每工具 schema+对拍 |
| W4 | A-2 后 8 个 + 框架体验回看 | — | — |
| W5+ | B 档基建（pickFile/FilePipelinePanel）→ 图片类试点 | — | 单独立项 brainstorm |

**A-2 不退役原条目**：devtools 工具的 CLI/参数化形态仍有运行教学价值，交互页是「新增一个更好的入口」，两者并存（卡片徽章可加「也有交互页」联动）。

## 6. 风险与不做清单

- **框架过度设计**：schema 只覆盖上面字段类型与 ToolResult 四种渲染，遇到表达不了的工具（如日期计算器的日历）就做专属页，**不强塞框架**
- **对拍成本失控**：sidecar 对拍用例每工具 ≤10 条，只钉核心口径
- **YAGNI 不做**：工具间联动/组合管道、用户自定义 schema、结果持久化、i18n、主题化结果导出
- **安全**：交互工具不触碰真实文件系统与网络（B 档的文件读写全部走 sidecar 工作区沙箱）
