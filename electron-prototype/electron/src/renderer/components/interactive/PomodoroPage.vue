<script setup lang="ts">
// PomodoroPage：番茄钟专属页（纯前端计时器，无 sidecar 依赖）。
// 25 分钟专注 / 5 分钟休息循环；大数字倒计时 + 开始/暂停/重置 + 会话计数。
// 计时基于时间戳差值（而非 setInterval 累减），后台挂起后回来仍准确。
import { computed, onBeforeUnmount, ref } from 'vue'
import { ArrowLeft, Pause, Play, RotateCcw, SkipForward } from 'lucide-vue-next'
import { closeInteractive } from '../../src/store/interactive'
import BaseButton from '../base/BaseButton.vue'

const WORK_SEC = 25 * 60
const BREAK_SEC = 5 * 60

type Phase = 'work' | 'break'
const phase = ref<Phase>('work')
const running = ref(false)
const sessions = ref(0)
// remaining 以毫秒时间戳记账：endedAt 为空表示暂停中
const remainMs = ref(WORK_SEC * 1000)
let endedAt: number | null = null
let timer: number | null = null

const totalSec = computed(() => (phase.value === 'work' ? WORK_SEC : BREAK_SEC))
const remainSec = computed(() => Math.max(0, Math.ceil(remainMs.value / 1000)))
const mmss = computed(() => {
  const m = Math.floor(remainSec.value / 60)
  const s = remainSec.value % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})
const progress = computed(() => 1 - remainMs.value / (totalSec.value * 1000))

function tick(): void {
  if (endedAt === null) return
  remainMs.value = Math.max(0, endedAt - Date.now())
  if (remainMs.value <= 0) {
    if (phase.value === 'work') {
      sessions.value++
      switchTo('break')
    } else {
      switchTo('work')
    }
  }
}

function switchTo(next: Phase): void {
  phase.value = next
  remainMs.value = (next === 'work' ? WORK_SEC : BREAK_SEC) * 1000
  endedAt = running.value ? Date.now() + remainMs.value : null
}

function toggle(): void {
  if (running.value) {
    // 暂停：把剩余时间定格
    if (endedAt !== null) remainMs.value = Math.max(0, endedAt - Date.now())
    endedAt = null
    running.value = false
    if (timer !== null) {
      clearInterval(timer)
      timer = null
    }
  } else {
    endedAt = Date.now() + remainMs.value
    running.value = true
    timer = window.setInterval(tick, 250)
  }
}

function reset(): void {
  running.value = false
  endedAt = null
  if (timer !== null) {
    clearInterval(timer)
    timer = null
  }
  phase.value = 'work'
  remainMs.value = WORK_SEC * 1000
}

onBeforeUnmount(() => {
  if (timer !== null) clearInterval(timer)
})
</script>

<template>
  <section class="flex-1 min-w-0 min-h-0 flex flex-col bg-page overflow-hidden">
    <div class="app-drag select-none px-8 pt-7 pb-3 flex items-center gap-3">
      <button
        class="app-no-drag border border-line rounded-control bg-transparent text-ink-mute hover:text-accent hover:border-accent cursor-pointer p-1.5"
        data-testid="pomodoro-back"
        aria-label="返回工具箱"
        @click="closeInteractive()"
      >
        <ArrowLeft :size="15" />
      </button>
      <h1 class="text-[length:--text-page] font-semibold text-ink m-0 tracking-[-0.02em]">番茄钟</h1>
      <span class="text-caption text-ink-mute border border-line rounded-control px-2 py-0.5">交互工具</span>
    </div>

    <div class="flex-1 flex flex-col items-center justify-center gap-8 app-no-drag">
      <div
        class="text-caption px-3 py-1 rounded-control border"
        :class="phase === 'work' ? 'text-accent border-accent' : 'text-ink-mute border-line'"
        data-testid="pomodoro-phase"
      >
        {{ phase === 'work' ? '专注中' : '休息中' }} · 已完成 {{ sessions }} 个番茄
      </div>

      <div class="text-center">
        <div
          class="font-semibold m-0 tabular-nums"
          :class="phase === 'work' ? 'text-ink' : 'text-ink-mute'"
          style="font-size: 96px; line-height: 1"
          data-testid="pomodoro-time"
        >
          {{ mmss }}
        </div>
        <div class="mt-4 h-1.5 w-[320px] rounded-full bg-line overflow-hidden">
          <div
            class="h-full rounded-full bg-accent transition-[width] dur-slow"
            :style="{ width: `${Math.round(progress * 100)}%` }"
          />
        </div>
      </div>

      <div class="flex items-center gap-3">
        <BaseButton
          variant="primary"
          size="lg"
          data-testid="pomodoro-toggle"
          :title="running ? '暂停' : '开始'"
          @click="toggle()"
        >
          <Pause v-if="running" :size="15" />
          <Play v-else :size="15" />
          {{ running ? '暂停' : remainSec === totalSec ? '开始专注' : '继续' }}
        </BaseButton>
        <BaseButton size="lg" title="跳到下一阶段" @click="switchTo(phase === 'work' ? 'break' : 'work')">
          <SkipForward :size="14" /> 跳过
        </BaseButton>
        <BaseButton size="lg" title="重置为专注 25 分钟" @click="reset()"> <RotateCcw :size="14" /> 重置 </BaseButton>
      </div>
    </div>
  </section>
</template>
