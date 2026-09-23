<script setup lang="ts">
// HistoryPanel：当前示例的运行历史（最近 20 条，可重跑）
// 徽章配色改走状态令牌（原为硬编码 GitHub 色值）。
import { rerunEntry, detailHistory } from '../store'

const BADGE_OK_CLS = 'shrink-0 text-caption font-[590] px-2 py-0.5 rounded-full text-ok bg-ok-bg'
const BADGE_FAIL_CLS = 'shrink-0 text-caption font-[590] px-2 py-0.5 rounded-full text-danger bg-danger-bg'
const RERUN_CLS =
  'inline-flex items-center px-2 py-0.5 border border-line-subtle rounded-control bg-transparent text-ink-dim text-caption font-[510] cursor-pointer hover:bg-hover hover:text-ink shrink-0'

// 月日时分秒交给 Intl（zh-CN 两位数字格式），不再手写 pad 拼接
const TIME_FMT = new Intl.DateTimeFormat('zh-CN', {
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: false
})
function formatTime(iso: string): string {
  return TIME_FMT.format(new Date(iso))
}
function formatDuration(ms: number): string {
  return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`
}
</script>

<template>
  <div class="py-1 flex-1 min-h-0 overflow-y-auto">
    <div v-if="detailHistory.length === 0" class="text-ink-mute text-control px-3 py-2">该示例还没有运行记录</div>
    <div
      v-for="(h, i) in detailHistory"
      :key="h.ts + String(i)"
      class="flex items-center justify-between gap-3 px-3 py-1.5 border-b border-line-subtle hover:bg-hover"
    >
      <div class="flex items-center gap-2.5 min-w-0 flex-1">
        <span :class="h.ok ? BADGE_OK_CLS : BADGE_FAIL_CLS">{{ h.ok ? '成功' : `失败 ${h.exit_code}` }}</span>
        <span class="text-caption text-ink-dim truncate">
          {{ formatTime(h.ts) }} · {{ formatDuration(h.duration_ms) }}
          <template v-if="h.args && h.args.length"> · 参数 {{ h.args.join(' ') }}</template>
        </span>
      </div>
      <button :class="RERUN_CLS" title="回填记录参数并运行" @click="rerunEntry(h)">重跑</button>
    </div>
  </div>
</template>
