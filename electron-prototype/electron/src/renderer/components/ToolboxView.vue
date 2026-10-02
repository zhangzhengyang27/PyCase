<script setup lang="ts">
// ToolboxView：工具箱——与画廊总览同语法的分区落地页
// 头区：定位统计 + 搜索/收藏/排序（右侧对齐，几何与画廊总览一致）；
// 主体：「交互工具」组恒置顶（应用内交互页门面，渲染交互形态卡片），
// 其余按 source_dir 工具项目分区，卡片网格呈现；大项目默认露前 6 张，
// 区头右侧「展开全部」收放；搜索时自动全展开（避免匹配项被折叠藏住）。
import { computed, reactive } from 'vue'
import { ChevronDown, ChevronUp, SearchX, Star } from 'lucide-vue-next'
import { buildToolboxGroups } from '../src/toolbox-groups'
import { INTERACTIVE_GROUP_KEY, isInteractiveId } from '../src/interactive-tools'
import { openInteractive } from '../src/store/interactive'
import { toolboxIcon } from '../src/section-icons'
import {
  catalogToolsTotal,
  examples,
  favOnly,
  loadError,
  loading,
  sortBy,
  sortVExamples,
  toolboxItems,
  toolsTotal,
  toolSearchQuery
} from '../src/store/catalog'
import { openDetail, runFromCard } from '../src/store/detail'
import { isFavorite, toggleFavorite } from '../src/store/prefs'
import ExampleCard from './ExampleCard.vue'
import SkeletonCard from './base/SkeletonCard.vue'
import AppEmpty from './base/AppEmpty.vue'
import AlertBanner from './base/AlertBanner.vue'
import BaseButton from './base/BaseButton.vue'
import BaseInput from './base/BaseInput.vue'
import BaseSelect from './base/BaseSelect.vue'

const emit = defineEmits<{ reload: [] }>()

const PREVIEW_COUNT = 6

// 分组：交互工具（应用内页面，非 .py 示例）恒置顶成首组，其余按 source_dir 项目分组。
// 交互工具不进 buildToolboxGroups——它没有 source_dir，混进去会被归到「独立工具」，
// 与目录池的独立 .py 工具混淆；且它渲染的是交互形态卡片（无运行/质量分）。
const groups = computed(() => {
  const all = toolboxItems.value
  const inter = all.filter((t) => isInteractiveId(t.id))
  const rest = buildToolboxGroups(all.filter((t) => !isInteractiveId(t.id))).map((g) => ({
    ...g,
    items: sortVExamples(g.items)
  }))
  return inter.length ? [{ key: INTERACTIVE_GROUP_KEY, label: '交互工具', items: sortVExamples(inter) }, ...rest] : rest
})
// 产品裁决：工具项目 = source_dir 工具项目。「交互工具」是应用内页面门面、不是工具项目，
// 置顶成组只是展示形态，不计入项目数（否则页头会把 1 个交互页吹成 1 个项目）。
const projectCount = computed(
  () => groups.value.filter((g) => g.key !== 'standalone' && g.key !== INTERACTIVE_GROUP_KEY).length
)
// 统计口径与画廊总览一致：库级常量，不随搜索浮动。
// 分母用目录池口径 catalogToolsTotal：交互工具无 .py 文件、无 run_status，
// 计入分母会把「可静态运行率」稀释成假数字（分子只数目录池的可运行条目）。
const runnablePct = computed(() => {
  const total = catalogToolsTotal.value
  if (!total) return 0
  const ok = examples.value.filter((e) => e.category === 'tools' && e.run_status === 'runnable').length
  return Math.round((ok / total) * 100)
})

// 展开态（会话内记忆）：搜索词非空时强制全展开
const expanded = reactive<Record<string, boolean>>({})
function isExpanded(key: string): boolean {
  return expanded[key] || toolSearchQuery.value !== ''
}
function overflowCount(total: number): number {
  return Math.max(0, total - PREVIEW_COUNT)
}

function onRun(id: string): void {
  void runFromCard(id)
}
// 卡片打开路由：交互工具进应用内专属页（App.vue 按 selectedId 前缀分支），其余开详情。
// 专属页路由在 Task 11 接入 App.vue 前为中间态：仅切换 selectedId
function onOpen(id: string): void {
  if (isInteractiveId(id)) openInteractive(id)
  else void openDetail(id)
}
function toggleFavOnly(): void {
  favOnly.value = !favOnly.value
}

// 空态归因：空态下页头仍然可见，所以文案必须指明是哪个开关造成的，
// 否则「只看收藏」导致的空列表会被误导性地归咎于搜索词。
const emptyHint = computed(() => {
  if (toolSearchQuery.value.trim()) return '调整搜索词试试'
  if (favOnly.value) return '当前只显示已收藏的工具，点右上角星标可恢复'
  return '工具库中暂无示例'
})
</script>

