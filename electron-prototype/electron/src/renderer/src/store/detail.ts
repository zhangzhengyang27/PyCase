// detail.ts：详情页与运行生命周期域。
//
// 职责：选中示例、参数表单（注册式接线）、Monaco 编辑与保存、运行发起与高危确认、
// 输出面（detail/runner 两个 sink）、运行事件订阅与历史记录、历史重跑。
import { computed, reactive, ref, shallowRef } from 'vue'
import { pushToast } from '../../toast'
import * as FilterEngine from '../filter-engine'
import { invalidateExampleVisual } from '../overview'
import { api, type SidecarError } from '../sidecar-client'
import { examples } from './catalog'
import type { ExampleDetail, VersionInfo } from '../../../../../shared/protocol'
import { recordHistory, runHistory, runTimeout, setSkipHighRiskConfirm, skipHighRiskConfirm } from './prefs'
import { assets, loadAssets } from './assets'
import { interactiveRouteForExample, vizVariantOf } from '../interactive-mapping'
import { isInteractiveId } from '../interactive-tools'

export interface ArgSpec {
  name: string
  flags: string[]
  dest: string
  type: string
  default?: unknown
  help?: string
  choices?: unknown[]
  required?: boolean
  action?: string
  is_positional?: boolean
  nargs?: string | number | null
  metavar?: string | null
}

export interface OutputLine {
  text: string
  cls: 'base' | 'system' | 'error' | 'success'
}

export interface OutputImage {
  url: string
  name: string
}

const MAX_OUTPUT_LINES = 5000
// 详情态
export const selectedId = ref<string | null>(null)
export const originalCode = ref('')
export const isDirty = ref(false)
export const saving = ref(false)
export const currentArgs = ref<ArgSpec[]>([])
export const argsLoading = ref(false)
// 参数回填令牌（历史重跑）：ArgsForm 在参数装载完成后消费
export const pendingBackfillTokens = ref<string[] | null>(null)
/** 参数解析失败信息（非空时参数区显式报错并可重试，不再静默空参数区） */
export const argsError = ref('')

/**
 * 应用内确认弹窗（替换原生 window.confirm；未保存改动守卫、AI 首次外发告知共用）。
 * 原生 confirm 是系统模态：样式与应用割裂、自动化走查驱动不了、
 * 也带不了"继续编辑/放弃修改"这类明确的按钮语义。
 */
export const confirmPrompt = ref<{
  title: string
  message: string
  confirmLabel: string
  action: (() => void) | null
} | null>(null)

/** 请求确认：用户点确认后执行 action（点取消什么都不做）。 */
export function requestConfirm(
  message: string,
  action: () => void,
  options?: { title?: string; confirmLabel?: string }
): void {
  confirmPrompt.value = {
    title: options?.title ?? '确认操作',
    message,
    confirmLabel: options?.confirmLabel ?? '继续',
    action
  }
}

/** 用户在确认弹窗上的选择：ok=true 执行挂起的动作。 */
export function resolveConfirm(ok: boolean): void {
  const pending = confirmPrompt.value
  confirmPrompt.value = null
  if (ok && pending?.action) pending.action()
}
/** 依赖安装进行中（详情页「安装依赖」按钮的 loading 态） */
export const installingDeps = ref(false)

// ---------------------------------------------------------------------------
// 编辑历史（可恢复编辑）：版本列表 / 预览内容 / 还原
// ---------------------------------------------------------------------------
export const versions = ref<VersionInfo[]>([])
export const versionsLoading = ref(false)
/** 当前预览的历史版本（含内容，用于与当前代码做行级差异） */
export const versionPreview = ref<{ ts: string; code: string } | null>(null)
export const restoringVersion = ref(false)

export async function loadVersions(): Promise<void> {
  const id = selectedId.value
  if (!id) return
  versionsLoading.value = true
  try {
    const result = await api.listVersions(id)
    if (selectedId.value === id) versions.value = result.versions
  } catch (err) {
    console.error('[versions] 读取编辑历史失败:', err)
  } finally {
    versionsLoading.value = false
  }
}

