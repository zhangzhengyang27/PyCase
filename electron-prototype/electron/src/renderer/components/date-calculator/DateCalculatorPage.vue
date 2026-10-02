<script setup lang="ts">
// DateCalculatorPage：日期计算器专属页（工具箱交互工具，interactive: 前缀路由）。
// 结构 = 页头 + 全局日期对输入行 + 四 Tab（垂直叙事，v-show 保活=会话内记忆）
//        + 底部折叠代码抽屉。本页无脏状态，返回直接清 selectedId。
import { computed } from 'vue'
import { ArrowLeft } from 'lucide-vue-next'
import DateRangeInputs from './DateRangeInputs.vue'
import TabDiff from './TabDiff.vue'
import TabCountdown from './TabCountdown.vue'
import TabArithmetic from './TabArithmetic.vue'
import TabCalendar from './TabCalendar.vue'
import CodeDrawer from './CodeDrawer.vue'
import { parseDate } from '../../src/date-core'
import { activeTab, closeInteractive, dateA, dateB, type TabKey } from '../../src/store/interactive'

const TABS: Array<{ key: TabKey; label: string }> = [
  { key: 'diff', label: '日期差' },
  { key: 'countdown', label: '正倒计时' },
  { key: 'arith', label: '日期加减' },
  { key: 'calendar', label: '日历' }
]

const valid = computed(() => !!parseDate(dateA.value) && !!parseDate(dateB.value))
const TAB_CLS = 'border-0 bg-transparent px-3 py-2 text-control cursor-pointer transition-colors dur-fast'
</script>

<template>
  <section class="flex-1 min-w-0 min-h-0 flex flex-col bg-page overflow-hidden">
    <div class="app-drag select-none px-8 pt-7 pb-3 flex items-center gap-3">
      <button
        class="app-no-drag border border-line rounded-control bg-transparent text-ink-mute hover:text-accent hover:border-accent cursor-pointer p-1.5"
        data-testid="dc-back"
        aria-label="返回工具箱"
        @click="closeInteractive()"
      >
        <ArrowLeft :size="15" />
      </button>
      <h1 class="text-[length:--text-page] font-semibold text-ink m-0 tracking-[-0.02em]">日期计算器</h1>
      <span class="text-caption text-ink-mute border border-line rounded-control px-2 py-0.5">交互工具</span>
    </div>
    <div class="app-no-drag px-8 pb-3">
      <div class="max-w-[1200px] mx-auto w-full"><DateRangeInputs /></div>
    </div>
    <div class="flex-1 min-h-0 overflow-y-auto app-no-drag">
      <div class="max-w-[1200px] mx-auto px-8">
        <div class="flex gap-1 border-b border-line mb-5">
          <button
            v-for="t in TABS"
            :key="t.key"
            :class="[TAB_CLS, activeTab === t.key ? 'text-ink border-b-2 border-accent font-medium' : 'text-ink-mute hover:text-ink']"
            :data-testid="`tab-${t.key}`"
            @click="activeTab = t.key"
          >
            {{ t.label }}
          </button>
        </div>
        <div v-if="!valid" class="text-control text-ink-mute pt-10 text-center" data-testid="dc-invalid">
          请补全两个有效日期
        </div>
        <template v-else>
          <TabDiff v-show="activeTab === 'diff'" />
          <TabCountdown v-show="activeTab === 'countdown'" />
          <TabArithmetic v-show="activeTab === 'arith'" />
          <TabCalendar v-show="activeTab === 'calendar'" />
        </template>
      </div>
    </div>
    <div class="app-no-drag border-t border-line shrink-0">
      <CodeDrawer />
    </div>
  </section>
</template>
