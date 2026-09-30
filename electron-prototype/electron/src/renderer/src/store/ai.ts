// ai.ts：AI 代码解释域（DeepSeek 流式；设置弹窗 / 首次外发告知 / 关面板即停止）。
import { reactive, ref } from 'vue'
import { pushToast } from '../../toast'
import { api } from '../sidecar-client'
import { editor, requestConfirm, selectedExample, selectedId } from './detail'

// ===========================================================================
// AI 代码解释（DeepSeek 流式；语义从旧 ai.ts 移植：设置弹窗 / 首次外发告知 /
// run_id 匹配的流式订阅 / 关面板即停止）
// ===========================================================================
export const aiSettings = reactive({
  hasKey: false,
  model: 'deepseek-chat',
  baseUrl: 'https://api.deepseek.com',
  acknowledged: false
})
export const aiRunId = ref('')
export const aiPanelOpen = ref(false)
export const aiSettingsOpen = ref(false)
export const aiStatus = ref('正在准备…')
export const aiStatusError = ref(false)
export const aiOutputText = ref('')
export const aiShowStop = ref(false)

export async function loadAISettings(): Promise<void> {
  try {
    const s = (await api.aiGetSettings()) as {
      hasKey?: boolean
      model?: string
      baseUrl?: string
      acknowledged?: boolean
    }
    aiSettings.hasKey = !!s.hasKey
    aiSettings.model = s.model || 'deepseek-chat'
    aiSettings.baseUrl = s.baseUrl || 'https://api.deepseek.com'
    aiSettings.acknowledged = !!s.acknowledged
  } catch (err) {
    console.error('[ai] 加载设置失败:', err)
  }
}

export function openAISettings(): void {
  aiSettingsOpen.value = true
}
export function closeAISettings(): void {
  aiSettingsOpen.value = false
}

export function setAIStatus(text: string, isError = false): void {
  aiStatus.value = text
  aiStatusError.value = isError
}

export function openAIPanel(): void {
  // 关闭旧面板（如有进行中的解释则一并终止）
  closeAIPanel()
  aiPanelOpen.value = true
  aiOutputText.value = ''
  setAIStatus('正在准备…')
}

export function closeAIPanel(): void {
  // 关闭面板即终止解释：否则流式请求继续消耗 token，结果也无处展示
  if (aiRunId.value) {
    void api.aiStop(aiRunId.value).catch(() => {})
    aiRunId.value = ''
  }
  aiPanelOpen.value = false
}

export function stopAI(): void {
  if (!aiRunId.value) return
  void api.aiStop(aiRunId.value).catch(() => {})
  setAIStatus('已停止')
  aiShowStop.value = false
}

export async function explainSelectedCode(): Promise<void> {
  // 上下文守卫：AI 解释依赖详情页 Monaco 中的代码
  if (!selectedId.value) {
    pushToast('info', '请先在画廊或工具箱打开示例详情，再使用 AI 解释')
    return
  }
  // 防重入：流式解释进行中忽略重复点击
  if (aiRunId.value) return
  // 无 key → 引导设置
  if (!aiSettings.hasKey) {
    openAISettings()
    return
  }
  // 首次使用外发告知（应用内弹窗；同意状态可在设置里复核与撤回）
  if (!aiSettings.acknowledged) {
    requestConfirm(
      `代码解释会把选中的代码发送到 ${aiSettings.baseUrl} 处理。同意后可在「设置 → 代码外发」里撤回。`,
      () => {
        aiSettings.acknowledged = true
        void api.aiSetSettings({ acknowledged: true })
        void explainSelectedCode()
      },
      { title: '把代码发送到外部服务？', confirmLabel: '同意并解释' }
    )
    return
  }

  const code = editor?.getSelectedText?.() || editor?.getValue() || ''
  if (!code.trim()) {
    // 先建面板再提示：状态行依赖面板节点存在
    openAIPanel()
    setAIStatus('没有可解释的代码', true)
    return
  }
  const fileName = selectedExample.value?.name || 'example.py'

  openAIPanel()
  setAIStatus('正在请求 DeepSeek…')
  try {
    const res = (await api.aiExplain(code, fileName)) as { status?: string; error?: string; run_id?: string }
    if (res.status === 'error' || res.error) {
      const err = res.error || 'unknown'
      if (err === 'no_api_key') {
        aiSettings.hasKey = false
        setAIStatus('API Key 未配置，请先在设置中填写', true)
      } else {
        setAIStatus('请求失败：' + err, true)
      }
      return
    }
    aiRunId.value = res.run_id || ''
    setAIStatus('正在生成解释…')
    aiShowStop.value = true
  } catch (err) {
    setAIStatus('调用失败：' + (err as Error).message, true)
    aiShowStop.value = false
  }
}

export function initAIEvents(): void {
  api.on('aiExplainChunk', (data) => {
    if (data.run_id && aiRunId.value && data.run_id !== aiRunId.value) return
    aiOutputText.value += data.text || ''
  })
  api.on('aiExplainDone', (data) => {
    if (data.run_id && aiRunId.value && data.run_id !== aiRunId.value) return
    const tokens = data.tokens ? `（约 ${data.tokens} tokens）` : ''
    setAIStatus('完成' + tokens)
    aiRunId.value = ''
    aiShowStop.value = false
  })
  api.on('aiExplainError', (data) => {
    if (data.run_id && aiRunId.value && data.run_id !== aiRunId.value) return
    setAIStatus('生成失败：' + (data.error || 'unknown'), true)
    aiRunId.value = ''
    aiShowStop.value = false
  })
}

export async function copyAIOutput(): Promise<void> {
  if (!aiOutputText.value) return
  try {
    await navigator.clipboard.writeText(aiOutputText.value)
    setAIStatus('已复制到剪贴板')
  } catch {
    setAIStatus('复制失败', true)
  }
}