export async function previewVersion(ts: string): Promise<void> {
  const id = selectedId.value
  if (!id) return
  try {
    const result = await api.readVersion(id, ts)
    if (selectedId.value === id) versionPreview.value = { ts: result.ts, code: result.code }
  } catch (err) {
    pushToast('error', `读取版本失败: ${(err as Error).message}`)
  }
}

/** 还原到某历史版本：写回真实文件（sidecar 侧还原前也会留快照，可反复回退）。 */
export async function restoreVersion(ts: string): Promise<boolean> {
  const id = selectedId.value
  if (!id || restoringVersion.value) return false
  restoringVersion.value = true
  try {
    await api.restoreVersion(id, ts)
    // 还原后编辑器与"原件"基线都要跟上，避免显示成"有未保存修改"
    const detail = await api.getExample(id)
    if (selectedId.value !== id) return false
    originalCode.value = detail.code
    isDirty.value = false
    editor?.setValue(detail.code)
    pushToast('success', '已还原到该版本')
    await loadVersions()
    versionPreview.value = null
    return true
  } catch (err) {
    pushToast('error', `还原失败: ${(err as Error).message}`)
    return false
  } finally {
    restoringVersion.value = false
  }
}

// 运行态（同窗口同时刻至多一个运行；输出汇固定 detail，运行器视图步骤 4 迁移）
export const isRunning = ref(false)
export const currentRunId = ref<string | null>(null)
export const currentRunMeta = ref<{ id: string; name: string; args: string[]; startedAt: number } | null>(null)
export const runStatusText = ref('就绪')
/** 运行超时（秒）：超时强制终止；设置弹窗「运行」分区可调，存 runPrefs */
export const runSink = ref<OutputSurface>('detail')
export type OutputSurface = 'detail' | 'runner'
export type OutputDot = 'idle' | 'running' | 'success' | 'error'
export interface SurfaceState {
  lines: OutputLine[]
  images: OutputImage[]
  dot: OutputDot
  truncated: boolean
}
const surfaces = reactive<Record<OutputSurface, SurfaceState>>({
  detail: { lines: [], images: [], dot: 'idle', truncated: false },
  runner: { lines: [], images: [], dot: 'idle', truncated: false }
})
export function surfaceState(s: OutputSurface): SurfaceState {
  return surfaces[s]
}
// run_id 回包到达前产生的早期输出缓冲（旧实现此处会丢行，这里补上）
let _earlyOutputBuffer: OutputLine[] = []

export const selectedExample = computed(() => examples.value.find((e) => e.id === selectedId.value) || null)

// ---------------------------------------------------------------------------
// 画廊路由上下文（交互页 ↔ 原示例双向可达）
// ---------------------------------------------------------------------------
/** 经画廊路由进入交互页时被点的那张卡片；从工具箱/命令面板直开交互页时为 null */
export const interactiveSourceId = ref<string | null>(null)
/** 路由携带的预选值（实验室页的类型 / viz 变体的数据模式等）；InteractiveToolPage 落页时消费并清空 */
export const pendingPreset = ref<{ pageId: string; values: Record<string, string> } | null>(null)
export const detailHistory = computed(() =>
  selectedId.value ? runHistory.value.filter((h) => h.id === selectedId.value).slice(0, 20) : []
)
/**
 * 参数是否「既没有默认值、也没有用户填的值」。
 *
 * 注意 sidecar 对**没有**默认值的参数返回 `"default": null`（不是省略、也不是 undefined），
 * 所以这里必须同时判 null 与 undefined —— 只判 `=== undefined` 会让整个必填门禁永远为假
 * （曾经如此：提示文案、字段红框、runFromCard 的拦截全是死代码）。
 */
function isRequiredArgUnset(a: ArgSpec): boolean {
  const noDefault = a.default === undefined || a.default === null
  return !!a.required && noDefault && a.action !== 'store_true' && a.action !== 'store_false'
}

