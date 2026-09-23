<script setup lang="ts">
// DetailPage：示例详情页（单例覆盖层，从旧 detail.ts + index.html 详情区移植）
// 结构：头部（返回/标题/标签/收藏/保存/停止/运行）+ 参数面板（可折叠）+ Monaco
//      + 下半区三标签（终端输出 / 资源 / 运行历史）
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { qualityBadgeCls } from '../../src/utils'
import { CATEGORY_META } from '../../src/category-meta'
import {
  assets,
  clearOutput,
  closeDetail,
  currentArgs,
  isDirty,
  isFavorite,
  isRunning,
  saving,
  saveExample,
  selectedExample,
  selectedId,
  stopRun,
  toggleFavorite,
  runFromDetail,
  runStatusText,
  outputDot
} from '../store'
import ArgsForm from './ArgsForm.vue'
import MonacoEditor from './MonacoEditor.vue'
import OutputPanel from './OutputPanel.vue'
import HistoryPanel from './HistoryPanel.vue'
import AssetsPanel from './AssetsPanel.vue'

const BTN_GHOST =
  'inline-flex items-center gap-1 px-3 py-[5px] border border-line-subtle rounded-md bg-transparent text-ink-dim text-[12px] font-[510] font-sans cursor-pointer whitespace-nowrap transition-all duration-[120ms] active:scale-[0.97] hover:bg-hover hover:text-ink disabled:opacity-[0.35] disabled:cursor-not-allowed'
const TAB_IDLE =
  'px-3 py-1 rounded-md text-[11px] font-[510] font-sans cursor-pointer border-0 bg-transparent text-ink-mute hover:text-ink transition-colors duration-[120ms]'
const TAB_ACTIVE = `${TAB_IDLE} bg-page text-ink`
const DOT_CLS: Record<string, string> = {
  idle: 'bg-ink-faint',
  running: 'bg-warn animate-pulse',
  success: 'bg-ok',
  error: 'bg-danger'
}

const argsCollapsed = ref(false)
const activeTab = ref<'output' | 'assets' | 'history'>('output')

const ex = selectedExample
const title = computed(() => {
  if (!ex.value) return '未选择示例'
  const base = ex.value.title || (ex.value.name || '').replace(/\.py$/i, '').replace(/[-_]/g, ' ')
  return base + (isDirty.value ? ' ●' : '')
})
const meta = computed(() => CATEGORY_META[ex.value?.category || ''] )

function switchTab(tab: 'output' | 'assets' | 'history'): void {
  activeTab.value = tab
}

