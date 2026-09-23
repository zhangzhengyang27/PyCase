<script setup lang="ts">
// AlertBanner：错误/警告横幅（ElAlert 替代），右侧插槽放动作（如重试按钮）
import { AlertTriangle } from 'lucide-vue-next'

withDefaults(defineProps<{ title: string; type?: 'error' | 'warning' }>(), { type: 'error' })
</script>

<template>
  <div
    role="alert"
    class="flex items-start gap-2 px-3 py-2.5 rounded-control border text-control"
    :class="type === 'error' ? 'border-danger/30 bg-danger-bg text-ink' : 'border-warn/30 bg-warn-bg text-ink'"
  >
    <AlertTriangle :size="14" :class="type === 'error' ? 'text-danger' : 'text-warn'" class="shrink-0 mt-0.5" />
    <div class="min-w-0 flex-1">{{ title }}</div>
    <slot />
  </div>
</template>
