# 交互工具 W1 实施计划：框架 + 温度/进制/凯撒（2026-10-02）

> 上游设计：`docs/interactive-tools-plan.md` §4（框架）与 §3.1（A-1 组）。执行方式：内联
> （子代理配额 2026-10-06 重置前不可用）。分支 `feat/interactive-tools-w1`。

## 任务分解

### T1 CodeDrawer 通用化（props 化）
- `CodeDrawer.vue`：删除对 date-core/py-codegen/store-interactive 的直接依赖，`code` computed
  迁出到调用方；新增 props `{ code: string; runId: string }`（Vue 自动解包 ref，watch
  `() => props.code` 做 setValue）。日期页传入自己的 computed 与 `DATE_CALC_ID`。
- 更新 `code-drawer.spec.ts`（props 传入代码）与 `date-page.spec.ts`（mock date-run 不再必要，
  但 drawer 经 props 接收 code——保持 monaco mock）。
- 验收：vitest 全量绿；typecheck 绿。

### T2 schema 类型 + 注册表数组化 + store 扩展
- `interactive-tools.ts`：新增 `FieldType/FieldSpec/ToolResult/InteractiveToolSchema` 类型
  （见规划文档 §4.1，`color` 类型本次不实现）；`toolSchemas: InteractiveToolSchema[]`
  （先空数组）；`interactiveToolItems` 改为派生 = 日期卡 + `toolSchemas.map(schemaToCard)`；
  `getToolSchema(id)` 查找函数。
- `store/interactive.ts`：新增 `toolValues = ref<Record<string, Record<string, FieldValue>>>({})`、
  `toolValueOf(id, schema)`（首次按 defaults 初始化）、`currentToolId`。
- 测试：注册表派生（卡片字段映射、无 run_status）、toolValueOf 初始化与回写。

### T3 动态表单与结果面板
- `components/interactive/ToolField.vue`：FieldSpec → 控件（text/textarea/number/select/checkbox），
  复用 base 组件与现有样式 token；required 缺失标红。
- `components/interactive/ToolResultPanel.vue`：ToolResult → primary 大数字 / rows 行列表(可复制) /
  text 文本块 / list 列表 / error 引导文案；空结果不渲染。
- 测试：字段渲染与 v-model 回写、必填标红、结果四种形态渲染与复制。

### T4 InteractiveToolPage + 路由分派
- `InteractiveToolPage.vue`：页头（返回/标题/徽章）+ 动态表单 + 结果区（compute 实时）+
  CodeDrawer（code=schema.pyCode(values)，runId=tool.id）。
- App.vue：interactive 分支内 `selectedId === DATE_CALC_ID ? DateCalculatorPage : InteractiveToolPage`。
- 测试：打开温度工具 → 表单默认值出结果；输入联动；返回清 selectedId。

### T5-T7 三个工具 schema + 双端对拍
每个工具 = schema（fields + compute + pyCode）+ 黄金用例（共享
`src/renderer/src/tool-golden.json`，分 `temp/base/caesar` 段）+ vitest（compute 逐条 + pyCode
片段断言）+ pytest（`tests/test_tool_golden.py` 参考实现逐条比对同一 JSON——复刻
test_date_core_golden 模式）。

- **温度**：Kelvin 锚点（C→K +273.15；F→K (v−459.67)×5/9；K→其余反解）；K<0 → error；
  输出 primary=目标单位 + rows=三单位对照；精度 0/1/2 位。
- **进制**：输入为字符串（防大数精度丢失），校验字符集合法；TS BigInt ↔ Python int(s,base)
  对拍（黄金含 >2^53 用例）；输出 rows=2/8/10/16 进制对照 + 自选目标进制。
- **凯撒**：mod 26 归一（负数/大数移位）；保留大小写、非字母跳过；输出 primary=密文/明文 +
  rows=加密与自解密验证；黄金含空串、纯符号、大小写混合。

### T8 变体退役（12 条：temp×3 + base×5 + caesar×4）
- `gen_bulk_examples.py` 删三个 add 块（含退役注记，复刻 date-diff 写法）。
- 外科手术：`bulk_basics.json` 从 HEAD 恢复后摘 12 条（94→82，总 1488→1476），删 12 个 .py，
  facts 重烘；**勿跑全量重生成**（migration --apply 会被 facts.json 预存噪音 error 拦）。
- 守卫锚点 1488→1476（test_guard_data G1 金标含 docstring、test_manifest_v2 总数、
  test_guard_protocol 列表 total）。
- 验收：pytest 全绿；git diff 仅落退役文件。

### T9 全局门禁 + 收尾
vitest / lint / format:check / typecheck / pytest / smoke 全绿；格式化产物随收尾提交。

## 验收口径（对应规划文档 W1）
框架 + 温度参考实例可走通（表单→结果→代码→运行）；三工具黄金对拍双端绿；
bulk_basics 工具 33→21，总条目 1488→1476；原 12 个变体条目从库中消失、交互卡片可搜索可收藏。