function onKeydown(e: KeyboardEvent): void {
  if (!(e.ctrlKey || e.metaKey)) return
  if (e.key === 's') {
    e.preventDefault()
    void saveExample()
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (!isRunning.value) runFromDetail()
  } else if (e.key === '.') {
    e.preventDefault()
    if (isRunning.value) void stopRun()
  }
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <section v-if="ex" class="flex-1 min-w-0 min-h-0 flex flex-col bg-page overflow-hidden">
    <!-- 头部 -->
    <div class="flex items-center gap-3 px-4 py-2.5 bg-panel border-b border-line-subtle shrink-0">
      <button :class="`${BTN_GHOST} shrink-0`" @click="closeDetail()">← 返回</button>
      <span class="text-[16px] shrink-0">{{ ex.category === 'tools' ? '🧰' : '🐍' }}</span>
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2 min-w-0">
          <span class="text-[13px] font-[590] text-ink truncate tracking-[-0.005em]" :title="title">{{ title }}</span>
          <span
            v-if="meta"
            class="inline-flex items-center px-2 py-0.5 rounded-sm text-[9px] font-[590] uppercase tracking-[0.03em] shrink-0"
            :class="meta.cls"
            >{{ ex.category }}</span
          >
        </div>
        <div class="flex flex-wrap gap-1 mt-0.5">
          <span
            v-for="tag in (ex.tags || []).slice(0, 6)"
            :key="tag"
            class="inline-block text-[10px] px-2 py-0.5 bg-card rounded text-ink-dim font-mono font-[510]"
            >{{ tag }}</span
          >
        </div>
      </div>
      <span
        class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-[510] font-mono shrink-0"
        :class="qualityBadgeCls(ex.quality_score)"
        title="六维质量评分（0-100）"
        >★ {{ ex.quality_score ?? 0 }}</span
      >
      <div class="flex items-center gap-2 shrink-0">
        <button :class="BTN_GHOST" @click="toggleFavorite(ex.id)">
          {{ isFavorite(ex.id) ? '★ 已收藏' : '☆ 收藏' }}
        </button>
        <button :class="BTN_GHOST" :disabled="!isDirty || saving" title="保存 (Cmd+S)">
          {{ saving ? '保存中…' : '💾 保存' }}
        </button>
        <button
          class="inline-flex items-center gap-1 px-3 py-[5px] border border-danger rounded-md bg-danger text-white text-[12px] font-[510] font-sans cursor-pointer whitespace-nowrap transition-all duration-[120ms] active:scale-[0.97] enabled:hover:opacity-90 disabled:opacity-[0.35] disabled:cursor-not-allowed"
          :disabled="!isRunning"
          title="停止 (Cmd+.)"
          @click="stopRun()"
        >
          ■ 停止
        </button>
        <button
          class="inline-flex items-center gap-1 px-3 py-[5px] border border-accent rounded-md bg-accent text-white text-[12px] font-[510] font-sans cursor-pointer whitespace-nowrap shadow-elev-1 transition-all duration-[120ms] active:scale-[0.97] enabled:hover:bg-accent-hover enabled:hover:shadow-elev-2 disabled:opacity-[0.35] disabled:cursor-not-allowed"
          :disabled="isRunning || !selectedId"
          title="运行 (Cmd+Enter)"
          @click="runFromDetail()"
        >
          ▶ 运行
        </button>
      </div>
    </div>

    <!-- 参数面板（argparse 静态解析，可折叠；无参数整区隐藏） -->
    <div v-if="currentArgs.length > 0 || argsCollapsed" class="border-b border-line-subtle shrink-0 bg-panel">
      <div
        class="flex items-center gap-2 px-3 py-1.5 cursor-pointer select-none"
        @click="argsCollapsed = !argsCollapsed"
      >
        <span class="text-[11px] text-ink-mute transition-transform duration-[120ms]" :class="argsCollapsed ? '' : 'rotate-90'"
          >▶</span
        >
        <span class="text-[11.5px] font-[590] text-ink-dim">命令行参数</span>
        <span class="text-[11px] text-ink-faint font-mono">({{ currentArgs.length }})</span>
      </div>
      <ArgsForm v-show="!argsCollapsed" />
    </div>

    <!-- 源码（Monaco，可编辑 + 保存回写） -->
    <div class="flex-[1.2] min-h-0 flex flex-col border-b border-line-subtle">
      <div class="relative flex-1 min-h-0 bg-page overflow-hidden">
        <MonacoEditor />
      </div>
    </div>

    <!-- 下半区：终端输出 / 资源 / 运行历史 三标签 -->
    <div class="flex-1 min-h-0 flex flex-col">
      <div class="flex items-center gap-1 px-3 h-8 bg-panel border-b border-line-subtle shrink-0">
        <button :class="activeTab === 'output' ? TAB_ACTIVE : TAB_IDLE" @click="switchTab('output')">终端输出</button>
        <button :class="activeTab === 'assets' ? TAB_ACTIVE : TAB_IDLE" @click="switchTab('assets')">
          资源 <span v-if="assets.length" class="text-ink-faint font-mono">({{ assets.length }})</span>
        </button>
        <button :class="activeTab === 'history' ? TAB_ACTIVE : TAB_IDLE" @click="switchTab('history')">历史</button>
        <div class="flex-1"></div>
        <span class="inline-block w-2 h-2 rounded-full shrink-0" :class="DOT_CLS[outputDot]"></span>
        <button :class="BTN_GHOST" title="清空输出" @click="clearOutput()">清空</button>
      </div>
      <OutputPanel v-show="activeTab === 'output'" />
      <AssetsPanel v-show="activeTab === 'assets'" />
      <HistoryPanel v-show="activeTab === 'history'" />
    </div>
  </section>
</template>
