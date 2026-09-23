<script setup lang="ts">
// HistoryPanel：当前示例的运行历史（最近 20 条，可重跑）
import { rerunEntry, detailHistory } from '../store'

const BADGE_OK_CLS = 'shrink-0 text-[11px] font-[590] px-2 py-0.5 rounded-full text-[#1a7f37] bg-[rgba(63,185,80,0.14)]'
const BADGE_FAIL_CLS = 'shrink-0 text-[11px] font-[590] px-2 py-0.5 rounded-full text-[#cf222e] bg-[rgba(248,81,73,0.14)]'
const RERUN_CLS =
  'inline-flex items-center px-2 py-0.5 border border-line-subtle rounded-md bg-transparent text-ink-dim text-[11px] font-[510] cursor-pointer hover:bg-hover hover:text-ink shrink-0'

function pad(n: number): string {
  return String(n).padStart(2, '0')
}
function formatTime(iso: string): string {
  const d = new Date(iso)
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}
function formatDuration(ms: number): string {
  return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`
}
</script>

<template>
  <div class="py-1">
    <div v-if="detailHistory.length === 0" class="text-ink-mute text-[13px] px-3 py-2">该示例还没有运行记录</div>
    <div
      v-for="(h, i) in detailHistory"
      :key="h.ts + String(i)"
      class="flex items-center justify-between gap-3 px-3 py-1.5 border-b border-line-subtle hover:bg-[rgba(127,127,127,0.06)]"
    >
      <div class="flex items-center gap-2.5 min-w-0 flex-1">
        <span :class="h.ok ? BADGE_OK_CLS : BADGE_FAIL_CLS">{{ h.ok ? '成功' : `失败 ${h.exit_code}` }}</span>
        <span class="text-[11.5px] text-ink-dim truncate">
          {{ formatTime(h.ts) }} · {{ formatDuration(h.duration_ms) }}
          <template v-if="h.args && h.args.length"> · 参数 {{ h.args.join(' ') }}</template>
        </span>
      </div>
      <button :class="RERUN_CLS" title="回填记录参数并运行" @click="rerunEntry(h)">重跑</button>
    </div>
  </div>
</template>
