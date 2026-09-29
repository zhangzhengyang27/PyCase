<script setup lang="ts">
// AppEmpty：空态（ElEmpty 替代）：图标 + 标题 + 描述 + 可选动作
import type { Component } from 'vue'

defineProps<{ icon?: Component; title: string; description?: string }>()
</script>

<template>
  <div class="flex-1 flex flex-col items-center justify-center gap-2 py-16 text-center">
    <div class="w-11 h-11 rounded-card border border-line-hairline bg-card flex items-center justify-center text-ink-mute">
      <component :is="icon" v-if="icon" :size="20" :stroke-width="1.5" />
    </div>
    <div class="text-body font-semibold text-ink">{{ title }}</div>
    <div v-if="description" class="text-control text-ink-mute">{{ description }}</div>
    <div v-if="$slots.default" class="mt-2"><slot /></div>
  </div>
</template>