<template>
  <section class="flex-1 min-w-0 min-h-0 flex bg-page overflow-hidden">
    <!-- 状态：加载 / 错误 / 空态 -->
    <div v-if="loading && examples.length === 0" class="flex-1 min-h-0 p-8">
      <div class="max-w-[1200px] mx-auto grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-4 content-start">
        <SkeletonCard v-for="i in 8" :key="i" />
      </div>
    </div>
    <div v-else-if="loadError" class="flex-1 flex flex-col items-center justify-center gap-3">
      <AlertBanner :title="`加载失败: ${loadError}`" class="w-[420px]" />
      <BaseButton variant="primary" @click="emit('reload')">重试</BaseButton>
    </div>

    <!-- 落地页：页头固定（app-drag 在滚动容器内不生效）+ 项目分区滚动。
         注意：工具池为空（搜索无匹配 / 只看收藏且无收藏）时，**页头必须留着**——
         它是关闭「只看收藏」、清空搜索词的唯一入口，随空态一起消失会把用户困死。 -->
    <div v-else class="flex-1 min-h-0 flex flex-col">
      <div class="app-drag select-none px-8 pt-7 pb-3">
        <div class="max-w-[1200px] mx-auto flex items-end justify-between gap-4">
          <div>
            <h1 class="text-[length:--text-page] font-semibold text-ink m-0 tracking-[-0.02em]">工具箱</h1>
            <p class="text-control text-ink-mute mt-1.5 mb-0">
              {{ toolsTotal }} 个工具 · {{ projectCount }} 个工具项目 · {{ runnablePct }}% 可静态运行
            </p>
          </div>
          <div class="app-no-drag flex items-center gap-2 shrink-0">
            <BaseInput v-model="toolSearchQuery" placeholder="搜索工具…" class="w-[220px]" />
            <BaseButton
              square
              :title="favOnly ? '显示全部工具' : '只看收藏'"
              :aria-label="favOnly ? '显示全部工具' : '只看收藏'"
              :aria-pressed="favOnly"
              @click="toggleFavOnly()"
            >
              <Star :size="15" :class="favOnly ? 'text-warn fill-current' : ''" />
            </BaseButton>
            <BaseSelect v-model="sortBy" title="排序（组内生效）">
              <option value="quality_desc">质量分优先</option>
              <option value="name">按名称</option>
              <option value="last_run">最近运行</option>
            </BaseSelect>
          </div>
        </div>
      </div>

      <!-- 项目分区（滚动层）：区头 + 卡片网格；工具池为空时同一滚动层内给空态 -->
      <div class="flex-1 min-h-0 overflow-y-auto">
        <div v-if="toolboxItems.length === 0" class="flex items-center justify-center pt-20">
          <AppEmpty :icon="SearchX" title="没有匹配的工具" :description="emptyHint" />
        </div>
        <div v-else class="max-w-[1200px] mx-auto px-8 pb-12">
          <section v-for="g in groups" :key="g.key" class="mb-9">
            <div class="flex items-center gap-2.5 mb-3">
              <span class="chip-ic">
                <component :is="toolboxIcon(g.key)" :size="15" :stroke-width="1.5" />
              </span>
              <h2 class="text-title font-semibold text-ink m-0">{{ g.label }}</h2>
              <span class="text-caption text-ink-mute">{{ g.items.length }} 个</span>
              <button
                v-if="overflowCount(g.items.length) > 0"
                class="ml-auto flex items-center gap-1 border-0 bg-transparent text-control text-ink-mute hover:text-accent cursor-pointer transition-colors dur-fast"
                @click="expanded[g.key] = !expanded[g.key]"
              >
                {{ isExpanded(g.key) ? '收起' : `展开全部 ${overflowCount(g.items.length)} 个` }}
                <component :is="isExpanded(g.key) ? ChevronUp : ChevronDown" :size="12" />
              </button>
            </div>
            <div class="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-4 content-start">
              <ExampleCard
                v-for="(ex, i) in isExpanded(g.key) ? g.items : g.items.slice(0, PREVIEW_COUNT)"
                :key="ex.id"
                :ex="ex"
                :enter-index="i"
                :faved="isFavorite(ex.id)"
                :interactive="isInteractiveId(ex.id)"
                @open="onOpen(ex.id)"
                @fav="toggleFavorite(ex.id)"
                @run="onRun(ex.id)"
              />
            </div>
          </section>
        </div>
      </div>
    </div>
  </section>
</template>
