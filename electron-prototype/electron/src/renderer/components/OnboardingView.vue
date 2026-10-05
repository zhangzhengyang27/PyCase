<script setup lang="ts">
// OnboardingView：首启引导页（A5.5 板 2 / 板 3）
// 关键约束：环境未就绪时「开始浏览」始终可用——浏览、搜索、读代码都不依赖运行环境，
// 只有「运行」需要。步骤状态全部来自 sidecar 的 env_status / env_progress，前端不猜、不编造。
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Code2, FolderOpen, LayoutGrid, LibraryBig, Play } from 'lucide-vue-next'
import {
  appInfo,
  dismissOnboarding,
  envStatus,
  openLog,
  retryEnvPrepare,
  useSystemPython,
  type EnvStatus
} from '../src/store/env'
import { modKeyLabel } from '../src/platform'
import BaseButton from './base/BaseButton.vue'

const modKey = modKeyLabel()
const env = computed<EnvStatus | null>(() => envStatus.value)

const PHASES: Array<{ key: EnvStatus['phase']; label: string; note: string }> = [
  { key: 'preparing', label: '安装共享依赖（.venv）', note: '通常 2–5 分钟' },
  { key: 'indexing', label: '建立示例索引', note: '' },
  { key: 'warming', label: '预检可运行性', note: '' }
]

type StepState = 'done' | 'active' | 'pending' | 'failed'
const ORDER: EnvStatus['phase'][] = ['starting', 'preparing', 'indexing', 'warming', 'ready']

function stateOf(phase: EnvStatus['phase']): StepState {
  const e = env.value
  if (!e) return 'pending'
  if (e.phase === 'failed') {
    // 失败归谁：sidecar 直接上报失败的步骤（failed_at），前端不猜
    const at = e.failed_at || 'preparing'
    const idx = ORDER.indexOf(phase)
    const atIdx = ORDER.indexOf(at)
    if (idx < atIdx) return 'done'
    if (idx === atIdx) return 'failed'
    return 'pending'
  }
  const cur = ORDER.indexOf(e.phase)
  const idx = ORDER.indexOf(phase)
  if (cur > idx) return 'done'
  if (cur === idx) return e.phase === 'ready' ? 'done' : 'active'
  return 'pending'
}

const ready = computed(() => env.value?.phase === 'ready')
const busy = computed(() => !!env.value && env.value.phase !== 'ready' && env.value.phase !== 'failed')

// 已用时：用 sidecar 上报的「开始时刻」实时推算——事件之间的停顿也要走秒，不是冻结值
const now = ref(Date.now() / 1000)
let ticker: ReturnType<typeof setInterval> | null = null
onMounted(() => {
  ticker = setInterval(() => (now.value = Date.now() / 1000), 1000)
  // 全屏接管层即模态：初始焦点落主操作（审计 P2；失败态时 .d-primary 是「重试」）
  document.querySelector<HTMLButtonElement>('[data-testid="onboarding"] .d-actions .d-primary')?.focus()
})
onBeforeUnmount(() => {
  if (ticker) clearInterval(ticker)
})

const elapsed = computed(() => {
  const started = env.value?.started_at
  const ms = started ? (now.value - started) * 1000 : (env.value?.elapsed_ms ?? 0)
  const s = Math.max(0, Math.round(ms / 1000))
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
})

const versionText = computed(() => (appInfo.value.version ? `v${appInfo.value.version}` : ''))
</script>

