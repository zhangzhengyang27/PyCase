<script setup lang="ts">
// InteractiveToolPage：schema 驱动交互工具的统一页面——
// 页头（返回/标题/徽章）+ 动态表单（toolValueOf 输入桶）+ 实时结果区 + 代码抽屉。
// 专属页（日期计算器）不走这里：App.vue 按 id 分派。
import { computed } from 'vue'
import { ArrowLeft } from 'lucide-vue-next'
import ToolField from './ToolField.vue'
import ToolResultPanel from './ToolResultPanel.vue'
import CodeDrawer from '../date-calculator/CodeDrawer.vue'
import { getToolSchema, type SelectOption } from '../../src/interactive-tools'
import { closeInteractive, toolValueOf } from '../../src/store/interactive'
import { selectedId } from '../../src/store/detail'

const schema = computed(() => (selectedId.value ? getToolSchema(selectedId.value) : undefined))
const values = computed(() => (schema.value ? toolValueOf(schema.value.id, schema.value.fields) : {}))
const result = computed(() => schema.value?.compute?.(values.value))
const code = computed(() => (schema.value ? schema.value.pyCode(values.value) : '# 工具不存在'))

/** required 且当前为空 → 传给 ToolField 标红（compute 侧同时出 error 引导） */
/** select 联动：options 函数形态按当前输入解析（静态 options 原样透传由 ToolField 兜底） */
function optionsOf(key: string): SelectOption[] | undefined {
  const f = schema.value?.fields.find((x) => x.key === key)
  if (!f || typeof f.options !== 'function') return undefined
  return f.options(values.value)
}

function isInvalid(key: string): boolean {
  const f = schema.value?.fields.find((x) => x.key === key)
  if (!f?.required) return false
  const v = values.value[key]
  return v === undefined || v === null || String(v).trim() === ''
}
</script>

<template>
  <section class="flex-1 min-w-0 min-h-0 flex flex-col bg-page overflow-hidden">
    <div class="app-drag select-none px-8 pt-7 pb-3 flex items-center gap-3">
      <button
        class="app-no-drag border border-line rounded-control bg-transparent text-ink-mute hover:text-accent hover:border-accent cursor-pointer p-1.5"
        data-testid="it-back"
        aria-label="返回工具箱"
        @click="closeInteractive()"
      >
        <ArrowLeft :size="15" />
      </button>
      <h1 class="text-[length:--text-page] font-semibold text-ink m-0 tracking-[-0.02em]">
        {{ schema?.title ?? '交互工具' }}
      </h1>
      <span class="text-caption text-ink-mute border border-line rounded-control px-2 py-0.5">交互工具</span>
    </div>

    <div
      v-if="!schema"
      class="flex-1 flex items-center justify-center text-control text-ink-mute"
      data-testid="it-ghost"
    >
      工具不存在或已下线
    </div>

    <template v-else>
      <div class="flex-1 min-h-0 overflow-y-auto app-no-drag">
        <div class="max-w-[900px] mx-auto px-8 pb-6 flex flex-col gap-5">
          <p class="text-control text-ink-mute m-0">{{ schema.description }}</p>
          <div class="grid grid-cols-2 gap-x-4 gap-y-3 items-start">
            <template v-for="f in schema.fields" :key="f.key">
              <ToolField
                :spec="f"
                :model-value="values[f.key]"
                :invalid="isInvalid(f.key)"
                :options="optionsOf(f.key)"
                @update:model-value="values[f.key] = $event"
              />
            </template>
          </div>
          <ToolResultPanel v-if="result" :result="result" />
        </div>
      </div>
      <div class="app-no-drag border-t border-line shrink-0">
        <CodeDrawer :code="code" :run-id="schema.id" />
      </div>
    </template>
  </section>
</template>
