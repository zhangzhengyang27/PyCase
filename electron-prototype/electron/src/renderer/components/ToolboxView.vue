<script setup lang="ts">
// ToolboxView：工具箱——与画廊总览同语法的分区落地页
// 头区：定位统计 + 搜索/收藏/排序（右侧对齐，几何与画廊总览一致）；
// 主体：按 source_dir 工具项目分区，卡片网格呈现；大项目默认露前 6 张，
// 区头右侧「展开全部」收放；搜索时自动全展开（避免匹配项被折叠藏住）。
import { computed, reactive } from 'vue'
import {
  ChevronDown,
  ChevronUp,
  Database,
  Download,
  FileSpreadsheet,
  Globe,
  MessageSquare,
  Paperclip,
  SearchX,
  Star,
  Timer,
  Wand2,
  Wrench,
  type LucideIcon
} from 'lucide-vue-next'
import { buildToolboxGroups } from '../src/toolbox-groups'
import {
  examples,
  favOnly,
  isFavorite,
  loadError,
  loading,
  openDetail,
  runFromCard,
  sortBy,
  sortVExamples,
  toggleFavorite,
  toolboxItems,
  toolsTotal,
  toolSearchQuery
} from '../store'
import ExampleCard from './ExampleCard.vue'
import SkeletonCard from './base/SkeletonCard.vue'
import AppEmpty from './base/AppEmpty.vue'
import AlertBanner from './base/AlertBanner.vue'
import BaseButton from './base/BaseButton.vue'
import BaseInput from './base/BaseInput.vue'
import BaseSelect from './base/BaseSelect.vue'

const emit = defineEmits<{ reload: [] }>()

const PREVIEW_COUNT = 6

// 与内置工具项目对应的 Lucide 图标（沿用设计系统线性图标语言，未收录项目回退 Wrench）
const PROJECT_ICONS: Record<string, LucideIcon> = {
  'db-table-dictionary-generator': Database,
  'excel-row-to-in-clause': FileSpreadsheet,
  'python-black-magic': Wand2,
  'remote-sftp-downloader': Download,
  'tkinter-work-countdown': Timer,
  'utility-crawlers': Globe,
  'wechat-official-account': MessageSquare,
  standalone: Paperclip
}
const FALLBACK_ICON = Wrench
const FALLBACK_HUE = '#64748b'

// 区头色相（specs §3.2 工具箱侧；键与 PROJECT_ICONS 对齐，未收录回退石板灰）
const TOOLBOX_HUES: Record<string, string> = {
  'db-table-dictionary-generator': '#2fb8a6',
  'excel-row-to-in-clause': '#2fa866',
  'python-black-magic': '#9a6bf2',
  'remote-sftp-downloader': '#38a8e0',
  'tkinter-work-countdown': '#d9a03d',
  'utility-crawlers': '#e07840',
  'wechat-official-account': '#2fa866',
  standalone: FALLBACK_HUE
}
function groupHue(key: string): Record<string, string> {
  return { '--hue': TOOLBOX_HUES[key] || FALLBACK_HUE }
}

const groups = computed(() => buildToolboxGroups(toolboxItems.value).map((g) => ({ ...g, items: sortVExamples(g.items) })))
const projectCount = computed(() => groups.value.filter((g) => g.key !== 'standalone').length)
// 统计口径与画廊总览一致：库级常量，不随搜索浮动
const runnablePct = computed(() => {
  const total = toolsTotal.value
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

function iconOf(key: string): LucideIcon {
  return PROJECT_ICONS[key] || FALLBACK_ICON
}

function onRun(id: string): void {
  void runFromCard(id)
}
function toggleFavOnly(): void {
  favOnly.value = !favOnly.value
}
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
    <div v-else-if="toolboxItems.length === 0" class="flex-1 flex items-center justify-center">
      <AppEmpty :icon="SearchX" title="没有匹配的工具" description="调整搜索词试试" />
    </div>

    <!-- 落地页：页头固定（app-drag 在滚动容器内不生效）+ 项目分区滚动 -->
    <div v-else class="flex-1 min-h-0 flex flex-col">
      <div class="app-drag select-none px-8 pt-7 pb-3">
        <div class="max-w-[1200px] mx-auto flex items-end justify-between gap-4">
          <div>
            <h1 class="text-page font-[650] text-ink m-0 tracking-[-0.02em]">工具箱</h1>
            <p class="text-control text-ink-faint mt-1.5 mb-0">
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

      <!-- 项目分区（滚动层）：区头 + 卡片网格 -->
      <div class="flex-1 min-h-0 overflow-y-auto">
        <div class="max-w-[1200px] mx-auto px-8 pb-12">
          <section v-for="g in groups" :key="g.key" class="mb-9">
            <div class="flex items-center gap-2.5 mb-3">
              <div class="hue-chip w-7 h-7 rounded-control flex items-center justify-center shrink-0" :style="groupHue(g.key)">
                <component :is="iconOf(g.key)" :size="15" />
              </div>
              <h2 class="text-title font-[590] text-ink m-0">{{ g.label }}</h2>
              <span class="text-caption text-ink-faint">{{ g.items.length }} 个</span>
              <button
                v-if="overflowCount(g.items.length) > 0"
                class="ml-auto flex items-center gap-1 border-0 bg-transparent text-control text-ink-mute hover:text-accent cursor-pointer transition-colors duration-150"
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
                @open="openDetail(ex.id)"
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
