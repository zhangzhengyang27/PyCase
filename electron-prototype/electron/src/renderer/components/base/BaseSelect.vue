<script setup lang="ts">
// BaseSelect：原生下拉统一样式（h-7；option 经插槽透传）
defineProps<{ modelValue: string; title?: string }>()
const emit = defineEmits<{ 'update:modelValue': [v: string] }>()
</script>

<template>
  <select
    :value="modelValue"
    :title="title"
    class="h-7 rounded-control border border-line bg-page px-2 text-control text-ink outline-none cursor-pointer transition-[border-color] duration-[120ms] hover:border-line-strong focus:border-accent"
    @change="emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
  >
    <slot />
  </select>
</template>
