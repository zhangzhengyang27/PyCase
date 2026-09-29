<script setup lang="ts">
// HistoryPanel：当前示例的运行历史（最近 20 条，可重跑）
// 徽章配色改走状态令牌（原为硬编码 GitHub 色值）。
import { rerunEntry, detailHistory } from '../store'

// v2 状态语言：圆点 + 中性文字（成功中性、失败红字），底色徽章退役
const RERUN_CLS =
  'inline-flex items-center px-2 py-0.5 border border-line-hairline rounded-control bg-transparent text-ink-dim text-caption cursor-pointer transition-colors dur-fast hover:bg-hover hover:text-ink shrink-0'

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
      class="flex items-center justify-between gap-3 px-3 py-1.5 border-b border-line-hairline hover:bg-hover"
    >
      <div class="flex items-center gap-2.5 min-w-0 flex-1">
        <span class="inline-flex items-center gap-1 shrink-0 text-caption" :class="h.ok ? 'text-ink-mute' : 'text-danger'">
          <span class="stat-dot" :class="h.ok ? 'bg-ok' : 'bg-danger'"></span>{{ h.ok ? '成功' : `失败 ${h.exit_code}` }}
        </span>
        <span class="text-caption text-ink-dim truncate">
          {{ formatTime(h.ts) }} · {{ formatDuration(h.duration_ms) }}
          <template v-if="h.args && h.args.length"> · 参数 {{ h.args.join(' ') }}</template>
        </span>
      </div>
      <button :class="RERUN_CLS" title="回填记录参数并运行" @click="rerunEntry(h)">重跑</button>
    </div>
  </div>
</template>
