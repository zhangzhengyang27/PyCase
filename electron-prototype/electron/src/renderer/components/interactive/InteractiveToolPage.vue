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
import { closeInteractive, rawToolValues, toolValueOf } from '../../src/store/interactive'
import { interactiveSourceId, openDetail, pendingPreset, selectedId } from '../../src/store/detail'
import { cliExampleOfCurrentPage } from '../../src/interactive-mapping'
import { examples } from '../../src/store/catalog'

const schema = computed(() => (selectedId.value ? getToolSchema(selectedId.value) : undefined))
const values = computed(() => {
  if (!schema.value) return {}
  const f = schema.value.fields
  // 动态表单探测：fieldsFn 可能读当前值（类型选择器）——用原始桶直读，避免计算环
  const probe = typeof f === 'function' ? f(rawToolValues(schema.value.id)) : f
  return toolValueOf(schema.value.id, probe)
})
const rawFields = computed(() => {
  if (!schema.value) return []
  const f = schema.value.fields
  return typeof f === 'function' ? f(values.value) : f
})
const fields = computed(() => {
  // 锁型（家族卡进入，示例身份由画廊选定）：类型选择器不出现在表单；
  // 预选套用仍走 rawFields，锁型页内同页重路由要能照常换型
  return typeLocked.value ? rawFields.value.filter((x) => x.key !== 'type') : rawFields.value
})
const result = computed(() => schema.value?.compute?.(values.value))
const code = computed(() => (schema.value ? schema.value.pyCode(values.value) : '# 工具不存在'))
// 页头标题/描述：实验室页随当前类型联动（headerFor），其余工具恒用静态值
const header = computed(() => {
  const s = schema.value
  if (!s) return { title: '交互工具', description: '' }
  const h = s.headerFor?.(values.value)
  return { title: h?.title ?? s.title, description: h?.description ?? s.description }
})

// 画廊路由回链：经画廊卡片进来时指向被点的那张卡（可能是 12 个同名变体中的任何一个），
// 与 W14 的 CLI 工具回链（cliExampleOfCurrentPage）互斥出现。
const sourceExample = computed(() => {
  const sid = interactiveSourceId.value
  return sid ? (examples.value.find((e) => e.id === sid) ?? null) : null
})

// --- W8-W11 框架：sidecar 计算型 + 向导步骤 + quickRun ---
import { onMounted, ref, watch } from 'vue'
import { ChevronLeft, ChevronRight, Download } from 'lucide-vue-next'
import type { ToolResult } from '../../src/interactive-tools'
import { runBusy, runContext, runImages, runOutput, runSnippet } from '../../src/store/date-run'
import { parseSidecarOutput } from '../../src/sidecar-result'
import { pushToast } from '../../toast'
import { api } from '../../src/sidecar-client'

const isSidecar = computed(() => schema.value?.computeVia === 'sidecar')
// sidecar 计算型：结果 = 运行输出 <<<JSON>>> 段的解析（标记外文本仍在抽屉日志区可见）
const sidecarResult = computed<ToolResult | null>(() =>
  isSidecar.value ? parseSidecarOutput(runOutput.value).result : null
)
const sidecarRest = computed(() => (isSidecar.value ? parseSidecarOutput(runOutput.value).rest : ''))

// 运行结果上下文门控：runContext（页面+类型）与当前页匹配才显示输出/产物图。
// store 是模块级的，返回画廊再进新示例时组件重挂载、旧输出还在——按上下文隔离
// 既不串页，同一家族卡重进时又能恢复各自的上次结果。
const runContextKey = computed(() => `${schema.value?.id ?? ''}|${String(values.value.type ?? '')}`)
const runActive = computed(() => runContext.value === runContextKey.value)

