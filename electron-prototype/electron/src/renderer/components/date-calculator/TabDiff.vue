<script setup lang="ts">
// TabDiff：日期差——大数字天数 + 指标行 + 跨度色带（垂直叙事）。
import { computed } from 'vue'
import { diffRange, parseDate } from '../../src/date-core'
import { dateA, dateB } from '../../src/store/interactive'

const result = computed(() => {
  const a = parseDate(dateA.value)
  const b = parseDate(dateB.value)
  if (!a || !b) return null
  return { ...diffRange(a, b), span: `${a.y}年${a.m}月`, spanEnd: `${b.y}年${b.m}月` }
})
</script>

<template>
  <div v-if="!result" class="text-control text-ink-mute pt-10 text-center">请补全两个有效日期</div>
  <div v-else class="flex flex-col gap-5 items-center pt-4 pb-2">
    <div v-if="result.swapped" data-testid="swap-hint" class="text-caption text-warn">
      起点晚于终点，结果按较晚为终点计算
    </div>
    <div class="text-center">
      <div class="font-semibold text-ink leading-none m-0" style="font-size: 44px" data-testid="diff-days">
        {{ result.days }}<span class="text-control text-ink-mute font-normal ml-1">天</span>
      </div>
      <div class="text-control text-ink-mute mt-2" data-testid="diff-metrics">
        ≈ {{ result.weeks }} 周 · {{ result.norm.years }} 年 {{ result.norm.months }} 个月 {{ result.norm.days }} 天 ·
        含 {{ result.leapDays }} 个闰日
      </div>
    </div>
    <div class="flex gap-2 w-full">
      <div class="surface-card flex-1 py-2 text-center text-control" data-testid="weekday-start">
        起点 {{ result.weekday1 }}
      </div>
      <div class="surface-card flex-1 py-2 text-center text-control" data-testid="weekday-end">
        终点 {{ result.weekday2 }}
      </div>
    </div>
    <div class="w-full surface-card p-3">
      <div class="flex justify-between text-caption text-ink-faint mb-1.5">
        <span>{{ result.span }}</span><span>{{ result.spanEnd }}</span>
      </div>
      <div class="h-3 rounded-full overflow-hidden bg-accent/15">
        <div class="h-full w-full rounded-full bg-gradient-to-r from-accent/30 to-accent" />
      </div>
    </div>
  </div>
</template>
