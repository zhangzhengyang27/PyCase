<script setup lang="ts">
// ToolField：FieldSpec → 控件（schema 驱动表单的原子件）。
// 控件复用现有样式语言（bg-page/border-line/rounded-control），值经 v-model 双向绑定
// 到父层的工具输入桶（store.toolValueOf）；required 失焦校验标红。
import { computed } from 'vue'
import type { FieldSpec, FieldValue, SelectOption } from '../../src/interactive-tools'

const props = defineProps<{
  spec: FieldSpec
  modelValue: FieldValue
  invalid?: boolean
  /** 动态选项（FieldSpec.options 为函数形态时由页面解析后传入；静态 options 直接用 spec 的） */
  options?: SelectOption[]
}>()
const emit = defineEmits<{ 'update:modelValue': [value: FieldValue] }>()

const INPUT_CLS =
  'px-2 h-8 bg-page border rounded-control text-ink text-control font-mono outline-none transition-[border-color] dur-fast hover:border-line-strong focus:border-accent'
const SELECT_CLS =
  'px-2 h-8 bg-page border border-line rounded-control text-control text-ink outline-none focus:border-accent'

const borderCls = computed(() => (props.invalid ? 'border-danger' : 'border-line'))
const widthCls = computed(() => (props.spec.width === 'half' ? 'min-w-[160px] flex-1' : 'w-full'))

function onInput(e: Event): void {
  const el = e.target as HTMLInputElement
  emit('update:modelValue', props.spec.type === 'number' ? (el.value === '' ? undefined : Number(el.value)) : el.value)
}
function onCheckbox(e: Event): void {
  emit('update:modelValue', (e.target as HTMLInputElement).checked)
}
</script>

<template>
  <div class="flex flex-col gap-1" :class="widthCls">
    <label class="text-caption font-medium text-ink-mute flex items-center gap-2" :for="`tf-${spec.key}`">
      {{ spec.label }}<span v-if="spec.required" class="text-danger">*</span>
    </label>

    <textarea
      v-if="spec.type === 'textarea'"
      :id="`tf-${spec.key}`"
      class="px-2 py-1.5 bg-page border rounded-control text-ink text-control font-mono outline-none transition-[border-color] dur-fast hover:border-line-strong focus:border-accent resize-y min-h-[88px]"
      :class="borderCls"
      :value="String(modelValue ?? '')"
      :placeholder="spec.placeholder"
      @input="onInput"
    />

    <select
      v-else-if="spec.type === 'select'"
      :id="`tf-${spec.key}`"
      class="w-full"
      :class="SELECT_CLS"
      :value="String(modelValue ?? '')"
      @change="onInput"
    >
      <option v-for="o in props.options ?? spec.options" :key="o.value" :value="o.value">{{ o.label }}</option>
    </select>

    <label
      v-else-if="spec.type === 'checkbox'"
      class="flex flex-row items-center gap-2 text-control text-ink cursor-pointer select-none"
    >
      <input
        :id="`tf-${spec.key}`"
        type="checkbox"
        class="w-4 h-4 accent-accent cursor-pointer rounded"
        :checked="modelValue === true"
        @change="onCheckbox"
      />
      <span class="text-ink-mute">{{ spec.help || spec.placeholder }}</span>
    </label>

    <input
      v-else
      :id="`tf-${spec.key}`"
      :type="spec.type === 'number' ? 'number' : 'text'"
      :step="spec.type === 'number' ? 'any' : undefined"
      class="w-full"
      :class="[INPUT_CLS, borderCls]"
      :value="modelValue === undefined ? '' : String(modelValue)"
      :placeholder="spec.placeholder"
      @input="onInput"
    />

    <span v-if="spec.help && spec.type !== 'checkbox'" class="text-[10px] text-ink-faint">{{ spec.help }}</span>
  </div>
</template>
