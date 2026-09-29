<script setup lang="ts">
// FilterSidebar：画廊/工具箱共用筛选侧栏（设计规范 v1，替代旧 FilterBar 顶部芯片平铺）
// 行式分组 + 右侧计数；分组可折叠（次要维度默认收起，降低常驻行数）；
// 可折叠为图标条（显示激活筛选数）；单根元素，同时修复旧 FilterBar fragment
// 根导致外部 class 全部丢失的问题。
import { computed, reactive, ref } from 'vue'
import {
  BarChart3,
  Camera,
  ChevronDown,
  ChevronRight,
  ChevronUp,
  Gamepad2,
  Image as ImageIcon,
  PanelLeftClose,
  PanelLeftOpen,
  Star,
  Turtle,
  X,
  type LucideIcon
} from 'lucide-vue-next'
import { THEMES } from '../src/themes'
import BaseInput from './base/BaseInput.vue'
import {
  activeRunnable,
  activeRunStatus,
  activeTags,
  activeTheme,
  clearFilters,
  examples,
  facetCounts,
  favOnly,
  favorites,
  minQuality,
  persistViewPrefs,
  searchQuery,
  tagFacetsFor,
  toolSearchQuery
} from '../store'

const props = defineProps<{ scope: 'gallery' | 'toolbox' }>()

const collapsed = ref(false)
const showAllTags = ref(false)

// 分组折叠态（会话内记忆，不持久化）：主题/质量分为次要维度默认收起，
// 高频维度（运行状态/可运行性/标签）默认展开
const openGroups = reactive<Record<string, boolean>>({
  runStatus: true,
  runnable: true,
  theme: false,
  quality: false,
  tags: true
})
function toggleGroup(key: string): void {
  openGroups[key] = !openGroups[key]
}

const THEME_ICONS: Record<string, LucideIcon> = {
  turtle: Turtle,
  games: Gamepad2,
  opencv: Camera,
  images: ImageIcon,
  viz: BarChart3
}

// 视图各自的搜索词经同一输入框读写
const query = computed<string>({
  get: () => (props.scope === 'gallery' ? searchQuery.value : toolSearchQuery.value),
  set: (v) => {
    if (props.scope === 'gallery') searchQuery.value = v
    else toolSearchQuery.value = v
  }
})

const tags = computed(() => (examples.value.length === 0 ? [] : tagFacetsFor(props.scope)))
const TAG_TOP_N = 10
const visibleTags = computed(() => (showAllTags.value ? tags.value : tags.value.slice(0, TAG_TOP_N)))
const hiddenTagCount = computed(() => Math.max(0, tags.value.length - TAG_TOP_N))

const RUN_STATUS_FACETS = [
  { key: 'all', label: '全部' },
  { key: 'ok', label: '成功过' },
  { key: 'failed', label: '失败过' },
  { key: 'never', label: '未运行' }
] as const
// 可运行性（代码体检派生状态）≠ 运行状态（本机运行历史），两个维度互补
const RUNNABLE_FACETS = [
  { key: 'all', label: '全部' },
  { key: 'runnable', label: '可运行', hint: '静态检查通过的推定状态' },
  { key: 'missing_deps', label: '缺依赖', hint: '依赖的第三方库在共享环境中缺失' },
  { key: 'empty', label: '空壳', hint: '去除 docstring 后没有有效代码' },
  { key: 'broken', label: '语法损坏', hint: '代码存在语法错误' },
  { key: 'risky', label: '高危', hint: '含高危操作，运行前需确认' }
] as const
const QUALITY_FACETS = [
  { min: 0, label: '全部' },
  { min: 90, label: '90+' },
  { min: 80, label: '80+' },
  { min: 60, label: '60+' }
]

const ROW_CLS =
  'flex items-center gap-2 w-full h-[var(--row-h)] px-2 rounded-control border-0 bg-transparent text-control text-left cursor-pointer transition-colors dur-fast text-ink-dim hover:bg-hover hover:text-ink'
