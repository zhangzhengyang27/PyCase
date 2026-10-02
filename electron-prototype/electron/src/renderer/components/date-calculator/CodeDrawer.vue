<script setup lang="ts">
// CodeDrawer：Python 代码抽屉——随 Tab 与输入实时生成等价代码；默认折叠。
// 只读 Monaco 用独立实例（绝不 import MonacoEditor.vue / detail store 的 registerEditor——
// 那会劫持详情页的单例编辑器，这正是本组件自己 create/dispose 的理由）；
// 复制 / 运行（sidecar adhoc code）/ 停止，输出就地显示。
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { ChevronUp, Copy, Play, Square } from 'lucide-vue-next'
import { applyMonacoTheme, currentMonacoTheme, monaco } from '../../monaco'
import { pushToast } from '../../toast'
import { parseDate } from '../../src/date-core'
import { genArithCode, genCalendarCode, genCountdownCode, genDiffCode } from '../../src/py-codegen'
import { DATE_CALC_ID } from '../../src/interactive-tools'
import { activeTab, arithRows, dateA, dateB } from '../../src/store/interactive'
import { runBusy, runExitCode, runOutput, runSnippet, stopSnippet } from '../../src/store/date-run'
import BaseButton from '../base/BaseButton.vue'

const open = ref(false)

const code = computed(() => {
  const a = parseDate(dateA.value)
  const b = parseDate(dateB.value)
  if (!a || !b) return '# 补全两个有效日期后自动生成代码'
  if (activeTab.value === 'diff') return genDiffCode(a, b)
  if (activeTab.value === 'countdown') return genCountdownCode(a, b)
  if (activeTab.value === 'calendar') return genCalendarCode(a, b)
  return genArithCode(a, b, arithRows.value)
})

const container = ref<HTMLDivElement | null>(null)
let ed: ReturnType<typeof monaco.editor.create> | null = null

function createEditor(): void {
  if (!container.value || ed) return
  applyMonacoTheme()
  ed = monaco.editor.create(container.value, {
    value: code.value,
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

watch(code, (v) => ed?.setValue(v))
onBeforeUnmount(() => {
  ed?.dispose()
  ed = null
})

async function copyCode(): Promise<void> {
  try {
    await navigator.clipboard.writeText(code.value)
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
      @click="toggle()"
    >
      <ChevronUp :size="14" :style="open ? '' : 'transform: rotate(180deg)'" />
      Python 代码<span class="text-caption text-ink-faint">随当前 Tab 与输入实时生成</span>
    </button>
    <div v-if="open" class="px-8 pb-4 flex flex-col gap-2">
      <div class="flex items-center gap-2">
        <BaseButton data-testid="drawer-copy" title="复制代码" @click="copyCode()">
          <Copy :size="14" />
        </BaseButton>
        <BaseButton
          variant="primary"
          data-testid="drawer-run"
          title="用 Python 真实运行并核对结果"
          :disabled="runBusy"
          @click="runSnippet(DATE_CALC_ID, code)"
        >
          <Play :size="14" /> 运行
        </BaseButton>
        <BaseButton v-if="runBusy" data-testid="drawer-stop" title="停止运行" @click="stopSnippet()">
          <Square :size="14" />
        </BaseButton>
        <span
          v-if="runExitCode !== null"
          class="text-caption"
          :class="runExitCode === 0 ? 'text-ink-mute' : 'text-danger'"
          data-testid="run-exit"
        >
          退出码 {{ runExitCode }}
        </span>
      </div>
      <div ref="container" class="h-[240px] border border-line rounded-control overflow-hidden bg-page" />
      <pre
        v-if="runOutput"
        class="m-0 p-3 max-h-[180px] overflow-auto text-control font-mono bg-page border border-line rounded-control whitespace-pre-wrap"
        data-testid="run-output"
        >{{ runOutput }}</pre
      >
    </div>
  </div>
</template>
