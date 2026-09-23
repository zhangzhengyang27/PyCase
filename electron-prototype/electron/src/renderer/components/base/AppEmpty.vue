<script setup lang="ts">
// AppEmpty：空态（ElEmpty 替代）：图标 + 标题 + 描述 + 可选动作
import type { Component } from 'vue'

defineProps<{ icon?: Component; title: string; description?: string }>()
</script>

<template>
  <div class="flex-1 flex flex-col items-center justify-center gap-2 py-16 text-center">
    <div class="w-11 h-11 rounded-panel bg-card border border-line-subtle flex items-center justify-center text-ink-faint">
      <component :is="icon" v-if="icon" :size="20" />
    </div>
    <div class="text-body font-[590] text-ink-dim">{{ title }}</div>
    <div v-if="description" class="text-control text-ink-faint">{{ description }}</div>
    <div v-if="$slots.default" class="mt-2"><slot /></div>
  </div>
</template>