// 选中行 = 强调色淡底（筛选是选中态，强调色允许出现在这里）
const ROW_ACTIVE_CLS = 'bg-accent/15 text-ink'
// 组头按钮：chevron + 组名 + 激活数徽标（折叠后激活状态仍可见）
const GROUP_CLS =
  'flex items-center gap-1 w-full h-[var(--row-h)] px-2 mb-0.5 border-0 bg-transparent text-caption font-medium text-ink-mute tracking-[0.04em] hover:text-ink-dim cursor-pointer transition-colors dur-fast'
const GROUP_BADGE_CLS =
  'min-w-[16px] h-[16px] px-1 flex items-center justify-center rounded-control bg-accent text-on-accent text-badge font-mono'
const ICON_BTN =
  'w-7 h-7 flex items-center justify-center rounded-control border-0 bg-transparent text-ink-mute hover:text-ink hover:bg-hover cursor-pointer shrink-0'

// 各分组的激活维度数（组头徽标；标签组为选中标签个数）
const groupActiveCounts = computed<Record<string, number>>(() => ({
  runStatus: activeRunStatus.value !== 'all' ? 1 : 0,
  runnable: activeRunnable.value !== 'all' ? 1 : 0,
  theme: props.scope === 'gallery' && activeTheme.value !== 'all' ? 1 : 0,
  quality: props.scope === 'gallery' && minQuality.value > 0 ? 1 : 0,
  tags: activeTags.value.size
}))

// 同旧 FilterBar：模板不直接赋值导入的 ref，全部经函数变更
function setStatus(k: 'all' | 'ok' | 'failed' | 'never'): void {
  activeRunStatus.value = k
}
function setRunnable(k: (typeof RUNNABLE_FACETS)[number]['key']): void {
  activeRunnable.value = k
}
function setTheme(k: string): void {
  activeTheme.value = k
  persistViewPrefs()
}
function setQuality(n: number): void {
  minQuality.value = n
  persistViewPrefs()
}
function toggleTag(tag: string): void {
  const next = new Set(activeTags.value)
  if (next.has(tag)) next.delete(tag)
  else next.add(tag)
  activeTags.value = next
}
function toggleFavOnly(): void {
  favOnly.value = !favOnly.value
}

const hasExtraFilters = computed(() => {
  // 主题/质量分是画廊专属维度，不参与工具箱的「清除筛选」显示判定
  if (props.scope === 'gallery' && (activeTheme.value !== 'all' || minQuality.value > 0)) return true
  return activeRunStatus.value !== 'all' || activeRunnable.value !== 'all' || activeTags.value.size > 0
})

// 折叠态徽标：当前激活的筛选维度数
const activeFilterCount = computed(
  () =>
    Number(activeRunStatus.value !== 'all') +
    Number(activeRunnable.value !== 'all') +
    (props.scope === 'gallery' ? Number(activeTheme.value !== 'all') + Number(minQuality.value > 0) : 0) +
    activeTags.value.size +
    Number(favOnly.value)
)
</script>

