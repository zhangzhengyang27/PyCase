<script setup lang="ts">
// RunnerView：代码运行器视图（最基础的运行入口，语义从旧 runner.ts 移植）
// 左：示例快速搜索（名称匹配 Top 8）+ 只读源码预览（文件名并入预览头）；
// 右：单行参数 + 运行/停止 + 终端输出 + 结果图。工具条从三层减为两层。
// 明确不做：编辑（去详情页）、参数表单、资源、AI。
import { computed, ref, watch } from 'vue'
import { FileCode2, Play, Square } from 'lucide-vue-next'
import { isRunning, runStatusText } from '../src/store/detail'
import {
  clearRunnerOutput,
  runnerArgsLine,
  runnerCode,
  runnerExample,
  runnerHits,
  runnerQuery,
  runnerRun,
  selectRunnerExample
} from '../src/store/runner'
import { stopRun } from '../src/store/detail'
import OutputPanel from './OutputPanel.vue'
import BaseButton from './base/BaseButton.vue'
import BaseInput from './base/BaseInput.vue'

const selected = computed(() => runnerExample.value)

// 搜索下拉的键盘导航：↑↓ 移动高亮，Enter 选中，Esc 清空关闭
const hitIdx = ref(0)
watch([runnerQuery, runnerHits], () => {
  hitIdx.value = 0
})

function onSelect(id: string): void {
  selectRunnerExample(id)
}

function onSearchKey(e: KeyboardEvent): void {
  const hits = runnerHits.value
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    if (hits.length) hitIdx.value = (hitIdx.value + 1) % hits.length
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    if (hits.length) hitIdx.value = (hitIdx.value - 1 + hits.length) % hits.length
  } else if (e.key === 'Enter') {
    e.preventDefault()
    const hit = hits[Math.min(hitIdx.value, hits.length - 1)]
    if (hit) onSelect(hit.id)
  } else if (e.key === 'Escape') {
    e.preventDefault()
    runnerQuery.value = ''
  }
}

function onArgsEnter(): void {
  runnerRun()
}
</script>

<template>
  <section class="flex-1 min-w-0 min-h-0 flex bg-page overflow-hidden">
    <!-- 左：示例快速选择 + 只读源码 -->
    <div class="w-[40%] min-w-[300px] flex flex-col border-r border-line-subtle min-h-0">
      <div class="relative px-2.5 py-2 border-b border-line-subtle bg-panel shrink-0">
        <BaseInput
          v-model="runnerQuery"
          placeholder="快速查找示例（输入名称关键字）…"
          aria-label="快速查找示例"
          :spellcheck="false"
          @keydown="onSearchKey"
        />
        <div
          v-if="runnerQuery"
          class="absolute left-2.5 right-2.5 top-full z-50 max-h-[320px] overflow-y-auto bg-panel border border-line-subtle rounded-panel shadow-elev-3"
        >
          <div v-if="runnerHits.length === 0" class="px-3 py-2 text-control text-ink-faint">无匹配示例</div>
          <button
            v-for="(e, i) in runnerHits"
            :key="e.id"
            class="w-full flex items-center gap-2 px-3 py-1.5 text-left border-0 bg-transparent cursor-pointer text-control text-ink-dim hover:bg-hover hover:text-ink"
            :class="i === hitIdx ? 'bg-accent/15 text-ink' : ''"
            :data-active="i === hitIdx"
            @click="onSelect(e.id)"
            @mousemove="hitIdx = i"
          >
            <FileCode2 :size="13" class="shrink-0 text-ink-faint" />
            <span class="truncate">{{ e.name }}</span>
            <span class="ml-auto shrink-0 text-caption text-ink-faint font-mono">{{ e.quality_score ?? 0 }}</span>
          </button>
        </div>
      </div>
      <div class="flex-1 min-h-0 flex flex-col console">
        <div
          v-if="selected"
          class="flex items-center gap-1.5 px-3 h-7 border-b border-line-hairline text-caption text-ink-mute font-mono shrink-0"
        >
          <FileCode2 :size="12" />
          <span class="truncate lowercase tracking-[0.02em]">{{ selected.name }}</span>
        </div>
        <pre
          class="flex-1 min-h-0 overflow-auto m-0 px-4 py-3 font-mono text-control leading-[1.55] text-console whitespace-pre"
          >{{
            selected
              ? runnerCode || '正在读取源码…'
              : '在上方搜索并选择示例，代码将在此只读预览。\n修改代码请进示例详情页。'
          }}</pre>
      </div>
    </div>

    <!-- 右：单行参数 + 运行 + 输出 + 结果图 -->
    <div class="flex-1 min-w-0 flex flex-col min-h-0">
      <div class="flex items-center gap-2 px-2.5 py-2 border-b border-line-subtle bg-panel shrink-0">
        <span class="text-caption text-ink-mute shrink-0">参数</span>
        <input
          v-model="runnerArgsLine"
          type="text"
          aria-label="命令行参数"
          :spellcheck="false"
          class="flex-1 min-w-0 h-7 px-2 bg-page border border-line rounded-control text-ink text-control font-mono outline-none transition-[border-color,box-shadow] dur-fast placeholder:text-ink-faint hover:border-line-strong focus:border-accent focus:shadow-elev-focus"
          placeholder="命令行参数，空格分隔（如 --width 100 --name demo）"
          @keydown.enter.prevent="onArgsEnter"
        />
        <BaseButton v-if="isRunning" title="停止 (Cmd+.)" @click="stopRun()"> <Square :size="13" /> 停止 </BaseButton>
        <BaseButton v-else variant="primary" :disabled="!selected" title="运行 (Cmd+Enter)" @click="runnerRun()">
          <Play :size="13" /> 运行
        </BaseButton>
      </div>
      <div class="flex items-center justify-between px-3 h-8 border-b border-line-subtle bg-panel shrink-0">
        <div class="flex items-center gap-2">
          <span
            class="inline-block w-2 h-2 rounded-full shrink-0"
            :class="{
              'bg-ink-faint': !isRunning && runStatusText === '就绪',
              'bg-warn animate-pulse': isRunning,
              'bg-ok': !isRunning && runStatusText === '运行成功',
              'bg-danger': !isRunning && (runStatusText === '运行失败' || runStatusText === '启动失败')
            }"
          ></span>
          <span class="text-caption font-medium text-ink-mute font-mono lowercase tracking-[0.02em]">终端输出</span>
        </div>
        <BaseButton size="sm" title="清空输出" @click="clearRunnerOutput()">清空</BaseButton>
      </div>
      <OutputPanel surface="runner" />
    </div>
  </section>
</template>
