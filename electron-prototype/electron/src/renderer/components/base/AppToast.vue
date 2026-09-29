<script setup lang="ts">
// AppToast：全局轻提示渲染层（右下角，成组进出场；状态由 toast.ts 持有）
// role=status + aria-live=polite：异步结果对读屏可见；悬停暂停自动退场。
import { AlertCircle, CheckCircle2, Info, X } from 'lucide-vue-next'
import type { Component } from 'vue'
import { dismissToast, holdToast, resumeToast, toasts, type ToastType } from '../../toast'

const ICON: Record<ToastType, Component> = { success: CheckCircle2, error: AlertCircle, info: Info }
const ICON_CLS: Record<ToastType, string> = { success: 'text-ok', error: 'text-danger', info: 'text-accent' }
</script>

<template>
  <Teleport to="body">
    <div class="fixed bottom-8 right-4 z-[1100] flex flex-col gap-2 items-end" role="status" aria-live="polite">
      <TransitionGroup name="toast">
        <div
          v-for="t in toasts"
          :key="t.id"
          class="flex items-center gap-2 bg-panel border border-line-hairline rounded-overlay shadow-elev-2 pl-3 pr-1.5 py-2 text-control text-ink max-w-[380px]"
          @mouseenter="holdToast(t.id)"
          @mouseleave="resumeToast(t.id)"
        >
          <component :is="ICON[t.type]" :size="15" :class="ICON_CLS[t.type]" class="shrink-0" />
          <span class="min-w-0 break-all">{{ t.text }}</span>
          <button
            class="shrink-0 w-5 h-5 flex items-center justify-center rounded-control text-ink-mute hover:text-ink cursor-pointer border-0 bg-transparent"
            title="关闭"
            aria-label="关闭通知"
            @click="dismissToast(t.id)"
          >
            <X :size="12" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition:
    opacity 180ms var(--ease-panel),
    transform 180ms var(--ease-panel);
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
