<script setup lang="ts">
// BaseInput：统一文本输入框（md 28 / lg 32）
// 错误态（error 显示红框 + 下方错误文案）与密码可见性切换（showPassword）。
import { computed, ref, useId } from 'vue'
import { Eye, EyeOff } from 'lucide-vue-next'

const props = withDefaults(
  defineProps<{
    modelValue: string
    placeholder?: string
    type?: string
    size?: 'md' | 'lg'
    autocomplete?: string
    title?: string
    error?: string
    showPassword?: boolean
    id?: string
    ariaLabel?: string
    spellcheck?: boolean
  }>(),
  {
    placeholder: '',
    type: 'text',
    size: 'md',
    autocomplete: 'off',
    title: undefined,
    error: '',
    showPassword: false,
    id: undefined,
    ariaLabel: undefined,
    spellcheck: undefined
  }
)
const emit = defineEmits<{ 'update:modelValue': [v: string] }>()

// 错误文案关联（审计 P2）：读屏用户光有 aria-invalid 听不到「错在哪」，
// 经 aria-describedby 把下方错误 <p> 挂到输入框上
const autoId = useId()
const errorId = computed(() => `${props.id || autoId}-error`)

const passwordVisible = ref(false)
const effectiveType = computed(() => {
  if (props.type !== 'password' || !props.showPassword) return props.type
  return passwordVisible.value ? 'text' : 'password'
})

const inputCls = computed(() => [
  props.size === 'lg' ? 'h-8 text-body' : 'h-7 text-control',
  props.error
    ? 'border-danger hover:border-danger focus:border-danger'
    : 'border-line hover:border-line-strong focus:border-accent',
  'w-full rounded-control bg-page px-2.5 text-ink outline-none transition-[border-color,box-shadow] dur-fast placeholder:text-ink-faint',
  props.type === 'password' && props.showPassword ? 'pr-8' : ''
])
</script>

<template>
  <div class="w-full">
    <div class="relative">
      <input
        :id="id"
        :value="modelValue"
        :type="effectiveType"
        :placeholder="placeholder"
        :autocomplete="autocomplete"
        :title="title"
        :aria-label="ariaLabel"
        :aria-invalid="error ? 'true' : undefined"
        :aria-describedby="error ? errorId : undefined"
        :spellcheck="spellcheck"
        :class="inputCls"
        @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      />
      <button
        v-if="type === 'password' && showPassword"
        type="button"
        class="absolute right-1.5 top-1/2 -translate-y-1/2 w-5 h-5 flex items-center justify-center border-0 bg-transparent text-ink-mute hover:text-ink cursor-pointer"
        :title="passwordVisible ? '隐藏密码' : '显示密码'"
        @click="passwordVisible = !passwordVisible"
      >
        <component :is="passwordVisible ? EyeOff : Eye" :size="13" />
      </button>
    </div>
    <p v-if="error" :id="errorId" class="m-0 mt-1 text-caption text-danger">{{ error }}</p>
  </div>
</template>
