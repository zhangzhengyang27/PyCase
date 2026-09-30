// panels 层组件测试：带 store 依赖的侧栏 / 弹窗（AI 解释面板、设置、导入向导、高危确认、资源面板）。
//
// 与 base.spec 的关键差异，也是本文件大量样板代码的来源：
//   1. 这些组件读写 store 单例（模块级状态），用例间会互相污染——必须逐项复位；
//   2. AISettingsModal / ImportWizardModal / HighRiskConfirmModal / AssetsPanel 都经
//      AppModal 渲染到 document.body（Teleport），查询要走 document.body 而非 wrapper；
//   3. AppModal 在 window 上注册 keydown 监听，若只清 innerHTML 而不 unmount，
//      上一个用例遗留的 Esc 监听会在下一个用例里误触弹窗关闭——因此统一 track + unmount。
import { describe, expect, it, afterEach, beforeEach, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { nextTick } from 'vue'

import AIExplainPanel from '../AIExplainPanel.vue'
import AISettingsModal from '../AISettingsModal.vue'
import ImportWizardModal from '../ImportWizardModal.vue'
import HighRiskConfirmModal from '../HighRiskConfirmModal.vue'
import AssetsPanel from '../AssetsPanel.vue'

import { aiSettings, aiSettingsOpen, aiPanelOpen, aiRunId, aiStatus, aiStatusError, aiOutputText, aiShowStop } from '../../src/store/ai'
import { assets, assetsLoading, type AssetInfo } from '../../src/store/assets'
import { examples, type VExample } from '../../src/store/catalog'
import { selectedId, pendingHighRiskRun, isRunning, currentRunId, currentRunMeta } from '../../src/store/detail'
import { importWizardOpen } from '../../src/store/import'
import { getTestApi } from '../../src/store/index'
import { runTimeout, skipHighRiskConfirm } from '../../src/store/prefs'
import { storageReport } from '../../src/store/storage'
import { toasts } from '../../toast'

// ---------------------------------------------------------------------------
// 共享夹具与工具
// ---------------------------------------------------------------------------

const mounted: Array<{ unmount: () => void }> = []

/** 登记 wrapper 以便 afterEach 统一卸载（释放 AppModal 的 window 监听）。 */
function track<T extends { unmount: () => void }>(w: T): T {
  mounted.push(w)
  return w
}

/** 在 body（或指定作用域）内按可见文案找按钮，避免依赖易变的 class 选择器。 */
function findButton(text: string, scope: ParentNode = document.body): HTMLButtonElement {
  const btn = Array.from(scope.querySelectorAll('button')).find((b) => (b.textContent || '').includes(text))
  if (!btn) throw new Error(`未找到按钮: ${text}`)
  return btn as HTMLButtonElement
}

function makeExample(over: Partial<VExample> = {}): VExample {
  return { id: 'ex-1', name: 'demo.py', category: 'topics', path: '/tmp/demo.py', ...over }
}

function makeAsset(over: Partial<AssetInfo> = {}): AssetInfo {
  return { filename: 'a.png', size: 1024, modified: 0, is_image: true, ...over }
}

// store.uploadAssets 用 File.arrayBuffer() 把文件读成二进制再 base64；
// jsdom 未实现该异步读取方法，补齐已由 vitest.setup.ts 统一提供（经 FileReader 兜底）。

/** store 单例逐项复位：不清就会串味（例如上一个用例打开的弹窗让下一个用例一挂载就有 dialog）。 */
function resetStore(): void {
  ;(getTestApi() as unknown as { resetViewFilters: () => void }).resetViewFilters()
  examples.value = []
  selectedId.value = null
  assets.value = []
  assetsLoading.value = false
  isRunning.value = false
  currentRunId.value = null
  currentRunMeta.value = null

  aiSettings.hasKey = false
  aiSettings.model = 'deepseek-chat'
  aiSettings.baseUrl = 'https://api.deepseek.com'
  aiSettings.acknowledged = false
  aiSettingsOpen.value = false
  aiPanelOpen.value = false
  aiRunId.value = ''
  aiStatus.value = '正在准备…'
  aiStatusError.value = false
  aiOutputText.value = ''
  aiShowStop.value = false

  importWizardOpen.value = false
  pendingHighRiskRun.value = null
  skipHighRiskConfirm.value = false
  runTimeout.value = 30

  toasts.value = []
}

beforeEach(() => {
  resetStore()
  // jsdom 无 clipboard；copyAIOutput 依赖它，缺了会走到 catch 分支掩盖真实行为。
  Object.defineProperty(navigator, 'clipboard', {
    value: { writeText: vi.fn(async () => undefined) },
    configurable: true,
    writable: true
  })
})

afterEach(() => {
  // 先卸载再清 DOM：卸载顺序决定 AppModal 的 keydown 监听被移除，
  // 否则残留监听会在后续用例响应 Esc。
  mounted.splice(0).forEach((w) => w.unmount())
  document.body.innerHTML = ''
  toasts.value = []
})

// ---------------------------------------------------------------------------
// AIExplainPanel：纯面板，无 Teleport，直接读 store refs
// ---------------------------------------------------------------------------
describe('AIExplainPanel', () => {
  it('渲染 store 中的状态行与解释正文，并随状态变化实时更新', async () => {
    aiStatus.value = '正在生成解释…'
    aiOutputText.value = '第一段\n第二段'
    const w = track(mount(AIExplainPanel))

    const header = w.element.children[0] as HTMLElement
    const status = w.element.children[1] as HTMLElement
    const output = w.element.children[2] as HTMLElement
    expect(header.textContent).toContain('AI 代码解释（DeepSeek）')
    expect(status.textContent).toContain('正在生成解释…')
    // whitespace-pre-wrap：换行原样保留
    expect(output.textContent).toBe('第一段\n第二段')

    aiOutputText.value = '追加的内容'
    await nextTick()
    expect((w.element.children[2] as HTMLElement).textContent).toBe('追加的内容')
  })

  it('aiStatusError 切换状态行配色（错误红 / 常态灰）', async () => {
    const w = track(mount(AIExplainPanel))
    const status = w.element.children[1] as HTMLElement
    expect(status.className).toContain('text-ink-mute')
    expect(status.className).not.toContain('text-danger')

    aiStatusError.value = true
    await nextTick()
    expect(status.className).toContain('text-danger')
    expect(status.className).not.toContain('text-ink-mute')
  })

  it('aiShowStop 控制「停止」按钮显隐（v-show：节点保留，仅切 display）', async () => {
    const w = track(mount(AIExplainPanel))
    const stop = w.get('button[title="停止解释"]').element as HTMLElement
    expect(stop.style.display).toBe('none')

    aiShowStop.value = true
    await nextTick()
    expect(stop.style.display).not.toBe('none')
  })

  it('点击「复制」把正文写入剪贴板并把状态行切为已复制', async () => {
    aiOutputText.value = '要复制的内容'
    const w = track(mount(AIExplainPanel))
    ;(w.get('button[title="复制解释"]').element as HTMLElement).click()
    await flushPromises()

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('要复制的内容')
    expect(aiStatus.value).toBe('已复制到剪贴板')
    expect(aiStatusError.value).toBe(false)
  })

  it('无输出时「复制」是空操作：不触碰剪贴板、状态行保持原样', async () => {
    aiOutputText.value = ''
    aiStatus.value = '等待中'
    const w = track(mount(AIExplainPanel))
    ;(w.get('button[title="复制解释"]').element as HTMLElement).click()
    await flushPromises()

    expect(navigator.clipboard.writeText).not.toHaveBeenCalled()
    expect(aiStatus.value).toBe('等待中')
  })

  it('剪贴板写入失败时状态行转为错误态', async () => {
    aiOutputText.value = 'x'
    vi.mocked(navigator.clipboard.writeText).mockRejectedValue(new Error('denied'))
    const w = track(mount(AIExplainPanel))
    ;(w.get('button[title="复制解释"]').element as HTMLElement).click()
    await flushPromises()

    expect(aiStatus.value).toBe('复制失败')
    expect(aiStatusError.value).toBe(true)
  })

  it('点击「停止」终止解释：调用 aiStop、状态转「已停止」并收起停止钮', async () => {
    aiRunId.value = 'run-42'
    aiShowStop.value = true
    const w = track(mount(AIExplainPanel))
    ;(w.get('button[title="停止解释"]').element as HTMLElement).click()
    await flushPromises()

    expect(window.sidecar.ai.stop).toHaveBeenCalledWith('run-42')
    expect(aiStatus.value).toBe('已停止')
    expect(aiShowStop.value).toBe(false)
  })

  it('点击关闭终止进行中的解释并隐藏面板', async () => {
    aiRunId.value = 'run-7'
    aiPanelOpen.value = true
    const w = track(mount(AIExplainPanel))
    ;(w.get('button[aria-label="关闭 AI 解释面板"]').element as HTMLElement).click()
    await flushPromises()

    expect(window.sidecar.ai.stop).toHaveBeenCalledWith('run-7')
    expect(aiPanelOpen.value).toBe(false)
    expect(aiRunId.value).toBe('')
  })
})

// ---------------------------------------------------------------------------
// AISettingsModal：store 可见性 + 校验 + 保存 + 运行/安全分区
// ---------------------------------------------------------------------------
describe('AISettingsModal', () => {
  it('aiSettingsOpen=false 时不渲染弹窗', () => {
    track(mount(AISettingsModal))
    expect(document.body.querySelector('[role="dialog"]')).toBeNull()
  })

  it('打开时标题为「设置」，model / baseUrl 回填 store，Key 始终为空输入', () => {
    aiSettings.model = 'deepseek-reasoner'
    aiSettings.baseUrl = 'https://api.example.com'
    aiSettingsOpen.value = true
    track(mount(AISettingsModal))

    const dialog = document.body.querySelector('[role="dialog"]')!
    expect(dialog.getAttribute('aria-label')).toBe('设置')
    expect((document.body.querySelector('#setting-model') as HTMLInputElement).value).toBe('deepseek-reasoner')
    expect((document.body.querySelector('#setting-baseurl') as HTMLInputElement).value).toBe('https://api.example.com')
    // 明文 key 从不回填到前端
    expect((document.body.querySelector('#setting-apikey') as HTMLInputElement).value).toBe('')
    // 未触碰且未尝试保存时不展示任何字段错误
    expect(document.body.querySelectorAll('p.text-danger')).toHaveLength(0)
  })

  it('模型清空后（已触碰）即时显示校验错误并标红', async () => {
    aiSettingsOpen.value = true
    track(mount(AISettingsModal))
    const input = document.body.querySelector('#setting-model') as HTMLInputElement
    input.value = ''
    input.dispatchEvent(new Event('input'))
    await nextTick()

    expect(input.getAttribute('aria-invalid')).toBe('true')
    expect(Array.from(document.body.querySelectorAll('p.text-danger')).map((p) => p.textContent)).toContain(
      '请输入模型名（默认 deepseek-chat）'
    )
  })

  it('Base URL 非 http(s) 时提示格式错误，改回合法地址后错误消失', async () => {
    aiSettingsOpen.value = true
    track(mount(AISettingsModal))
    const input = document.body.querySelector('#setting-baseurl') as HTMLInputElement

    input.value = 'ftp://nope'
    input.dispatchEvent(new Event('input'))
    await nextTick()
    expect(document.body.textContent).toContain('需为 http(s):// 开头的合法地址')

    input.value = 'https://api.deepseek.com'
    input.dispatchEvent(new Event('input'))
    await nextTick()
    expect(document.body.textContent).not.toContain('需为 http(s):// 开头的合法地址')
  })

  it('API Key 少于 8 字符报错；留空视为「不修改」不报错', async () => {
    aiSettingsOpen.value = true
    track(mount(AISettingsModal))
    const input = document.body.querySelector('#setting-apikey') as HTMLInputElement

    input.value = 'short'
    input.dispatchEvent(new Event('input'))
    await nextTick()
    expect(document.body.textContent).toContain('Key 至少 8 个字符')

    input.value = ''
    input.dispatchEvent(new Event('input'))
    await nextTick()
    expect(document.body.textContent).not.toContain('Key 至少 8 个字符')
  })

  it('校验未通过时保存被拦截：attempted 让未触碰字段也报错、聚焦首个错误字段、不发请求', async () => {
    aiSettings.model = ''
    aiSettings.baseUrl = ''
    aiSettingsOpen.value = true
    track(mount(AISettingsModal))

    findButton('保存').click()
    await flushPromises()

    expect(window.sidecar.ai.setSettings).not.toHaveBeenCalled()
    expect(aiSettingsOpen.value).toBe(true)
    expect(document.body.textContent).toContain('请输入模型名（默认 deepseek-chat）')
    expect(document.body.textContent).toContain('请输入 Base URL')
    expect(document.activeElement).toBe(document.body.querySelector('#setting-model'))
  })

  it('保存成功：写回 store、提示成功、关闭弹窗；空 Key 不进入 patch', async () => {
    vi.mocked(window.sidecar.ai.setSettings).mockResolvedValue({ ok: true, hasKey: true })
    aiSettingsOpen.value = true
    track(mount(AISettingsModal))

    findButton('保存').click()
    await flushPromises()

    expect(window.sidecar.ai.setSettings).toHaveBeenCalledWith({
      model: 'deepseek-chat',
      baseUrl: 'https://api.deepseek.com'
    })
    expect(aiSettings.hasKey).toBe(true)
    expect(aiSettingsOpen.value).toBe(false)
    expect(toasts.value.at(-1)?.type).toBe('success')
    expect(toasts.value.at(-1)?.text).toBe('AI 设置已保存')
  })

  it('填入新 Key 时随 patch 一并提交', async () => {
    vi.mocked(window.sidecar.ai.setSettings).mockResolvedValue({ ok: true, hasKey: true })
    aiSettingsOpen.value = true
    track(mount(AISettingsModal))
    const key = document.body.querySelector('#setting-apikey') as HTMLInputElement
    key.value = 'sk-12345678'
    key.dispatchEvent(new Event('input'))
    await nextTick()

    findButton('保存').click()
    await flushPromises()

    expect(window.sidecar.ai.setSettings).toHaveBeenCalledWith(expect.objectContaining({ apiKey: 'sk-12345678' }))
  })

  it('保存失败：提示错误、弹窗保持打开、loading 复位', async () => {
    vi.mocked(window.sidecar.ai.setSettings).mockRejectedValue(new Error('网络不可达'))
    aiSettingsOpen.value = true
    track(mount(AISettingsModal))

    findButton('保存').click()
    await flushPromises()

    expect(aiSettingsOpen.value).toBe(true)
    expect(toasts.value.at(-1)?.type).toBe('error')
    expect(toasts.value.at(-1)?.text).toContain('保存 AI 设置失败')
    expect(findButton('保存').querySelector('.animate-spin')).toBeNull()
  })

  it('超时下拉：选项固定，改值写入 store 并持久化 runPrefs', async () => {
    aiSettingsOpen.value = true
    track(mount(AISettingsModal))
    const select = document.body.querySelector('select') as HTMLSelectElement
    expect(select.value).toBe('30')
    expect(Array.from(select.options).map((o) => o.value)).toEqual(['15', '30', '60', '120', '300'])

    select.value = '60'
    select.dispatchEvent(new Event('change'))
    await nextTick()

    expect(runTimeout.value).toBe(60)
    expect(window.sidecar.store.set).toHaveBeenCalledWith('runPrefs', { timeout: 60 })
  })

  it('高危确认勾选框映射 skipHighRiskConfirm（取消勾选 = 不再提示并持久化）', async () => {
    aiSettingsOpen.value = true
    track(mount(AISettingsModal))
    const cb = document.body.querySelector('input[type="checkbox"]') as HTMLInputElement
    // skip=false → 勾选态
    expect(cb.checked).toBe(true)

    cb.click()
    await nextTick()

    expect(skipHighRiskConfirm.value).toBe(true)
    expect(cb.checked).toBe(false)
    expect(window.sidecar.store.set).toHaveBeenCalledWith('safetyPrefs', { skipHighRiskConfirm: true })
  })

  it('再次打开时复位输入与校验状态（Key 清空、错误消失）', async () => {
    aiSettingsOpen.value = true
    track(mount(AISettingsModal))
    const key = document.body.querySelector('#setting-apikey') as HTMLInputElement
    key.value = 'bad'
    key.dispatchEvent(new Event('input'))
    await nextTick()
    expect(document.body.textContent).toContain('Key 至少 8 个字符')

    aiSettingsOpen.value = false
    await nextTick()
    aiSettingsOpen.value = true
    await nextTick()

    expect((document.body.querySelector('#setting-apikey') as HTMLInputElement).value).toBe('')
    expect(document.body.textContent).not.toContain('Key 至少 8 个字符')
  })
})

// ---------------------------------------------------------------------------
// ImportWizardModal：三步向导（pick → preview → done）
// ---------------------------------------------------------------------------
describe('设置中心·存储分区（A6 缓存入口）', () => {
  const report = {
    workspace: {
      root: '/tmp/ws',
      bytes: 1024 * 1024 * 300,
      max_bytes: 1024 * 1024 * 1024,
      entries: [
        { key: 'a-1', bytes: 100, last_used: 1, has_assets: false },
        { key: 'b-2', bytes: 200, last_used: 2, has_assets: true }
      ],
      asset_entries: 1
    },
    legacy: { root: '/tmp/cache', bytes: 1024 * 1024 * 120, entries: 3151 },
    history: { bytes: 2048 }
  }

  it('打开设置时拉取占用：显示工作区/旧根/编辑历史与含资产条目数', async () => {
    vi.mocked(window.sidecar.storageReport).mockResolvedValue(report)
    aiSettingsOpen.value = true
    track(mount(AISettingsModal))
    await flushPromises()

    expect(window.sidecar.storageReport).toHaveBeenCalled()
    const ws = document.body.querySelector('[data-testid="storage-workspace"]')!
    expect(ws.textContent).toContain('300.0MB')
    expect(ws.textContent).toContain('1024.0MB')
    expect(document.body.querySelector('[data-testid="storage-assets"]')!.textContent).toContain('1 个')
    expect(document.body.querySelector('[data-testid="storage-legacy"]')!.textContent).toContain('3151 项')
    expect(document.body.querySelector('[data-testid="storage-history"]')!.textContent).toContain('0.0MB')
  })

  it('清理干净工作区：先弹确认（只数干净条目）再调 clean', async () => {
    vi.mocked(window.sidecar.storageReport).mockResolvedValue(report)
    vi.mocked(window.sidecar.cleanWorkspace).mockResolvedValue({ removed: 1, kept: 1, freed_bytes: 100 })
    aiSettingsOpen.value = true
    track(mount(AISettingsModal))
    await flushPromises()

    findButton('清理干净工作区', document.body).click()
    await nextTick()
    const dialog = document.body.querySelector('[role="dialog"][aria-label="清理工作区"]')!
    expect(dialog.textContent).toContain('1 个干净工作区副本')
    expect(window.sidecar.cleanWorkspace).not.toHaveBeenCalled()

    findButton('清理', dialog).click()
    await flushPromises()
    expect(window.sidecar.cleanWorkspace).toHaveBeenCalledWith('clean')
    expect(toasts.value.some((t) => t.text.includes('已清理 1 个工作区'))).toBe(true)
  })

  it('全部清理：确认文案点明含上传资源且不可撤销，按 danger 档调用 all', async () => {
    vi.mocked(window.sidecar.storageReport).mockResolvedValue(report)
    vi.mocked(window.sidecar.cleanWorkspace).mockResolvedValue({ removed: 2, kept: 0, freed_bytes: 300 })
    aiSettingsOpen.value = true
    track(mount(AISettingsModal))
    await flushPromises()

    ;(document.body.querySelector('[data-testid="storage-clean-all"]') as HTMLButtonElement).click()
    await nextTick()
    const dialog = document.body.querySelector('[role="dialog"][aria-label="清理工作区"]')!
    expect(dialog.textContent).toContain('包含你上传的资源与运行产物')
    expect(dialog.textContent).toContain('不可撤销')

    findButton('全部清理', dialog).click()
    await flushPromises()
    expect(window.sidecar.cleanWorkspace).toHaveBeenCalledWith('all')
  })

  it('回收旧版缓存：仅在存在 v1 遗留时出现，确认后调用回收', async () => {
    vi.mocked(window.sidecar.storageReport).mockResolvedValue(report)
    vi.mocked(window.sidecar.reclaimLegacyCache).mockResolvedValue({ removed: 3151, freed_bytes: 1024 * 1024 * 120 })
    aiSettingsOpen.value = true
    track(mount(AISettingsModal))
    await flushPromises()

    findButton('回收旧版缓存', document.body).click()
    await nextTick()
    const dialog = document.body.querySelector('[role="dialog"][aria-label="回收旧版缓存"]')!
    findButton('回收', dialog).click()
    await flushPromises()
    expect(window.sidecar.reclaimLegacyCache).toHaveBeenCalled()
    expect(toasts.value.some((t) => t.text.includes('已回收旧缓存 3151 项'))).toBe(true)
  })

  it('代码外发同意可复核可撤销（A6 可恢复编辑的一部分）', async () => {
    vi.mocked(window.sidecar.storageReport).mockResolvedValue(null as never)
    aiSettings.acknowledged = true
    aiSettingsOpen.value = true
    track(mount(AISettingsModal))
    await flushPromises()

    const section = document.body.querySelector('[data-testid="settings-consent"]')!
    expect(section.textContent).toContain('已同意')
    findButton('撤回同意', section).click()
    await flushPromises()
    expect(window.sidecar.ai.setSettings).toHaveBeenCalledWith({ acknowledged: false })
    expect(aiSettings.acknowledged).toBe(false)

    // 撤回后按钮翻转为「现在同意」
    await nextTick()
    findButton('现在同意', document.body.querySelector('[data-testid="settings-consent"]')!)
      .click()
    await flushPromises()
    expect(window.sidecar.ai.setSettings).toHaveBeenCalledWith({ acknowledged: true })
  })

  it('无 v1 遗留时不显示回收按钮', async () => {
    vi.mocked(window.sidecar.storageReport).mockResolvedValue({ ...report, legacy: { root: '/tmp', bytes: 0, entries: 0 } })
    aiSettingsOpen.value = true
    track(mount(AISettingsModal))
    await flushPromises()
    const reclaimBtn = Array.from(document.body.querySelectorAll('button')).find((b) =>
      (b.textContent || '').includes('回收旧版缓存')
    )
    expect(reclaimBtn ?? null).toBeNull()
  })
})

describe('ImportWizardModal', () => {
  const FILES = [
    { id: 'a.py', name: 'a', tags: [], requirements: ['requests', 'numpy', 'pandas'], bytes: 2048 },
    { id: 'b.py', name: 'b', tags: [], requirements: [], bytes: 300 }
  ]

  function mockPick(path: string | null): void {
    vi.mocked(window.sidecar.pickDirectory).mockResolvedValue(path ? { canceled: false, path } : { canceled: true })
  }
  function mockScan(files: typeof FILES, skipped: Array<{ file: string; reason: string }> = []): void {
    vi.mocked(window.sidecar.scanImportSource).mockResolvedValue({ total: files.length, files, skipped })
  }
  /** 走到预览步的公共路径：选目录 → 自动扫描。 */
  async function gotoPreview(
    path = '/home/me/myset',
    files = FILES,
    skipped: Array<{ file: string; reason: string }> = []
  ): Promise<void> {
    mockPick(path)
    mockScan(files, skipped)
    findButton('选择目录').click()
    await flushPromises()
  }
  function dialogLabel(): string | null {
    return document.body.querySelector('[role="dialog"]')?.getAttribute('aria-label') ?? null
  }

  it('importWizardOpen=false 时不渲染', () => {
    track(mount(ImportWizardModal))
    expect(document.body.querySelector('[role="dialog"]')).toBeNull()
  })

  it('第一步：未选目录时展示占位文案，扫描按钮禁用', () => {
    importWizardOpen.value = true
    track(mount(ImportWizardModal))
    const dialog = document.body.querySelector('[role="dialog"]')!
    expect(dialog.getAttribute('aria-label')).toBe('导入示例目录')
    expect(dialog.textContent).toContain('尚未选择目录')
    expect(findButton('扫描并预览').hasAttribute('disabled')).toBe(true)
  })

  it('选目录后自动扫描进入预览：展示文件、最多 2 个依赖徽标与体积', async () => {
    importWizardOpen.value = true
    track(mount(ImportWizardModal))
    await gotoPreview('/home/me/myset', FILES, [{ file: 'skip.py', reason: 'empty' }])

    expect(window.sidecar.scanImportSource).toHaveBeenCalledWith('/home/me/myset')
    expect(dialogLabel()).toBe('确认导入')
    const text = document.body.textContent || ''
    expect(text).toContain('扫描到')
    expect(text).toContain('a.py')
    expect(text).toContain('b.py')
    expect(text).toContain('跳过 1 个')
    // requirements 只展示前 2 个
    expect(text).toContain('requests')
    expect(text).toContain('numpy')
    expect(text).not.toContain('pandas')
    expect(text).toContain('2.0 KB')
    expect(text).toContain('300 B')
  })

  it('取消选择目录时不进入扫描，保持第一步', async () => {
    importWizardOpen.value = true
    track(mount(ImportWizardModal))
    mockPick(null)
    findButton('选择目录').click()
    await flushPromises()

    expect(window.sidecar.scanImportSource).not.toHaveBeenCalled()
    expect(document.body.textContent).toContain('尚未选择目录')
  })

  it('目录内无可导入 .py 时停在第一步并给出错误', async () => {
    importWizardOpen.value = true
    track(mount(ImportWizardModal))
    await gotoPreview('/tmp/empty', [])

    expect(dialogLabel()).toBe('导入示例目录')
    expect(document.body.textContent).toContain('该目录下没有可导入的 .py 文件')
  })

  it('扫描抛错时把错误消息展示出来（不静默吞掉）', async () => {
    importWizardOpen.value = true
    track(mount(ImportWizardModal))
    mockPick('/tmp/boom')
    vi.mocked(window.sidecar.scanImportSource).mockRejectedValue(new Error('permission denied'))
    findButton('选择目录').click()
    await flushPromises()

    expect(document.body.textContent).toContain('permission denied')
  })

  it('扫描失败后按钮恢复可用，可手动重扫并进入预览', async () => {
    importWizardOpen.value = true
    track(mount(ImportWizardModal))
    await gotoPreview('/tmp/retry', [])

    const scan = findButton('扫描并预览')
    expect(scan.hasAttribute('disabled')).toBe(false)

    mockScan(FILES)
    findButton('扫描并预览').click()
    await flushPromises()
    expect(dialogLabel()).toBe('确认导入')
  })

  it('执行导入成功：进入完成步、提示成功并刷新示例列表', async () => {
    vi.mocked(window.sidecar.importExamples).mockResolvedValue({ imported: 2, skipped: [], collection: 'myset' })
    importWizardOpen.value = true
    track(mount(ImportWizardModal))
    await gotoPreview('/home/me/myset', FILES)

    findButton('导入 2 个示例').click()
    await flushPromises()

    expect(window.sidecar.importExamples).toHaveBeenCalledWith({ source_path: '/home/me/myset', name: 'myset' })
    expect(window.sidecar.listExamples).toHaveBeenCalled()
    expect(dialogLabel()).toBe('导入完成')
    expect(document.body.textContent).toContain('已导入 2 个示例')
    expect(document.body.textContent).toContain('myset')
    expect(toasts.value.at(-1)?.text).toBe('已导入 2 个示例到「myset」')
  })

  it('导入结果含跳过项时在完成步补充说明', async () => {
    vi.mocked(window.sidecar.importExamples).mockResolvedValue({
      imported: 1,
      skipped: [{ file: 'b.py', reason: 'dup' }],
      collection: 'myset'
    })
    importWizardOpen.value = true
    track(mount(ImportWizardModal))
    await gotoPreview()

    findButton('导入 2 个示例').click()
    await flushPromises()

    expect(document.body.textContent).toContain('跳过 1 个文件')
  })

  it('导入失败：提示错误并留在预览步', async () => {
    vi.mocked(window.sidecar.importExamples).mockRejectedValue(new Error('磁盘已满'))
    importWizardOpen.value = true
    track(mount(ImportWizardModal))
    await gotoPreview()

    findButton('导入 2 个示例').click()
    await flushPromises()

    expect(toasts.value.at(-1)?.type).toBe('error')
    expect(toasts.value.at(-1)?.text).toContain('导入失败')
    expect(dialogLabel()).toBe('确认导入')
  })

  it('「上一步」回到第一步但保留已选目录', async () => {
    importWizardOpen.value = true
    track(mount(ImportWizardModal))
    await gotoPreview()

    findButton('上一步').click()
    await nextTick()

    expect(dialogLabel()).toBe('导入示例目录')
    expect(document.body.textContent).toContain('/home/me/myset')
  })

  it('完成步「完成」关闭向导', async () => {
    vi.mocked(window.sidecar.importExamples).mockResolvedValue({ imported: 1, skipped: [], collection: 'myset' })
    importWizardOpen.value = true
    track(mount(ImportWizardModal))
    await gotoPreview()
    findButton('导入 2 个示例').click()
    await flushPromises()

    findButton('完成').click()
    await nextTick()

    expect(importWizardOpen.value).toBe(false)
    expect(document.body.querySelector('[role="dialog"]')).toBeNull()
  })
})

// ---------------------------------------------------------------------------
// HighRiskConfirmModal：高危运行二次确认
// ---------------------------------------------------------------------------
describe('HighRiskConfirmModal', () => {
  function seedRiskExample(over: Partial<VExample> = {}): VExample {
    const ex = makeExample({
      id: 'risk-1',
      name: 'danger.py',
      title: '危险脚本',
      risk_high: true,
      risk_findings: [
        { description: '删除用户文件', category: 'fs' },
        { description: '执行系统命令', category: 'exec' }
      ],
      ...over
    })
    examples.value = [ex]
    return ex
  }
  function setPending(id = 'risk-1', args: string[] = []): void {
    pendingHighRiskRun.value = { id, args, sink: 'detail' }
  }
  function dialog(): Element | null {
    return document.body.querySelector('[role="dialog"]')
  }

  it('无待确认运行时完全不渲染', () => {
    seedRiskExample()
    track(mount(HighRiskConfirmModal))
    expect(dialog()).toBeNull()
  })

  it('pending 指向的示例不存在时（target 为空）也不渲染', () => {
    seedRiskExample()
    setPending('missing-id')
    track(mount(HighRiskConfirmModal))
    expect(dialog()).toBeNull()
  })

  it('渲染标题、示例名与全部高危明细', () => {
    seedRiskExample()
    setPending()
    track(mount(HighRiskConfirmModal))

    const d = dialog()!
    expect(d.getAttribute('aria-label')).toBe('运行高危示例')
    expect(d.textContent).toContain('危险脚本')
    const items = Array.from(d.querySelectorAll('li')).map((li) => li.textContent)
    expect(items).toEqual(['删除用户文件', '执行系统命令'])
  })

  it('示例无 title 时回退展示 name', () => {
    seedRiskExample({ title: undefined, name: 'no-title.py' })
    setPending()
    track(mount(HighRiskConfirmModal))
    expect(dialog()!.textContent).toContain('no-title.py')
  })

  it('取消：清空待确认运行且不发起运行', async () => {
    seedRiskExample()
    setPending()
    track(mount(HighRiskConfirmModal))

    findButton('取消').click()
    await flushPromises()

    expect(pendingHighRiskRun.value).toBeNull()
    expect(window.sidecar.runExample).not.toHaveBeenCalled()
  })

  it('「仍要运行」（未勾选不再提示）：清空 pending、发起运行、不改持久化开关', async () => {
    seedRiskExample()
    setPending('risk-1', ['--force'])
    track(mount(HighRiskConfirmModal))

    findButton('仍要运行').click()
    await flushPromises()

    expect(pendingHighRiskRun.value).toBeNull()
    // args 非空时随参数一并透传
    expect(window.sidecar.runExample).toHaveBeenCalledWith({ id: 'risk-1', timeout: 30, args: ['--force'] })
    expect(skipHighRiskConfirm.value).toBe(false)
    expect(window.sidecar.store.set).not.toHaveBeenCalledWith('safetyPrefs', { skipHighRiskConfirm: true })
  })

  it('勾选「不再提示」后仍要运行：持久化 skipHighRiskConfirm 并继续运行', async () => {
    seedRiskExample()
    setPending()
    track(mount(HighRiskConfirmModal))
    const cb = document.body.querySelector('input[type="checkbox"]') as HTMLInputElement
    cb.click()
    await nextTick()

    findButton('仍要运行').click()
    await flushPromises()

    expect(skipHighRiskConfirm.value).toBe(true)
    expect(window.sidecar.store.set).toHaveBeenCalledWith('safetyPrefs', { skipHighRiskConfirm: true })
    expect(window.sidecar.runExample).toHaveBeenCalled()
  })

  it('点关闭（X）等同取消：清空 pending、不运行', async () => {
    seedRiskExample()
    setPending()
    track(mount(HighRiskConfirmModal))

    ;(document.body.querySelector('button[aria-label="关闭"]') as HTMLElement).click()
    await flushPromises()

    expect(pendingHighRiskRun.value).toBeNull()
    expect(window.sidecar.runExample).not.toHaveBeenCalled()
  })
})

// ---------------------------------------------------------------------------
// AssetsPanel：上传 / 分组列举 / 删除确认
// ---------------------------------------------------------------------------
describe('AssetsPanel', () => {
  /** 模拟选择文件：jsdom 的 file input 只读 files，需用 defineProperty 注入。 */
  function dispatchFiles(input: HTMLInputElement, files: File[]): void {
    Object.defineProperty(input, 'files', { value: files, configurable: true })
    input.dispatchEvent(new Event('change'))
  }

  // 分组标题是独立的 div，文本恰好等于分组名。不能拿整面板文本判断：
  // 上传按钮文案「上传图片 / 文档」同时含「图片」「文档」，会假阳性。
  function groupLabels(root: Element): string[] {
    return Array.from(root.querySelectorAll('div'))
      .map((d) => (d.textContent || '').trim())
      .filter((t) => t === '图片' || t === '文档')
  }

  it('无资源时展示空态文案，不渲染任何分组标题', () => {
    const w = track(mount(AssetsPanel))
    expect(w.text()).toContain('尚未上传资源')
    expect(groupLabels(w.element)).toEqual([])
  })

  it('按 is_image 分组展示（图片在前），并格式化体积', () => {
    assets.value = [
      makeAsset({ filename: 'pic.png', is_image: true, size: 2048 }),
      makeAsset({ filename: 'note.md', is_image: false, size: 300 })
    ]
    const w = track(mount(AssetsPanel))
    const text = w.text()
    expect(groupLabels(w.element)).toEqual(['图片', '文档'])
    expect(text).toContain('pic.png')
    expect(text).toContain('note.md')
    expect(text).toContain('2.0 KB')
    expect(text).toContain('300 B')
  })

  it('只有单一类型时另一分组标题不出现', () => {
    assets.value = [makeAsset({ filename: 'pic.png', is_image: true })]
    const w = track(mount(AssetsPanel))
    expect(groupLabels(w.element)).toEqual(['图片'])
  })

  it('上传按钮在未选中示例或加载中时禁用，否则可用', async () => {
    const w = track(mount(AssetsPanel))
    const upload = (): HTMLButtonElement => findButton('上传图片', w.element)

    expect(upload().hasAttribute('disabled')).toBe(true)

    selectedId.value = 'ex-1'
    await nextTick()
    expect(upload().hasAttribute('disabled')).toBe(false)

    assetsLoading.value = true
    await nextTick()
    expect(upload().hasAttribute('disabled')).toBe(true)
  })

  it('点击上传按钮触发隐藏 file input 的 click', async () => {
    selectedId.value = 'ex-1'
    const w = track(mount(AssetsPanel))
    const input = w.get('input[type="file"]').element as HTMLInputElement
    const clickSpy = vi.spyOn(input, 'click')

    findButton('上传图片', w.element).click()
    await nextTick()
    expect(clickSpy).toHaveBeenCalledTimes(1)
  })

  it('选择文件后上传并刷新资源列表', async () => {
    selectedId.value = 'ex-1'
    vi.mocked(window.sidecar.listAssets).mockResolvedValue({ assets: [makeAsset({ filename: 'a.png' })] })
    const w = track(mount(AssetsPanel))
    const input = w.get('input[type="file"]').element as HTMLInputElement

    dispatchFiles(input, [new File(['hi'], 'a.png', { type: 'image/png' })])
    // uploadAssets 要经 File.arrayBuffer() 读二进制（jsdom 下由 FileReader 兜底），
    // 是异步 IO 而非微任务，flushPromises 不够——必须等调用真正落地，
    // 否则这个未完成的 Promise 会漂到下一个用例里，造成跨用例假阳性/假阴性。
    await vi.waitFor(() => expect(window.sidecar.uploadAsset).toHaveBeenCalled())

    // 线上字段名（sidecar 契约：id / filename / data）——客户端负责把 UI 口径翻译成线口径
    expect(window.sidecar.uploadAsset).toHaveBeenCalledWith({
      id: 'ex-1',
      filename: 'a.png',
      data: 'aGk='
    })
    expect(window.sidecar.listAssets).toHaveBeenCalledWith('ex-1')
    await vi.waitFor(() => expect(assets.value.map((a) => a.filename)).toEqual(['a.png']))
  })

  it('.py 文件被拒收（与示例脚本冲突），不发起上传', async () => {
    selectedId.value = 'ex-1'
    const w = track(mount(AssetsPanel))
    const input = w.get('input[type="file"]').element as HTMLInputElement

    dispatchFiles(input, [new File(['x'], 'evil.py')])
    await flushPromises()

    expect(window.sidecar.uploadAsset).not.toHaveBeenCalled()
    expect(toasts.value.at(-1)?.text).toContain('冲突，已拒绝')
  })

  it('超过 15MB 的文件被拒收，不发起上传', async () => {
    selectedId.value = 'ex-1'
    const w = track(mount(AssetsPanel))
    const input = w.get('input[type="file"]').element as HTMLInputElement
    const big = new File(['x'], 'big.bin')
    Object.defineProperty(big, 'size', { value: 16 * 1024 * 1024 })

    dispatchFiles(input, [big])
    await flushPromises()

    expect(window.sidecar.uploadAsset).not.toHaveBeenCalled()
    expect(toasts.value.at(-1)?.text).toContain('超过 15MB 限制')
  })

  it('未选中示例时选择文件不触发上传', async () => {
    const w = track(mount(AssetsPanel))
    const input = w.get('input[type="file"]').element as HTMLInputElement

    dispatchFiles(input, [new File(['hi'], 'a.png')])
    await flushPromises()

    expect(window.sidecar.uploadAsset).not.toHaveBeenCalled()
  })

  it('点「删除」弹出确认框并展示文件名', async () => {
    selectedId.value = 'ex-1'
    assets.value = [makeAsset({ filename: 'a.png' })]
    const w = track(mount(AssetsPanel))

    findButton('删除', w.element).click()
    await nextTick()

    const d = document.body.querySelector('[role="dialog"]')!
    expect(d.getAttribute('aria-label')).toBe('删除资源')
    expect(d.textContent).toContain('a.png')
    // 仅弹确认，尚未真正删除
    expect(window.sidecar.deleteAsset).not.toHaveBeenCalled()
  })

  it('确认删除后调用 deleteAsset 并用返回值刷新列表', async () => {
    selectedId.value = 'ex-1'
    assets.value = [makeAsset({ filename: 'a.png' })]
    vi.mocked(window.sidecar.deleteAsset).mockResolvedValue({ deleted: 'a.png', assets: [] })
    const w = track(mount(AssetsPanel))

    findButton('删除', w.element).click()
    await nextTick()
    const d = document.body.querySelector('[role="dialog"]')!
    findButton('删除', d).click()
    await flushPromises()

    expect(window.sidecar.deleteAsset).toHaveBeenCalledWith({ id: 'ex-1', filename: 'a.png' })
    expect(assets.value).toEqual([])
    expect(document.body.querySelector('[role="dialog"]')).toBeNull()
  })

  it('确认框「取消」关闭弹窗且不删除', async () => {
    selectedId.value = 'ex-1'
    assets.value = [makeAsset({ filename: 'a.png' })]
    const w = track(mount(AssetsPanel))

    findButton('删除', w.element).click()
    await nextTick()
    const d = document.body.querySelector('[role="dialog"]')!
    findButton('取消', d).click()
    await nextTick()

    expect(window.sidecar.deleteAsset).not.toHaveBeenCalled()
    expect(document.body.querySelector('[role="dialog"]')).toBeNull()
    expect(assets.value.map((a) => a.filename)).toEqual(['a.png'])
  })
})
