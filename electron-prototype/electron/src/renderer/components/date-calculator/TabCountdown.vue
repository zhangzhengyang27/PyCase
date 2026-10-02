<script setup lang="ts">
// TabCountdown：正倒计时——d1/d2 各自距今天数 + 纪念日前瞻（未来最近 3 个）。
import { computed } from 'vue'
import { daysFromToday, formatYMD, parseDate, todayYMD, upcomingAnniversaries, type DateYMD } from '../../src/date-core'
import { dateA, dateB } from '../../src/store/interactive'

// 显式注解而非 as const + 推断：避免 map 分支（date: null / DateYMD）凹出联合类型问题。
interface CountdownRow {
  key: 'a' | 'b'
  label: string
  raw: string
  date: DateYMD | null
  delta: number
  list: Array<{ date: string; label: string }>
}

const rows = computed<CountdownRow[]>(() => {
  const today = todayYMD()
  const inputs: Array<{ key: 'a' | 'b'; label: string; raw: string }> = [
    { key: 'a', label: '起点', raw: dateA.value },
    { key: 'b', label: '终点', raw: dateB.value }
  ]
  return inputs.map((it): CountdownRow => {
    const v = parseDate(it.raw)
    if (!v) return { ...it, date: null, delta: 0, list: [] }
    return {
      ...it,
      date: v,
      delta: daysFromToday(v, today),
      list: upcomingAnniversaries(v, today, 3).map((x) => ({ date: formatYMD(x.date), label: x.label }))
    }
  })
})

function deltaText(n: number): string {
  if (n === 0) return '就是今天'
  return n > 0 ? `还有 ${n} 天` : `已过 ${-n} 天`
}
</script>

<template>
  <div class="grid grid-cols-2 gap-4 pt-4 pb-2">
    <div v-for="r in rows" :key="r.key" class="surface-card p-4" :data-testid="`cd-${r.key}`">
      <div class="text-caption text-ink-mute mb-2">{{ r.label }} · {{ r.raw }}</div>
      <template v-if="r.date">
        <div class="font-semibold text-ink" style="font-size: 30px" data-testid="cd-delta">{{ deltaText(r.delta) }}</div>
        <ul class="mt-3 mb-0 pl-4 list-disc text-control text-ink-dim flex flex-col gap-1">
          <li v-for="m in r.list" :key="m.label">{{ m.date }} · {{ m.label }}</li>
        </ul>
      </template>
      <div v-else class="text-control text-ink-mute">无效日期</div>
    </div>
  </div>
</template>
