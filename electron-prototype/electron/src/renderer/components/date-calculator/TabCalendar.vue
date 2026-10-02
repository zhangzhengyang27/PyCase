<script setup lang="ts">
// TabCalendar：双月并排日历——起止高亮 + 区间淡染 + 点击格反向设定（第一次点=起点，
// 第二次点=终点，再点重新开始）。左月：未手动翻月时实时跟随起点所在月（cursor=null），
// 手动翻月后固定为游标月。
import { computed, ref } from 'vue'
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { daysBetween, formatYMD, parseDate } from '../../src/date-core'
import { dateA, dateB } from '../../src/store/interactive'

const WD_HEAD = ['一', '二', '三', '四', '五', '六', '日']

function isLeap(y: number): boolean {
  return (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0
}
function lastDay(y: number, m: number): number {
  return [31, isLeap(y) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]
}
function monthAdd(c: { y: number; m: number }, n: number): { y: number; m: number } {
  const total = c.y * 12 + (c.m - 1) + n
  return { y: Math.floor(total / 12), m: (((total % 12) + 12) % 12) + 1 }
}

const a = computed(() => parseDate(dateA.value))
const b = computed(() => parseDate(dateB.value))
const cursor = ref<{ y: number; m: number } | null>(null)
const left = computed(() => cursor.value ?? (a.value ? { y: a.value.y, m: a.value.m } : { y: 2024, m: 1 }))
const right = computed(() => monthAdd(left.value, 1))

const pickStage = ref<0 | 1>(0)
function onPick(ymd: string): void {
  if (pickStage.value === 0) {
    dateA.value = ymd
    pickStage.value = 1
  } else {
    dateB.value = ymd
    pickStage.value = 0
  }
}

interface Cell {
  ymd: string
  d: number
  blank?: boolean
  start?: boolean
  end?: boolean
  between?: boolean
}

function monthCells(c: { y: number; m: number }): Cell[] {
  const lead = (new Date(Date.UTC(c.y, c.m - 1, 1)).getUTCDay() + 6) % 7 // 周一起
  const cells: Cell[] = []
  for (let i = 0; i < lead; i++) cells.push({ ymd: `blank-${c.y}-${c.m}-${i}`, d: 0, blank: true })
  const last = lastDay(c.y, c.m)
  for (let d = 1; d <= last; d++) {
    const ymd = formatYMD({ y: c.y, m: c.m, d })
    const v = parseDate(ymd)!
    cells.push({
      d,
      ymd,
      start: a.value ? daysBetween(a.value, v) === 0 : false,
      end: b.value ? daysBetween(b.value, v) === 0 : false,
      between: a.value && b.value ? daysBetween(a.value, v) > 0 && daysBetween(v, b.value) > 0 : false
    })
  }
  return cells
}

function cellCls(c: Cell): string {
  if (c.blank) return ''
  if (c.start) return 'bg-accent text-page font-semibold rounded'
  if (c.end) return 'border border-accent text-accent font-semibold rounded'
  if (c.between) return 'text-ink-dim bg-accent/10'
  return 'text-ink-dim hover:bg-line cursor-pointer'
}
</script>

<template>
  <div class="pt-4 pb-2">
    <div class="flex items-center gap-2 mb-3">
      <button class="border-0 bg-transparent text-ink-mute hover:text-accent cursor-pointer" aria-label="前翻一月" data-testid="cal-prev" @click="cursor = monthAdd(left, -1)">
        <ChevronLeft :size="16" />
      </button>
      <div class="text-caption text-ink-mute">点击日期格：第一次设起点，第二次设终点（当前：{{ pickStage === 0 ? '设起点' : '设终点' }}）</div>
      <button class="ml-auto border-0 bg-transparent text-ink-mute hover:text-accent cursor-pointer" aria-label="后翻一月" data-testid="cal-next" @click="cursor = monthAdd(left, 1)">
        <ChevronRight :size="16" />
      </button>
    </div>
    <div class="grid grid-cols-2 gap-4">
      <div v-for="mc in [left, right]" :key="`${mc.y}-${mc.m}`" class="surface-card p-3">
        <div class="text-control text-ink font-medium text-center mb-2">{{ mc.y }} 年 {{ mc.m }} 月</div>
        <div class="grid grid-cols-7 text-center text-caption text-ink-faint mb-1">
          <span v-for="w in WD_HEAD" :key="w">{{ w }}</span>
        </div>
        <div class="grid grid-cols-7 gap-0.5 text-center text-control">
          <template v-for="c in monthCells(mc)" :key="c.ymd">
            <button
              v-if="!c.blank"
              type="button"
              class="border-0 bg-transparent py-0.5 text-caption rounded cursor-pointer"
              :class="cellCls(c)"
              :data-testid="`cal-${c.ymd}`"
              :aria-label="`选定 ${c.ymd}`"
              @click="onPick(c.ymd)"
            >
              {{ c.d }}
            </button>
            <span v-else class="py-0.5 text-caption" aria-hidden="true"></span>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>
