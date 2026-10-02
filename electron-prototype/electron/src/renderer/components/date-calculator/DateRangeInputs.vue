<script setup lang="ts">
// DateRangeInputs：全局日期对输入行（四 Tab 共享）。
// 原生 input[type=date]；星期标注随值即时更新；解析失败标红；
// 预设是单日期快捷值，写入最近聚焦的日期框（默认 d1）。
import { computed, ref } from 'vue'
import { ArrowLeftRight } from 'lucide-vue-next'
import { formatYMD, parseDate, todayYMD, weekdayZh } from '../../src/date-core'
import { dateA, dateB, swapDates } from '../../src/store/interactive'
import BaseButton from '../base/BaseButton.vue'

const lastFocused = ref<'a' | 'b'>('a')
const validA = computed(() => !!parseDate(dateA.value))
const validB = computed(() => !!parseDate(dateB.value))
const wdA = computed(() => {
  const v = parseDate(dateA.value)
  return v ? weekdayZh(v) : '无效日期'
})
const wdB = computed(() => {
  const v = parseDate(dateB.value)
  return v ? weekdayZh(v) : '无效日期'
})

const INPUT_CLS =
  'px-2 h-8 bg-page border rounded-control text-ink text-control font-mono outline-none transition-[border-color] dur-fast hover:border-line-strong focus:border-accent'

const PRESETS: Array<{ label: string; value: () => string }> = [
  { label: '今天', value: () => formatYMD(todayYMD()) },
  { label: '今年元旦', value: () => `${todayYMD().y}-01-01` },
  {
    label: '明年今天',
    value: () => {
      const t = todayYMD()
      return `${t.y + 1}-${String(t.m).padStart(2, '0')}-${String(t.d).padStart(2, '0')}`
    }
  },
  { label: '闰年日', value: () => '2024-02-29' }
]

function applyPreset(value: string): void {
  if (lastFocused.value === 'a') dateA.value = value
  else dateB.value = value
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-2">
    <div class="flex items-center gap-1.5">
      <input
        v-model="dateA"
        type="date"
        data-testid="date-a"
        :class="[INPUT_CLS, validA ? 'border-line' : 'border-danger']"
        aria-label="起始日期"
        @focus="lastFocused = 'a'"
      />
      <span class="text-caption text-ink-mute w-[58px]" data-testid="weekday-a">{{ wdA }}</span>
    </div>
    <BaseButton square title="交换起止日期" aria-label="交换起止日期" @click="swapDates()">
      <ArrowLeftRight :size="14" />
    </BaseButton>
    <div class="flex items-center gap-1.5">
      <input
        v-model="dateB"
        type="date"
        data-testid="date-b"
        :class="[INPUT_CLS, validB ? 'border-line' : 'border-danger']"
        aria-label="结束日期"
        @focus="lastFocused = 'b'"
      />
      <span class="text-caption text-ink-mute w-[58px]" data-testid="weekday-b">{{ wdB }}</span>
    </div>
    <div class="flex gap-1.5 ml-auto">
      <button
        v-for="p in PRESETS"
        :key="p.label"
        class="border border-line rounded-control px-2 h-7 text-caption text-ink-mute hover:text-accent hover:border-accent bg-transparent cursor-pointer transition-colors dur-fast"
        data-testid="dc-preset"
        @click="applyPreset(p.value())"
      >
        {{ p.label }}
      </button>
    </div>
  </div>
</template>