// 表单值（用户已填的内容）存在 ArgsForm 组件局部的 reactive 里，store 侧读不到，
// 因此由表单反向注册一个「按当前值判断是否仍缺必填项」的校验器。
// 未注册时（例如详情页未挂载表单）回退到纯 spec 判定。
const _argsValidator = shallowRef<(() => boolean) | null>(null)

export function registerArgsValidator(fn: (() => boolean) | null): void {
  _argsValidator.value = fn
}

/**
 * 是否存在「必填但没有值」的参数。
 * 「有默认值」即视为已满足——必填不等于「必须由用户输入」（见 isRequiredArgUnset）。
 */
export const requiredArgsMissing = computed(() =>
  _argsValidator.value ? _argsValidator.value() : currentArgs.value.some(isRequiredArgUnset)
)

function appendOutput(text: string, cls: OutputLine['cls'] = 'base', surface: OutputSurface = 'detail'): void {
  const state = surfaces[surface]
  const lines = state.lines
  if (lines.length >= MAX_OUTPUT_LINES) {
    const removeCount = Math.floor(MAX_OUTPUT_LINES * 0.1)
    lines.splice(0, removeCount)
    if (!state.truncated) {
      state.truncated = true
      lines.unshift({ text: `[系统] 输出超过 ${MAX_OUTPUT_LINES} 行，已自动截断，仅保留最近的输出`, cls: 'system' })
    }
  }
  lines.push({ text, cls })
}

function resetOutputSurface(surface: OutputSurface): void {
  const state = surfaces[surface]
  state.lines = []
  state.images = []
  state.truncated = false
  state.dot = 'running'
}

export function clearSurface(surface: OutputSurface): void {
  const state = surfaces[surface]
  state.lines = []
  state.images = []
  state.truncated = false
  state.dot = 'idle'
  if (!isRunning.value) runStatusText.value = '就绪'
}

/** 打开详情页：返回参数解析 Promise（卡片「运行」据此决定自动运行或引导填参） */
export async function openDetail(
  id: string,
  skipGuard = false,
  opts: { forceDetail?: boolean } = {}
): Promise<ArgSpec[]> {
  const ex = examples.value.find((e) => e.id === id)
  if (!ex) return []
  // 未保存的编辑不得静默丢弃：切换到不同示例前需要确认
  if (!skipGuard && selectedId.value && selectedId.value !== id && isDirty.value) {
    // 不在 openDetail 里同步询问：改为渲染层弹窗 + 用户确认后重放本次切换
    requestConfirm('当前示例有未保存的修改，放弃并打开另一个示例？', () => void openDetail(id, true, opts), {
      title: '放弃未保存的修改？',
      confirmLabel: '放弃修改'
    })
    return []
  }
  // ---- 画廊路由收口：凡交互页已覆盖能力的条目（CLI 工具标题表 / bulk_viz 图族表），
  // 打开动作一律直达交互页面——画廊/清单/收藏/历史/命令面板全走这里。交互 id 自身与
  // forceDetail（卡片「运行」、参数重试、「查看原示例源码」回链）不路由。
  if (!isInteractiveId(id) && !opts.forceDetail) {
    const route = interactiveRouteForExample(ex)
    if (route) {
      interactiveSourceId.value = ex.id
      const preset: Record<string, string> = {}
      if (route.type) preset.type = route.type
      const variant = vizVariantOf(ex)
      if (variant?.mode) preset.mode = variant.mode
      pendingPreset.value = Object.keys(preset).length ? { pageId: route.page, values: preset } : null
      selectedId.value = route.page
      return []
    }
  }
  interactiveSourceId.value = null
  pendingPreset.value = null
  if (selectedId.value !== id) {
    selectedId.value = id
    // 源码不在这里取：契约 v2 起列表项不含 code，只能按 id 单独拉（loadSourceCode）。
    // 先置空而不是回落占位串——「请选择示例」占位只允许出现在未选中任何示例时。
    originalCode.value = ''
    isDirty.value = false
    resetOutputSurface('detail')
    runStatusText.value = '就绪'
    assets.value = []
    void loadSourceCode(id)
  } else if (originalCode.value === '' && !isDirty.value) {
    // 同一 id 重复打开（双击卡片 / Cmd+K 再次选中当前示例）：源码还没到位就补发一次，
    // 覆盖「首次装载失败后重新打开可重试」与「在途时重复打开」两种情形。
    // 有内容或有未保存编辑时一律不补发——否则 watch(originalCode) → setValue 会顶掉用户正在编辑的内容。
    void loadSourceCode(id)
  }
  // 参数解析与资源列表并行；带序号防过期响应（旧版竞态的响应式等价物）
  const seq = ++_openDetailSeq
  argsLoading.value = true
  argsError.value = ''
  const argsPromise = (async () => {
    try {
      const result = await api.parseArgs(id)
      if (seq !== _openDetailSeq) return []
      currentArgs.value = result.args || []
    } catch (err) {
      console.error('解析参数失败:', err)
      if (seq !== _openDetailSeq) return []
      currentArgs.value = []
      // 显式失败态：用户看到"解析失败 + 重试"，而不是"这个示例没有参数"
      const code = (err as SidecarError)?.code
      argsError.value = `${(err as Error).message}${typeof code === 'number' ? `（错误码 ${code}）` : ''}`
    } finally {
      if (seq === _openDetailSeq) argsLoading.value = false
    }
    return currentArgs.value
  })()
  void loadAssets(id)
  return argsPromise
}
let _openDetailSeq = 0
// 源码装载的序号**独立于** _openDetailSeq：只在真正发起一次装载时才自增。
// 若复用 openDetail 的共享序号，同一 id 重复打开（走不到切换分支、不会发起新装载）
// 也会把序号推高，于是那唯一一次 getExample 的回包被自己的守卫判为过期而丢弃，
// 源码永远停在空串——重复点击同一张卡片就会把代码块饿死成空白（与本次要修的缺陷同症状）。
let _sourceSeq = 0
/** 在途装载的目标 id：同一 id 的重复调用直接忽略，既不重复请求也不作废在途那一次。 */
let _sourceInflightId: string | null = null

