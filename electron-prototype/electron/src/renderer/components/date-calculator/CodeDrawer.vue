<script setup lang="ts">
// CodeDrawer：Python 代码抽屉（通用组件）——代码内容由调用方以 props 传入，
// 本组件只负责展示（只读 Monaco 独立实例）、复制、运行与输出。
// 绝不 import MonacoEditor.vue / detail store 的 registerEditor——那会劫持详情页的
// 单例编辑器，这正是本组件自己 create/dispose 的理由。
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { ChevronUp, Copy, Download, Play, Square } from 'lucide-vue-next'
import { applyMonacoTheme, currentMonacoTheme, monaco } from '../../monaco'
import { pushToast } from '../../toast'
import { api } from '../../src/sidecar-client'
import {
  runBusy,
  runContext,
  runExitCode,
  runImages,
  runOutput,
  runSnippet,
  stopSnippet
} from '../../src/store/date-run'
import BaseButton from '../base/BaseButton.vue'

const props = defineProps<{ code: string; runId: string; contextKey?: string | null }>()

// 运行输出/产物图只显示属于本页上下文的运行（InteractiveToolPage 传实验室页的
// 「页面|类型」上下文）；不传 contextKey 的调用方保持原行为（恒显示）。
const runMatches = (): boolean => !props.contextKey || props.contextKey === runContext.value

const open = ref(false)

const container = ref<HTMLDivElement | null>(null)
let ed: ReturnType<typeof monaco.editor.create> | null = null

function createEditor(): void {
  if (!container.value || ed) return
  applyMonacoTheme()
  ed = monaco.editor.create(container.value, {
    value: props.code,
    language: 'python',
    theme: currentMonacoTheme(),
    readOnly: true,
    fontSize: 12,
    minimap: { enabled: false },
    automaticLayout: true,
    scrollBeyondLastLine: false,
    wordWrap: 'on'
  })
}

function toggle(): void {
  open.value = !open.value
  if (open.value) void nextTick(createEditor)
  else {
    ed?.dispose()
    ed = null
  }
}

watch(
  () => props.code,
  (v) => ed?.setValue(v)
)
onBeforeUnmount(() => {
  ed?.dispose()
  ed = null
})

async function downloadImage(url: string): Promise<void> {
  try {
    const r = await api.downloadResultImage(url)
    if (r.savedTo) pushToast('success', `已保存：${r.savedTo}`)
    else if (!r.canceled) pushToast('error', r.error || '保存失败')
  } catch {
    pushToast('error', '保存失败')
  }
}

async function copyCode(): Promise<void> {
  try {
    await navigator.clipboard.writeText(props.code)
    pushToast('success', '代码已复制')
  } catch {
    pushToast('error', '复制失败')
  }
}
</script>

<template>
  <div class="flex flex-col">
    <button
      class="flex items-center gap-2 px-8 py-2.5 border-0 bg-transparent text-control text-ink-mute hover:text-accent cursor-pointer select-none"
      data-testid="drawer-toggle"
      aria-label="切换 Python 代码抽屉"
      :aria-expanded="open"
      aria-controls="code-drawer-panel"
      @click="toggle()"
    >
      <ChevronUp :size="14" :style="open ? '' : 'transform: rotate(180deg)'" />
      Python 代码<span class="text-caption text-ink-faint">随当前输入实时生成</span>
    </button>
    <div v-if="open" id="code-drawer-panel" class="px-8 pb-4 flex flex-col gap-2">
      <div class="flex items-center gap-2">
        <BaseButton data-testid="drawer-copy" title="复制代码" @click="copyCode()">
          <Copy :size="14" />
        </BaseButton>
        <BaseButton
          variant="primary"
          data-testid="drawer-run"
          title="用 Python 真实运行并核对结果"
          :disabled="runBusy"
          @click="runSnippet(runId, code)"
        >
          <Play :size="14" /> 运行
        </BaseButton>
        <BaseButton v-if="runBusy" data-testid="drawer-stop" title="停止运行" @click="stopSnippet()">
          <Square :size="14" />
        </BaseButton>
        <span
          v-if="runExitCode !== null"
          aria-live="polite"
          class="text-caption"
          :class="runExitCode === 0 ? 'text-ink-mute' : 'text-danger'"
          data-testid="run-exit"
        >
          退出码 {{ runExitCode }}
        </span>
      </div>
      <div ref="container" class="h-[240px] border border-line rounded-control overflow-hidden bg-page" />
      <div v-if="runMatches() && runImages.length" class="flex flex-wrap gap-2" data-testid="run-images">
        <figure
          v-for="img in runImages"
          :key="img"
          class="m-0 border border-line rounded-control overflow-hidden bg-panel w-[160px]"
        >
          <img :src="img" alt="运行产物" loading="lazy" class="block w-full h-[110px] object-contain bg-page" />
          <figcaption class="flex items-center justify-end px-1.5 py-1">
            <button
              class="shrink-0 inline-flex items-center gap-1 px-1.5 py-0.5 text-caption border border-line rounded-control bg-panel text-ink-dim cursor-pointer transition-colors dur-fast hover:bg-hover hover:text-ink"
              type="button"
              @click="downloadImage(img)"
            >
              <Download :size="11" /> 下载
            </button>
          </figcaption>
        </figure>
      </div>
      <pre
        v-if="runMatches() && runOutput"
        aria-live="polite"
        class="m-0 p-3 max-h-[180px] overflow-auto text-control font-mono bg-page border border-line rounded-control whitespace-pre-wrap"
        data-testid="run-output"
        >{{ runOutput }}</pre>
    </div>
  </div>
</template>
