<script setup lang="ts">
// BaseButton：统一按钮（设计规范 v1）
// variants: primary / ghost / danger；sizes: sm 24 / md 28 / lg 32；
// square 用于图标钮（等宽方形）；loading 时禁用并显示内联 spinner。
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    variant?: 'primary' | 'ghost' | 'danger'
    size?: 'sm' | 'md' | 'lg'
    square?: boolean
    disabled?: boolean
    loading?: boolean
    title?: string
    type?: 'button' | 'submit'
  }>(),
  { variant: 'ghost', size: 'md', square: false, disabled: false, loading: false, title: undefined, type: 'button' }
)

defineEmits<{ click: [e: MouseEvent] }>()

const SIZE_CLS: Record<string, string> = {
  sm: 'h-6 text-caption',
  md: 'h-7 text-control',
  lg: 'h-8 text-control'
}
const VARIANT_CLS: Record<string, string> = {
  ghost:
    'border border-line-subtle bg-transparent text-ink-dim hover:bg-hover hover:text-ink hover:border-line-strong',
  primary: 'btn-primary-deep',
  danger: 'border border-danger bg-danger text-white hover:opacity-90'
}

const cls = computed(
  () =>
    `inline-flex items-center justify-center gap-1.5 rounded-control font-[510] font-sans whitespace-nowrap select-none cursor-pointer transition-[color,background-color,border-color,box-shadow,transform] duration-[120ms] active:scale-[0.98] disabled:opacity-[0.35] disabled:cursor-not-allowed disabled:active:scale-100 ${SIZE_CLS[props.size]} ${VARIANT_CLS[props.variant]} ${
      props.square ? (props.size === 'sm' ? 'w-6 px-0' : props.size === 'lg' ? 'w-8 px-0' : 'w-7 px-0') : 'px-2.5'
    }`
)
</script>

<template>
  <button :class="cls" :type="type" :title="title" :disabled="disabled || loading" @click="$emit('click', $event)">
    <span
      v-if="loading"
      class="inline-block w-3 h-3 border-[1.5px] border-current border-t-transparent rounded-full animate-spin"
    ></span>
    <slot />
  </button>
</template>