/**
 * 装载示例源码（详情页源码的唯一来源）。
 *
 * 契约 v2 起 `list_examples` 不再下发源码（全库只为元数据序列化），源码必须由
 * `get_example` 按 id 单独读取。渲染层若继续从列表项取 `ex.code`，恒为空串 →
 * Monaco 回落到「请选择示例」占位注释 → 用户看到的就是「代码块全空白」。
 *
 * 过期判定用本域自己的序号：快速切换示例时，先发后到的响应不得覆盖当前内容。
 * 失败不静默：置空 + toast，让用户看到「加载失败」而不是「这个示例是空的」。
 */
async function loadSourceCode(id: string): Promise<void> {
  if (_sourceInflightId === id) return
  const seq = ++_sourceSeq
  _sourceInflightId = id
  try {
    const detail: Partial<ExampleDetail> | null = await api.getExample(id)
    if (seq !== _sourceSeq || selectedId.value !== id) return
    // 在途期间用户已在编辑器里敲过字（isDirty 为真）：跳过写入，保住用户输入——
    // 否则 watch(originalCode) → setValue 会把刚敲的内容整段覆盖掉。
    // 代价（已评估可接受）：这种情况下源码永不落地，originalCode 停在 ''、isDirty 保持 true。
    // 保存链路不受影响（saveExample 写的是编辑器当前内容）；要重新拿到真源码须先保存或放弃
    // 本次修改——切换示例会被未保存守卫拦下确认，同 id 重开的补发条件也要求 !isDirty。
    // 只守成功分支：失败分支仍要置空 + toast，不能被脏标记吞掉。
    if (isDirty.value) return
    originalCode.value = detail?.code ?? ''
    isDirty.value = false
  } catch (err) {
    if (seq !== _sourceSeq || selectedId.value !== id) return
    console.error('[detail] 加载源码失败:', err)
    pushToast('error', `加载源码失败: ${(err as Error).message}`)
    originalCode.value = ''
    isDirty.value = false
  } finally {
    // 只有仍是最新那次装载才释放「在途」标记，避免并发的旧响应提前清空它
    if (seq === _sourceSeq) _sourceInflightId = null
  }
}