<template>
  <div
    data-testid="onboarding"
    role="dialog"
    aria-modal="true"
    aria-label="首次启动引导"
    class="fixed inset-0 z-[1300] bg-page flex items-center justify-center p-5 overflow-y-auto"
  >
    <div class="w-[620px] max-w-full bg-card border border-line-hairline rounded-overlay shadow-elev-3 overflow-hidden">
      <div class="flex items-center gap-2.5 px-4.5 pt-4 pb-3">
        <span
          class="w-[30px] h-[30px] rounded-control bg-accent text-on-accent inline-flex items-center justify-center shrink-0"
        >
          <LibraryBig :size="16" :stroke-width="1.5" />
        </span>
        <span class="min-w-0">
          <span class="block text-title font-semibold text-ink truncate">示例库</span>
          <span class="block text-caption text-ink-mute truncate">Python 示例管理器</span>
        </span>
        <span class="ml-auto text-caption text-ink-mute font-mono shrink-0">{{ versionText }}</span>
      </div>

      <p class="m-0 px-4.5 pb-3.5 text-body text-ink-dim leading-[1.65]">
        内置
        <b class="text-ink">{{ env?.examples ?? '…' }} 条 Python 示例</b
        >：浏览、运行、改代码都在一个窗口里完成。<template v-if="!ready"
          >首次启动需要几分钟准备运行环境，这一步不会挡住浏览。</template
        ><template v-else>运行环境已就绪，可以直接运行任何示例。</template>
      </p>

      <div class="grid grid-cols-3 gap-2.5 px-4.5 pb-3.5">
        <div class="border border-line-hairline rounded-card bg-inset p-2.5">
          <LayoutGrid :size="15" :stroke-width="1.5" class="text-ink-dim" />
          <div class="text-caption font-semibold mt-1.5">浏览</div>
          <div class="text-caption text-ink-dim leading-[1.55] mt-0.5">
            按主题分区逛；{{ modKey }} K 搜名称、标签或代码。
          </div>
        </div>
        <div class="border border-line-hairline rounded-card bg-inset p-2.5">
          <Play :size="15" :stroke-width="1.5" class="text-ink-dim" />
          <div class="text-caption font-semibold mt-1.5">运行</div>
          <div class="text-caption text-ink-dim leading-[1.55] mt-0.5">独立子进程、实时输出；生成的图片自动收集。</div>
        </div>
        <div class="border border-line-hairline rounded-card bg-inset p-2.5">
          <Code2 :size="15" :stroke-width="1.5" class="text-ink-dim" />
          <div class="text-caption font-semibold mt-1.5">编辑</div>
          <div class="text-caption text-ink-dim leading-[1.55] mt-0.5">Monaco 编辑器；保存后可随时恢复原始版本。</div>
        </div>
      </div>

      <!-- 环境准备：状态全部来自 sidecar 上报 -->
      <div class="mx-4.5 mb-3.5 border border-line-hairline rounded-card bg-inset">
        <div class="flex items-center gap-2 px-3 py-2.5 border-b border-line-hairline">
          <span
            class="stat-dot shrink-0"
            :class="ready ? 'bg-ok' : env?.phase === 'failed' ? 'bg-danger' : 'bg-warn animate-pulse'"
          ></span>
          <span class="text-caption text-ink-dim">
            {{ ready ? '运行环境已就绪' : env?.phase === 'failed' ? '环境准备失败' : '正在准备运行环境' }}
            <template v-if="env?.mode === 'system'">（已切换为系统 Python）</template>
          </span>
          <span class="ml-auto text-caption text-ink-mute font-mono">已用时 {{ elapsed }}</span>
        </div>
        <div v-if="busy" class="h-[3px] mx-3 my-2 bg-line-hairline rounded-full overflow-hidden">
          <i class="block h-full w-1/3 bg-accent animate-indeterminate"></i>
        </div>
        <div class="px-3 py-2.5 flex flex-col gap-1.5">
          <div class="flex items-center gap-2.5 text-caption">
            <span class="w-3.5 h-3.5 inline-flex items-center justify-center shrink-0">
              <span class="stat-dot" :class="stateOf('starting') === 'done' ? 'bg-ok' : 'bg-warn animate-pulse'"></span>
            </span>
            <span class="text-ink">启动 Python 服务</span>
            <span class="ml-auto text-ink-mute">{{ stateOf('starting') === 'done' ? '已完成' : '进行中' }}</span>
          </div>
          <div
            v-for="p in PHASES"
            :key="p.key"
            class="flex items-center gap-2.5 text-caption"
            :class="stateOf(p.key) === 'failed' ? 'text-danger' : ''"
          >
            <span class="w-3.5 h-3.5 inline-flex items-center justify-center shrink-0">
              <span v-if="stateOf(p.key) === 'done'" class="stat-dot bg-ok"></span>
              <span v-else-if="stateOf(p.key) === 'active'" class="spinner"></span>
              <span v-else-if="stateOf(p.key) === 'failed'" class="stat-dot bg-danger"></span>
              <span v-else class="ring"></span>
            </span>
            <span :class="stateOf(p.key) === 'failed' ? 'text-danger' : 'text-ink'">{{ p.label }}</span>
            <span class="ml-auto" :class="stateOf(p.key) === 'failed' ? 'text-danger' : 'text-ink-mute'">
              <template v-if="stateOf(p.key) === 'failed'">{{ env?.error || '准备失败' }}</template>
              <template v-else-if="stateOf(p.key) === 'done'">已完成</template>
              <template v-else-if="stateOf(p.key) === 'active'">进行中</template>
              <template v-else>{{ p.note || '等待中' }}</template>
            </span>
          </div>
        </div>
      </div>

      <div class="d-actions px-4.5 pb-4">
        <BaseButton v-if="env?.phase === 'failed'" class="d-primary" @click="retryEnvPrepare()">重试</BaseButton>
        <BaseButton v-if="env?.phase === 'failed'" @click="openLog()">查看准备日志</BaseButton>
        <BaseButton v-if="env?.phase === 'failed' && env?.mode !== 'system'" variant="ghost" @click="useSystemPython()">
          用系统 Python 继续
        </BaseButton>
        <template v-if="env?.phase !== 'failed'">
          <BaseButton class="d-primary" variant="primary" @click="dismissOnboarding()">开始浏览</BaseButton>
          <BaseButton variant="ghost" @click="dismissOnboarding()">跳过引导</BaseButton>
        </template>
      </div>

      <div class="flex items-center gap-2 px-4.5 py-2.5 border-t border-line-hairline text-caption text-ink-mute">
        <FolderOpen :size="12" :stroke-width="1.5" class="shrink-0" />
        <span v-if="env?.phase === 'failed'">浏览示例不受影响；未装依赖的示例会在运行时提示「缺依赖」。</span>
        <span v-else>环境在后台继续准备；就绪后运行按钮可用，状态栏会显示「环境已就绪」。</span>
      </div>
    </div>
  </div>
</template>
