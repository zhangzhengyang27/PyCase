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
import { openDetail, selectedId } from '../../src/store/detail'
import { cliExampleOfCurrentPage } from '../../src/interactive-mapping'

const schema = computed(() => (selectedId.value ? getToolSchema(selectedId.value) : undefined))
const values = computed(() => (schema.value ? toolValueOf(schema.value.id, schema.value.fields) : {}))
const result = computed(() => schema.value?.compute?.(values.value))
const code = computed(() => (schema.value ? schema.value.pyCode(values.value) : '# 工具不存在'))

// --- W8-W11 框架：sidecar 计算型 + 向导步骤 + quickRun ---
import { onMounted, ref, watch } from 'vue'
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'
import type { ToolResult } from '../../src/interactive-tools'
import { runBusy, runOutput, runSnippet } from '../../src/store/date-run'
import { parseSidecarOutput } from '../../src/sidecar-result'

const isSidecar = computed(() => schema.value?.computeVia === 'sidecar')
// sidecar 计算型：结果 = 运行输出 <<<JSON>>> 段的解析（标记外文本仍在抽屉日志区可见）
const sidecarResult = computed<ToolResult | null>(() =>
  isSidecar.value ? parseSidecarOutput(runOutput.value).result : null
)
const sidecarRest = computed(() => (isSidecar.value ? parseSidecarOutput(runOutput.value).rest : ''))

const stepIndex = ref(0)
const steps = computed(() => schema.value?.steps ?? [])
const stepFields = computed(() => {
  if (!steps.value.length || !schema.value) return schema.value?.fields ?? []
  const keys = steps.value[stepIndex.value]?.keys ?? []
  const set = new Set(keys)
  return schema.value.fields.filter((f) => set.has(f.key))
})
const isLastStep = computed(() => !steps.value.length || stepIndex.value >= steps.value.length - 1)
function nextStep(): void {
  if (!isLastStep.value) stepIndex.value++
}
function prevStep(): void {
  if (stepIndex.value > 0) stepIndex.value--
}

// quickRun：速查工具进页自动运行一次（切工具时重置）
const quickRan = ref(false)
function autoRun(): void {
  if (!schema.value || quickRan.value || runBusy.value) return
  quickRan.value = true
  runSnippet(schema.value.id, code.value)
}
onMounted(() => {
  if (schema.value?.quickRun) autoRun()
})
watch(schema, (sc) => {
  stepIndex.value = 0
  quickRan.value = false
  if (sc?.quickRun) autoRun()
})

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
      <button
        v-if="cliExampleOfCurrentPage"
        class="app-no-drag border border-line rounded-control bg-transparent text-ink-mute hover:text-accent hover:border-accent cursor-pointer px-2 py-1 text-caption"
        data-testid="it-cli"
        :title="`查看同能力 CLI 示例源码：${cliExampleOfCurrentPage.title}`"
        @click="openDetail(cliExampleOfCurrentPage.id)"
      >
        CLI 源码
      </button>
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
          <div v-if="steps.length" class="flex items-center gap-2 mb-3">
            <template v-for="(st, i) in steps" :key="st.title">
              <span
                class="text-caption px-2 py-0.5 rounded-control"
                :class="
                  i === stepIndex ? 'bg-accent text-page font-medium' : i < stepIndex ? 'text-accent' : 'text-ink-faint'
                "
              >
                {{ i + 1 }}. {{ st.title }}
              </span>
              <ChevronRight v-if="i < steps.length - 1" :size="12" class="text-ink-faint" />
            </template>
          </div>
          <div class="grid grid-cols-2 gap-x-4 gap-y-3 items-start">
            <template v-for="f in stepFields" :key="f.key">
              <ToolField
                :spec="f"
                :model-value="values[f.key]"
                :invalid="isInvalid(f.key)"
                :options="optionsOf(f.key)"
                @update:model-value="values[f.key] = $event"
              />
            </template>
          </div>
          <div
            v-if="isSidecar && (!steps.length || isLastStep)"
            class="flex justify-center"
            data-testid="page-run-wrap"
          >
            <button
              class="inline-flex items-center gap-1.5 px-5 h-9 rounded-control border-0 text-control font-medium cursor-pointer transition-colors dur-fast disabled:opacity-50"
              style="background: var(--color-accent, #3b82f6); color: #fff"
              data-testid="page-run"
              :disabled="runBusy"
              @click="runSnippet(schema.id, code)"
            >
              ▶ {{ runOutput ? '重新运行' : '运行' }}
            </button>
          </div>
          <template v-if="isSidecar">
            <ToolResultPanel v-if="result?.error" :result="result" data-testid="sidecar-invalid" />
            <div v-else-if="runBusy" class="text-control text-ink-mute pt-4 text-center" data-testid="sidecar-running">
              正在运行…
            </div>
            <ToolResultPanel v-else-if="sidecarResult" :result="sidecarResult" data-testid="sidecar-result" />
            <ToolResultPanel v-else-if="result" :result="result" data-testid="sidecar-echo" />
            <div v-else class="text-control text-ink-mute pt-4 text-center">点击「运行」获取结果</div>
            <pre
              v-if="sidecarRest"
              class="m-0 p-3 surface-card text-caption font-mono text-ink-mute whitespace-pre-wrap"
              data-testid="sidecar-rest"
              >{{ sidecarRest }}</pre>
          </template>
          <template v-else>
            <ToolResultPanel v-if="result" :result="result" />
          </template>
          <div v-if="steps.length && !isLastStep" class="flex justify-end">
            <button
              class="inline-flex items-center gap-1 px-3 h-8 border border-line rounded-control bg-panel text-control text-ink cursor-pointer hover:border-accent transition-colors dur-fast"
              data-testid="wizard-next"
              @click="nextStep()"
            >
              下一步 <ChevronRight :size="13" />
            </button>
          </div>
          <div v-if="steps.length && stepIndex > 0" class="flex justify-start -mt-8">
            <button
              class="inline-flex items-center gap-1 px-3 h-8 border-0 bg-transparent text-control text-ink-mute hover:text-accent cursor-pointer"
              data-testid="wizard-prev"
              @click="prevStep()"
            >
              <ChevronLeft :size="13" /> 上一步
            </button>
          </div>
        </div>
      </div>
      <div class="app-no-drag border-t border-line shrink-0">
        <CodeDrawer :code="code" :run-id="schema.id" />
      </div>
    </template>
  </section>
</template>