/** 参数解析失败后的重试（沿用当前选中项；详情页语境，不走画廊路由）。 */
export function retryParseArgs(): Promise<ArgSpec[]> {
  return selectedId.value ? openDetail(selectedId.value, false, { forceDetail: true }) : Promise.resolve([])
}

/**
 * 缺依赖修复：装该示例的依赖 → 刷新后可运行性徽章 → 若当前就在详情页则直接重跑。
 * 入口在详情页头部（run_status=missing_deps 时出现），对应审计 A3「缺依赖无修复路径」。
 */
export async function installDepsAndRerun(): Promise<void> {
  const id = selectedId.value
  if (!id || installingDeps.value) return
  installingDeps.value = true
  appendOutput('▶ 正在安装该示例的依赖（按派生 import 分析）…\n', 'system')
  try {
    const result = await api.installExampleDeps(id)
    if (result.packages.length === 0) {
      appendOutput('[系统] 未识别到需要安装的第三方依赖\n', 'system')
      return
    }
    if (result.failed.length > 0) {
      appendOutput(`[错误] 这些包安装失败：${result.failed.join(', ')}\n`, 'error')
      pushToast('error', `有 ${result.failed.length} 个依赖安装失败`)
    } else {
      appendOutput(`[系统] 依赖已安装：${result.installed.join(', ')}\n`, 'system')
      pushToast('success', `已安装 ${result.installed.length} 个依赖`)
    }
  } catch (err) {
    appendOutput(`[错误] 安装依赖失败: ${(err as Error).message}\n`, 'error')
    pushToast('error', `安装失败: ${(err as Error).message}`)
    return
  } finally {
    installingDeps.value = false
  }
  // 装完即重跑（这是用户点这个按钮的意图）
  if (selectedId.value === id) runFromDetail()
}

export function closeDetail(force = false): void {
  if (!force && isDirty.value) {
    requestConfirm('当前示例有未保存的修改，放弃并返回？', () => closeDetail(true), {
      title: '放弃未保存的修改？',
      confirmLabel: '放弃修改'
    })
    return
  }
  selectedId.value = null
  interactiveSourceId.value = null
  pendingPreset.value = null
}

// Monaco 实例由组件注册进来；内容变更与取值都经它
export let editor: { getValue: () => string; setValue: (v: string) => void; getSelectedText?: () => string } | null =
  null
let _argsCollector: (() => string[]) | null = null
let _argsSetter: ((idx: number, v: string) => void) | null = null

export function registerEditor(fn: typeof editor): void {
  editor = fn
}
export function registerArgsCollector(fn: (() => string[]) | null): void {
  _argsCollector = fn
}
export function registerArgsSetter(fn: ((idx: number, v: string) => void) | null): void {
  _argsSetter = fn
}

export function onEditorContentChanged(code: string): void {
  if (selectedId.value) isDirty.value = code !== originalCode.value
}

export async function saveExample(): Promise<void> {
  const id = selectedId.value
  const ed = editor
  if (!id || !isDirty.value || saving.value || !ed) return
  const newCode = ed.getValue()
  saving.value = true
  try {
    const result = (await api.saveExample(id, newCode)) as { json_file?: string; path?: string }
    // 保存期间可能已切换示例：只允许写回保存时那个示例的状态
    if (selectedId.value !== id) return
    originalCode.value = newCode
    isDirty.value = false
    const ex = examples.value.find((e) => e.id === id)
    if (ex) {
      ex.code = newCode
      // 同步重建筛选预处理缓存与参数解析（argparse 定义可能变化）
      ex._importTags = FilterEngine.extractImportTags(newCode)
      ex._codeLower = newCode.toLowerCase()
      ex._tagsAll = FilterEngine.allTagsOf(ex)
      invalidateExampleVisual(ex)
      void openDetail(id) // 重载参数（保持选中，isDirty 已复位）
    }
    appendOutput(`[系统] 已保存: ${result.json_file || result.path || id}\n`, 'system')
    pushToast('success', '示例已保存并回写 JSON')
    void loadVersions() // 刚才这一版已进历史，面板开着时要立刻看到
  } catch (err) {
    appendOutput(`[错误] 保存失败: ${(err as Error).message}\n`, 'error')
    pushToast('error', `保存失败: ${(err as Error).message}`)
  } finally {
    saving.value = false
  }
}

