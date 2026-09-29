<script setup lang="ts">
// BaseButton：统一按钮（视觉基线 v2）
// variants: primary（强调填充）/ ghost（中性描边）/ danger（红色文字按钮）；sizes 走 --ctrl-sm/md/lg；
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
  sm: 'h-[var(--ctrl-sm)] text-caption',
  md: 'h-[var(--ctrl-md)] text-control',
  lg: 'h-[var(--ctrl-lg)] text-control'
}
// v2 按钮语言：primary = 强调填充 + on-accent；危险 = 表示危而非填充（.btn-danger-deep）
const VARIANT_CLS: Record<string, string> = {
  ghost:
    'border border-line-hairline bg-transparent text-ink-dim hover:bg-hover hover:text-ink hover:border-line-strong',
  primary: 'btn-primary-deep',
  danger: 'btn-danger-deep'
}

const cls = computed(
  () =>
    `inline-flex items-center justify-center gap-1.5 rounded-control font-medium font-sans whitespace-nowrap select-none cursor-pointer transition-[color,background-color,border-color,box-shadow,transform] dur-fast active:scale-[0.98] disabled:opacity-[0.35] disabled:cursor-not-allowed disabled:active:scale-100 ${SIZE_CLS[props.size]} ${VARIANT_CLS[props.variant]} ${
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
