<script setup lang="ts">
// TabArithmetic：日期加减——增减行列表（目标 × 运算 × 数值 × 单位），即时出结果。
// 数值整数化两道防线：@change 失焦钳制（输入中不打扰）+ results 里 Math.trunc 兜底
// （防粘贴/滚轮写入小数）——小数 n 会让 month/year 的 Python 产物 TypeError。
import { computed } from 'vue'
import { Trash2, Plus } from 'lucide-vue-next'
import { addToDate, formatYMD, parseDate, weekdayZh } from '../../src/date-core'
import { arithRows, dateA, dateB, type ArithRow } from '../../src/store/interactive'

const UNITS: Array<{ v: ArithRow['unit']; label: string }> = [
  { v: 'day', label: '天' },
  { v: 'week', label: '周' },
  { v: 'month', label: '月' },
  { v: 'year', label: '年' }
]

const results = computed(() =>
  arithRows.value.map((r) => {
    const src = parseDate(r.target === 'd1' ? dateA.value : dateB.value)
    if (!src || !Number.isFinite(r.n)) return null
    const n = Math.trunc(r.n)
    const out = addToDate(src, r.op === '+' ? n : -n, r.unit)
    return `${formatYMD(out)}（${weekdayZh(out)}）`
  })
)

function addRow(): void {
  arithRows.value.push({ target: 'd1', op: '+', n: 7, unit: 'day' })
}
function removeRow(i: number): void {
  arithRows.value.splice(i, 1)
}
</script>

<template>
  <div class="flex flex-col gap-2 pt-4 pb-2">
    <div
      v-for="(r, i) in arithRows"
      :key="i"
      class="flex items-center gap-2 surface-card px-3 py-2"
      :data-testid="`arith-row-${i}`"
    >
      <select v-model="r.target" class="px-2 h-7 bg-page border border-line rounded-control text-control text-ink" :aria-label="`第 ${i + 1} 行目标日期`">
        <option value="d1">起点</option>
        <option value="d2">终点</option>
      </select>
      <select v-model="r.op" class="px-2 h-7 bg-page border border-line rounded-control text-control text-ink" :aria-label="`第 ${i + 1} 行运算`">
        <option value="+">＋</option>
        <option value="-">－</option>
      </select>
      <input
        v-model.number="r.n"
        type="number"
        step="1"
        class="px-2 h-7 w-[90px] bg-page border border-line rounded-control text-ink text-control font-mono outline-none focus:border-accent"
        aria-label="数值"
        @change="r.n = Math.trunc(Number(r.n) || 0)"
      />
      <select v-model="r.unit" class="px-2 h-7 bg-page border border-line rounded-control text-control text-ink" :aria-label="`第 ${i + 1} 行单位`">
        <option v-for="u in UNITS" :key="u.v" :value="u.v">{{ u.label }}</option>
      </select>
      <span class="text-ink-mute">→</span>
      <span class="text-control text-ink font-mono" data-testid="arith-result">{{ results[i] ?? '—' }}</span>
      <button
        class="ml-auto border-0 bg-transparent text-ink-faint hover:text-danger cursor-pointer"
        :aria-label="`删除第 ${i + 1} 行`"
        @click="removeRow(i)"
      >
        <Trash2 :size="14" />
      </button>
    </div>
    <button
      class="self-start flex items-center gap-1 border-0 bg-transparent text-control text-ink-mute hover:text-accent cursor-pointer"
      data-testid="arith-add"
      @click="addRow()"
    >
      <Plus :size="14" /> 增加一行
    </button>
  </div>
</template>