const stepIndex = ref(0)
const steps = computed(() => schema.value?.steps ?? [])
const stepFields = computed(() => {
  if (!steps.value.length || !schema.value) return fields.value
  const keys = steps.value[stepIndex.value]?.keys ?? []
  const set = new Set(keys)
  return fields.value.filter((f) => set.has(f.key))
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
// 锁型：画廊家族卡进入（预选含 type）时示例身份已定，页内不提供类型下拉；
// 本组件跨 selectedId 复用实例（App.vue 无 key），切页须重置
const typeLocked = ref(false)
function autoRun(): void {
  if (!schema.value || quickRan.value || runBusy.value) return
  quickRan.value = true
  runSnippet(schema.value.id, code.value, runContextKey.value)
}
onMounted(() => {
  if (schema.value?.quickRun) autoRun()
})
watch(schema, (sc) => {
  stepIndex.value = 0
  quickRan.value = false
  typeLocked.value = false
  if (sc?.quickRun) autoRun()
})

/** 产物图下载（与代码抽屉同一主进程通道） */
async function downloadImage(url: string): Promise<void> {
  try {
    const r = await api.downloadResultImage(url)
    if (r.savedTo) pushToast('success', `已保存：${r.savedTo}`)
    else if (!r.canceled) pushToast('error', r.error || '保存失败')
  } catch {
    pushToast('error', '保存失败')
  }
}

// 路由携带的预选（类型/数据模式等）：落页（含同页换变体重路由）时逐键套用一次并清空。
// 键在当前字段表不存在、或 select 档位不含该值时静默跳过（回落页面默认）。
// immediate 必须开——首落场景 preset 在挂载前已设置，靠 immediate 补上这次消费。
watch(
  pendingPreset,
  (p) => {
    if (!p || !schema.value || schema.value.id !== p.pageId) return
    for (const [key, val] of Object.entries(p.values)) {
      const f = rawFields.value.find((x) => x.key === key)
      if (!f) continue
      if (f.type === 'select' && Array.isArray(f.options) && !f.options.some((o) => o.value === val)) continue
      values.value[key] = val
    }
    // 预选携带类型 → 示例身份固定，隐藏页内类型选择器
    if ('type' in p.values) typeLocked.value = true
    pendingPreset.value = null
  },
  { immediate: true }
)

/** required 且当前为空 → 传给 ToolField 标红（compute 侧同时出 error 引导） */
/** select 联动：options 函数形态按当前输入解析（静态 options 原样透传由 ToolField 兜底） */
function optionsOf(key: string): SelectOption[] | undefined {
  const f = fields.value.find((x) => x.key === key)
  if (!f || typeof f.options !== 'function') return undefined
  return f.options(values.value)
}

function isInvalid(key: string): boolean {
  const f = fields.value.find((x) => x.key === key)
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
        {{ header.title }}
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
      <button
        v-if="sourceExample"
        class="app-no-drag border border-line rounded-control bg-transparent text-ink-mute hover:text-accent hover:border-accent cursor-pointer px-2 py-1 text-caption"
        data-testid="it-source"
        :title="`查看原示例源码：${sourceExample.title}（${sourceExample.name}）`"
        @click="openDetail(sourceExample.id, true, { forceDetail: true })"
      >
        查看原示例源码
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
          <p class="text-control text-ink-mute m-0">{{ header.description }}</p>
          <div v-if="steps.length" class="flex items-center gap-2 mb-3">
            <template v-for="(st, i) in steps" :key="st.title">
              <span
                class="text-caption px-2 py-0.5 rounded-control"
                :class="
                  i === stepIndex
                    ? 'bg-accent text-on-accent font-medium'
                    : i < stepIndex
                      ? 'text-accent'
                      : 'text-ink-faint'
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
              @click="runSnippet(schema.id, code, runContextKey)"
            >
              ▶ {{ runActive && runOutput ? '重新运行' : '运行' }}
            </button>
          </div>
          <template v-if="isSidecar">
            <ToolResultPanel v-if="result?.error" :result="result" data-testid="sidecar-invalid" />
            <div
              v-else-if="runActive && runBusy"
              class="text-control text-ink-mute pt-4 text-center"
              data-testid="sidecar-running"
            >
              正在运行…
            </div>
            <ToolResultPanel
              v-else-if="runActive && sidecarResult"
              :result="sidecarResult"
              data-testid="sidecar-result"
            />
            <ToolResultPanel v-else-if="result" :result="result" data-testid="sidecar-echo" />
            <div v-else class="text-control text-ink-mute pt-4 text-center">点击「运行」获取结果</div>
            <div v-if="runActive && runImages.length" class="flex flex-wrap gap-3" data-testid="page-run-images">
              <figure
                v-for="img in runImages"
                :key="img"
                class="m-0 border border-line rounded-control overflow-hidden bg-panel w-[320px]"
              >
                <img :src="img" alt="运行产物" class="block w-full h-[240px] object-contain bg-page" />
                <figcaption class="flex items-center justify-end px-1.5 py-1">
                  <button
                    class="shrink-0 inline-flex items-center gap-1 px-1.5 py-0.5 text-caption border border-line rounded-control bg-panel text-ink-dim cursor-pointer transition-colors dur-fast hover:bg-hover hover:text-ink"
                    type="button"
                    @click="downloadImage(img)"
                  >
                    <Download :size="11" /> 下载
                  </button>
                </figcaption>
              </figure>
            </div>
            <pre
              v-if="runActive && sidecarRest"
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
        <CodeDrawer :code="code" :run-id="schema.id" :context-key="runContextKey" />
      </div>
    </template>
  </section>
</template>