<template>
  <aside
    :class="collapsed ? 'w-11' : 'w-[232px]'"
    class="shrink-0 flex flex-col bg-panel border-r border-line-subtle min-h-0"
  >
    <div
      class="app-drag select-none flex items-center h-10 px-2 border-b border-line-subtle shrink-0"
      :class="{ 'justify-center': collapsed }"
    >
      <button
        class="app-no-drag"
        :class="ICON_BTN"
        :title="collapsed ? '展开筛选栏' : '收起筛选栏'"
        :aria-label="collapsed ? '展开筛选栏' : '收起筛选栏'"
        :aria-expanded="!collapsed"
        @click="collapsed = !collapsed"
      >
        <component :is="collapsed ? PanelLeftOpen : PanelLeftClose" :size="15" />
      </button>
      <span v-if="!collapsed" class="ml-1.5 text-caption font-medium text-ink-mute tracking-[0.08em]">筛选</span>
    </div>

    <template v-if="!collapsed">
      <div class="p-2 border-b border-line-subtle shrink-0">
        <BaseInput
          v-model="query"
          :placeholder="scope === 'gallery' ? '搜索名称 / 标签 / 代码…' : '搜索工具…'"
          :aria-label="scope === 'gallery' ? '搜索示例（名称、标签、代码）' : '搜索工具'"
          :spellcheck="false"
        />
      </div>

      <div class="flex-1 overflow-y-auto px-2 py-2.5 space-y-4">
        <!-- 收藏 -->
        <button :class="[ROW_CLS, favOnly ? ROW_ACTIVE_CLS : '']" title="只看收藏" :aria-pressed="favOnly" @click="toggleFavOnly()">
          <Star :size="13" :class="favOnly ? 'text-warn fill-current' : 'text-ink-mute'" />
          <span>收藏</span>
          <span v-if="favorites.size" class="ml-auto text-caption text-ink-mute font-mono">{{ favorites.size }}</span>
        </button>

        <!-- 运行状态 -->
        <div>
          <button :class="GROUP_CLS" :aria-expanded="openGroups.runStatus" @click="toggleGroup('runStatus')">
            <component :is="openGroups.runStatus ? ChevronDown : ChevronRight" :size="12" class="shrink-0" />
            <span>运行状态</span>
            <span v-if="groupActiveCounts.runStatus" :class="GROUP_BADGE_CLS">{{ groupActiveCounts.runStatus }}</span>
          </button>
          <div v-show="openGroups.runStatus">
            <button
              v-for="s in RUN_STATUS_FACETS"
              :key="s.key"
              :class="[ROW_CLS, activeRunStatus === s.key ? ROW_ACTIVE_CLS : '']"
              :aria-pressed="activeRunStatus === s.key"
              @click="setStatus(s.key)"
            >
              <span>{{ s.label }}</span>
            </button>
          </div>
        </div>

        <!-- 可运行性 -->
        <div>
          <button :class="GROUP_CLS" :aria-expanded="openGroups.runnable" @click="toggleGroup('runnable')">
            <component :is="openGroups.runnable ? ChevronDown : ChevronRight" :size="12" class="shrink-0" />
            <span>可运行性</span>
            <span v-if="groupActiveCounts.runnable" :class="GROUP_BADGE_CLS">{{ groupActiveCounts.runnable }}</span>
          </button>
          <div v-show="openGroups.runnable">
            <button
              v-for="r in RUNNABLE_FACETS"
              :key="r.key"
              :class="[ROW_CLS, activeRunnable === r.key ? ROW_ACTIVE_CLS : '']"
              :aria-pressed="activeRunnable === r.key"
              :title="'hint' in r && r.hint ? r.hint : undefined"
              @click="setRunnable(r.key)"
            >
              <span>{{ r.label }}</span>
              <span
                v-if="'key' in r && r.key !== 'all' && facetCounts.runnableCounts.get(r.key)"
                class="ml-auto text-caption text-ink-mute font-mono"
                >{{ facetCounts.runnableCounts.get(r.key) }}</span
              >
            </button>
          </div>
        </div>

        <!-- 主题 / 质量（画廊专属，次要维度默认收起） -->
        <template v-if="scope === 'gallery'">
          <div>
            <button :class="GROUP_CLS" :aria-expanded="openGroups.theme" @click="toggleGroup('theme')">
              <component :is="openGroups.theme ? ChevronDown : ChevronRight" :size="12" class="shrink-0" />
              <span>主题</span>
              <span v-if="groupActiveCounts.theme" :class="GROUP_BADGE_CLS">{{ groupActiveCounts.theme }}</span>
            </button>
            <div v-show="openGroups.theme">
              <button
                :class="[ROW_CLS, activeTheme === 'all' ? ROW_ACTIVE_CLS : '']"
                :aria-pressed="activeTheme === 'all'"
                @click="setTheme('all')"
              >
                <span>全部主题</span>
              </button>
              <button
                v-for="t in THEMES"
                :key="t.key"
                :class="[ROW_CLS, activeTheme === t.key ? ROW_ACTIVE_CLS : '']"
                :aria-pressed="activeTheme === t.key"
                :title="t.placeholder"
                @click="setTheme(t.key)"
              >
                <component :is="THEME_ICONS[t.key]" :size="13" class="shrink-0 text-ink-mute" />
                <span class="truncate">{{ t.label }}</span>
                <span class="ml-auto text-caption text-ink-mute font-mono">{{ facetCounts.themeCounts.get(t.key) || 0 }}</span>
              </button>
            </div>
          </div>
          <div>
            <button :class="GROUP_CLS" :aria-expanded="openGroups.quality" @click="toggleGroup('quality')">
              <component :is="openGroups.quality ? ChevronDown : ChevronRight" :size="12" class="shrink-0" />
              <span>质量分</span>
              <span v-if="groupActiveCounts.quality" :class="GROUP_BADGE_CLS">{{ groupActiveCounts.quality }}</span>
            </button>
            <div v-show="openGroups.quality">
              <button
                v-for="qf in QUALITY_FACETS"
                :key="qf.min"
                :class="[ROW_CLS, minQuality === qf.min ? ROW_ACTIVE_CLS : '']"
                :aria-pressed="minQuality === qf.min"
                @click="setQuality(qf.min)"
              >
                <span>{{ qf.label }}</span>
                <span v-if="qf.min > 0" class="ml-auto text-caption text-ink-mute font-mono">{{
                  facetCounts.qualityCounts.get(qf.min) || 0
                }}</span>
              </button>
            </div>
          </div>
        </template>

        <!-- 标签（Top 10 + 展开） -->
        <div v-if="tags.length > 0">
          <button :class="GROUP_CLS" :aria-expanded="openGroups.tags" @click="toggleGroup('tags')">
            <component :is="openGroups.tags ? ChevronDown : ChevronRight" :size="12" class="shrink-0" />
            <span>标签</span>
            <span v-if="groupActiveCounts.tags" :class="GROUP_BADGE_CLS">{{ groupActiveCounts.tags }}</span>
          </button>
          <div v-show="openGroups.tags">
            <button
              v-for="f in visibleTags"
              :key="f.tag"
              :class="[ROW_CLS, activeTags.has(f.tag) ? ROW_ACTIVE_CLS : '']"
              :aria-pressed="activeTags.has(f.tag)"
              :title="f.tag"
              @click="toggleTag(f.tag)"
            >
              <span class="truncate font-mono lowercase">{{ f.tag }}</span>
              <span class="ml-auto text-caption text-ink-mute font-mono">{{ f.count }}</span>
            </button>
            <button
              v-if="hiddenTagCount > 0 || showAllTags"
              class="flex items-center gap-1 h-6 px-2 mt-0.5 border-0 bg-transparent text-caption text-ink-mute hover:text-ink cursor-pointer"
              @click="showAllTags = !showAllTags"
            >
              <component :is="showAllTags ? ChevronUp : ChevronDown" :size="12" />
              {{ showAllTags ? '收起标签' : `展开全部（+${hiddenTagCount}）` }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="hasExtraFilters" class="p-2 border-t border-line-subtle shrink-0">
        <button :class="ROW_CLS" @click="clearFilters()">
          <X :size="13" />
          <span>清除筛选</span>
        </button>
      </div>
    </template>

    <!-- 折叠态：激活筛选数徽标 -->
    <div v-else class="flex-1 flex flex-col items-center pt-3">
      <span
        v-if="activeFilterCount"
        class="min-w-[18px] h-[18px] px-1 flex items-center justify-center rounded-control bg-accent text-on-accent text-badge font-mono"
        >{{ activeFilterCount }}</span
      >
    </div>
  </aside>
</template>