export function runFromDetail(): void {
  if (isRunning.value || !selectedId.value) return
  const args = _argsCollector ? _argsCollector() : []
  // 必填项确实没有值（既无 default、用户也没填）时不起跑：collectArgs 已在上面置错
  // 并聚焦首个缺失字段，这里只负责拦住这次运行。有默认值的必填项不会被拦。
  if (requiredArgsMissing.value) return
  void startRun(selectedId.value, args, 'detail')
}

/** 卡片「运行」入口：必填参数缺失则留在表单引导填写，否则按表单值自动运行。
 * forceDetail：运行要跑的是这个示例文件本身，不得被画廊路由改道到交互页。 */
export async function runFromCard(id: string): Promise<void> {
  await openDetail(id, false, { forceDetail: true }) // 参数落到 currentArgs；运行走 runFromDetail 的收集路径
  if (selectedId.value !== id) return // 等待期间用户已切换
  if (requiredArgsMissing.value) return
  runFromDetail()
}

export const pendingHighRiskRun = ref<{ id: string; args: string[]; sink: OutputSurface } | null>(null)

/** 高危确认开关（设置弹窗「安全」分区）：与确认弹窗的「不再提示」共用同一持久化键 */
export function resolveHighRiskRun(proceed: boolean, skip: boolean): void {
  const pending = pendingHighRiskRun.value
  pendingHighRiskRun.value = null
  if (skip && pending) setSkipHighRiskConfirm(true)
  if (pending && proceed) void beginRun(pending.id, pending.args, pending.sink)
}

export async function startRun(id: string, args: string[], sink: OutputSurface = 'detail'): Promise<void> {
  const ex = examples.value.find((e) => e.id === id)
  if (!ex) return
  if (ex.risk_high && !skipHighRiskConfirm.value) {
    pendingHighRiskRun.value = { id, args, sink }
    return
  }
  await beginRun(id, args, sink)
}

/** 调整并持久化运行超时（秒） */
async function beginRun(id: string, args: string[], sink: OutputSurface = 'detail'): Promise<void> {
  const ex = examples.value.find((e) => e.id === id)
  if (!ex) return
  runSink.value = sink
  isRunning.value = true
  resetOutputSurface(sink)
  runStatusText.value = '运行中…'
  appendOutput(`▶ 运行: ${ex.name}\n`, 'system', sink)
  if (args.length > 0) appendOutput(`  参数: ${args.join(' ')}\n`, 'system', sink)
  currentRunMeta.value = { id, name: ex.name, args, startedAt: Date.now() }
  _earlyOutputBuffer = []
  try {
    const params: { id: string; timeout: number; args?: string[] } = { id, timeout: runTimeout.value }
    if (args.length > 0) params.args = args
    const result = (await api.runExample(params)) as { run_id?: string }
    currentRunId.value = result.run_id || null
    appendOutput(`  run_id: ${currentRunId.value}\n`, 'system', sink)
    // 补放 run_id 回包前到达的早期输出
    outputStats.replayed += _earlyOutputBuffer.length
    for (const line of _earlyOutputBuffer) surfaces[runSink.value].lines.push(line)
    _earlyOutputBuffer = []
  } catch (err) {
    appendOutput(`[错误] 启动失败: ${(err as Error).message}\n`, 'error', sink)
    isRunning.value = false
    currentRunMeta.value = null
    surfaces[sink].dot = 'error'
    runStatusText.value = '启动失败'
  }
}

export async function stopRun(): Promise<void> {
  if (!currentRunId.value) return
  try {
    await api.stopRun(currentRunId.value)
    appendOutput('\n[系统] 已发送停止指令\n', 'system')
  } catch (err) {
    appendOutput(`[错误] 停止失败: ${(err as Error).message}\n`, 'error')
  }
}

