<script setup lang="ts">
// BaseSelectMenu：工具栏单选下拉（reka-ui DropdownMenu 底座）。
//
// 为什么不用原生 <select>：原生菜单是系统白色样式、锚定与层级不可控，
// 压在深色工具栏/密度切换上非常突兀（2026-10-02 用户反馈「样式有问题」）。
// 本组件是工具栏下拉的统一形态：触发器回显当前项（不含计数右缀，避免过宽），
// 菜单内勾选标记 + 计数右缀；开合/Esc/外点/方向键/焦点归还由 reka-ui 承担。
import { computed } from 'vue'
import {
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuRoot,
  DropdownMenuTrigger
} from 'reka-ui'
import { Check, ChevronDown } from 'lucide-vue-next'

export interface SelectMenuOption {
  value: string
  label: string
  /** 计数右缀（如 facet 数），只显示在菜单内 */
  hint?: string
}

const props = defineProps<{
  modelValue: string
  options: SelectMenuOption[]
  title?: string
  ariaLabel?: string
  /** 有生效筛选时的强调态（与 TagFilterSelect 同语言） */
  active?: boolean
  testid?: string
  /** 菜单对齐：默认靠 start；右缘控件用 end 防溢出 */
  align?: 'start' | 'center' | 'end'
}>()

const emit = defineEmits<{ 'update:modelValue': [v: string] }>()

const current = computed(() => props.options.find((o) => o.value === props.modelValue))
const triggerCls = computed(() => [
  'inline-flex items-center gap-1.5 h-7 pl-2 pr-1.5 rounded-control border text-control cursor-pointer transition-colors dur-fast',
  props.active ? 'border-line-subtle bg-accent/12 text-accent-text' : 'border-line bg-page text-ink-dim hover:text-ink'
])
</script>

<template>
  <div class="relative shrink-0 app-no-drag">
    <DropdownMenuRoot>
      <DropdownMenuTrigger as-child>
        <button type="button" :title="title" :aria-label="ariaLabel || title" :data-testid="testid" :class="triggerCls">
          <span class="truncate max-w-[160px]">{{ current?.label ?? title }}</span>
          <ChevronDown :size="13" class="shrink-0" />
        </button>
      </DropdownMenuTrigger>

      <!-- 不套 Portal（与 TagFilterSelect 同决策）：工具栏上的锚定浮层，jsdom 卸载也稳 -->
      <DropdownMenuContent
        :side-offset="4"
        :align="align || 'start'"
        :aria-label="ariaLabel || title"
        class="z-50 min-w-[150px] max-h-[320px] overflow-y-auto bg-panel border border-line-subtle rounded-panel shadow-elev-3 py-1 outline-none"
      >
        <DropdownMenuRadioGroup
          :model-value="modelValue"
          @update:model-value="emit('update:modelValue', $event as string)"
        >
          <DropdownMenuRadioItem
            v-for="o in options"
            :key="o.value"
            :value="o.value"
            :title="o.label"
            class="group flex items-center gap-2 px-3 py-1 m-0 rounded-0 cursor-pointer text-control text-ink-dim outline-none data-[highlighted]:bg-hover data-[highlighted]:text-ink"
          >
            <!-- 勾选只属于选中项（占位保持对齐；modelValue 即状态，不依赖 reka 指示器） -->
            <span class="w-3.5 shrink-0 inline-flex justify-center">
              <Check v-if="o.value === modelValue" :size="13" class="text-accent-text" />
            </span>
            <span class="truncate">{{ o.label }}</span>
            <span v-if="o.hint" class="ml-auto shrink-0 text-caption text-ink-mute font-mono">{{ o.hint }}</span>
          </DropdownMenuRadioItem>
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenuRoot>
  </div>
</template>