// 运行输出计数（诊断用，走查探针据此定位丢行环节）
export const outputStats = { received: 0, buffered: 0, dropped: 0, appended: 0, replayed: 0 }

export function initRunEvents(): void {
  api.on('runOutput', (data) => {
    outputStats.received++
    if (data.run_id !== currentRunId.value) {
      // run_id 回包前的早期输出进缓冲，避免丢弃
      if (isRunning.value && currentRunId.value === null) {
        outputStats.buffered++
        _earlyOutputBuffer.push({ text: data.text || '', cls: 'base' })
      } else {
        outputStats.dropped++
      }
      return
    }
    outputStats.appended++
    const text = data.text || ''
    const cls: OutputLine['cls'] = text.startsWith('[系统]') || text.startsWith('[错误]') ? 'system' : 'base'
    appendOutput(text, cls, runSink.value)
  })
  api.on('runImages', (data) => {
    if (data.run_id !== currentRunId.value) return
    surfaces[runSink.value].images = (data.images || []).map((url: string) => ({
      url,
      name: decodeURIComponent(url.split('/').pop() || 'image')
    }))
  })
  api.on('runFinished', (data) => {
    if (data.run_id !== currentRunId.value) return
    const exitCode = data.exit_code
    const sink = runSink.value
    if (exitCode === 0) {
      appendOutput('✓ 运行成功 (exit code: 0)\n', 'success', sink)
      surfaces[sink].dot = 'success'
      runStatusText.value = '运行成功'
    } else {
      appendOutput(`✗ 运行失败 (exit code: ${exitCode})\n`, 'error', sink)
      surfaces[sink].dot = 'error'
      runStatusText.value = '运行失败'
    }
    if (currentRunMeta.value) recordHistory(currentRunMeta.value, exitCode)
    isRunning.value = false
    currentRunMeta.value = null
    currentRunId.value = null
  })
}

// ---------------------------------------------------------------------------
// 测试钩子（详情页与运行）：由 store/index.ts 的 getTestApi 组合成 window.__app
// ---------------------------------------------------------------------------
export function detailTestHooks(): Record<string, unknown> {
  return {
    openDetail: (id: string) => openDetail(id),
    selectedId: () => selectedId.value,
    currentArgs: () => currentArgs.value,
    setArgValue: (idx: number, v: string) => _argsSetter?.(idx, v),
    collectArgs: () => _argsCollector?.() || [],
    backfillArgs: (tokens: string[]) => {
      pendingBackfillTokens.value = tokens
    },
    runFromDetail: () => runFromDetail(),
    argsError: () => argsError.value,
    // 走查脚本用：直接写编辑器内容并走真实保存路径（含快照）
    closeDetail: () => closeDetail(),
    confirmPrompt: () => confirmPrompt.value,
    resolveConfirm: (ok: boolean) => resolveConfirm(ok),
    requestConfirm: (message: string, action: () => void) => requestConfirm(message, action),
    setEditorValue: (code: string) => {
      if (!editor) return false
      editor.setValue(code)
      return true
    },
    saveExample: () => saveExample(),
    isDirty: () => isDirty.value,
    versions: () => versions.value,
    versionPreview: () => versionPreview.value,
    loadVersions: () => loadVersions(),
    previewVersion: (ts: string) => previewVersion(ts),
    restoreVersion: (ts: string) => restoreVersion(ts),
    retryParseArgs: () => retryParseArgs(),
    installDepsAndRerun: () => installDepsAndRerun(),
    isRunning: () => isRunning.value,
    runStatusText: () => runStatusText.value,
    outputText: () => surfaces.detail.lines.map((l) => l.text).join(''),
    outputLineCount: () => surfaces.detail.lines.length,
    outputStats: () => ({
      ...outputStats,
      sink: runSink.value,
      detailLines: surfaces.detail.lines.length,
      runnerLines: surfaces.runner.lines.length,
      detailTruncated: surfaces.detail.truncated
    }),
    detailHistory: () => detailHistory.value
  }
}
