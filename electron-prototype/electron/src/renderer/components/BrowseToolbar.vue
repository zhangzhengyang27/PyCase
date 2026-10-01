<script setup lang="ts">
// BrowseToolbar：画廊结果条（specs §4.2 变体）
// 行 1：面包屑（示例库 / 当前分区/范围标题）+ 右侧结果计数；
// 行 2：关键字搜索 + 筛选维度收成工具栏下拉（收藏开关 + 主题 / 可运行性 / 质量分 / 运行状态 / 标签）
//       + 排序 + 密度；控件多、必须 flex-wrap 优雅换行（窄窗不横向溢出）；
// 行 3：生效筛选芯片（可逐个移除 + 清空）；无筛选时不渲染。
//
// 关键字搜索走 searchQuery（防抖 120ms 写入 appliedSearch，另触发服务端代码检索——
// 契约 §5：列表不带 code，代码命中由 sidecar 按需读文件）。它是画廊唯一的文本检索入口，
// 筛选下拉只承担维度收窄，不能顶替它。
import { computed } from 'vue'
import { ArrowLeft, LayoutGrid, List, Star, X } from 'lucide-vue-next'
import { THEMES } from '../src/themes'
import { sectionLabelOf } from '../src/overview'
import { QUALITY_OPTIONS, RUN_STATUS_OPTIONS, RUNNABLE_OPTIONS, type RunStatusKey } from '../src/filter-options'
import type { RunnableFilter } from '../src/filter-engine'
import {
  activeRunnable,
  activeRunStatus,
  activeSectionKey,
  activeTheme,
  clearAllFilters,
  facetCounts,
  favOnly,
  filtered,
  galleryChips,
  minQuality,
  persistViewPrefs,
  removeChip,
  searchQuery,
  selectSection,
  sortBy,
  viewMode
} from '../src/store/catalog'
import { favorites } from '../src/store/prefs'
import BaseInput from './base/BaseInput.vue'
import BaseSelect from './base/BaseSelect.vue'
import TagFilterSelect from './TagFilterSelect.vue'

// 范围标题：分区（侧栏二级菜单）> 主题 facet > 全部示例
const title = computed(() => {
  const sec = sectionLabelOf(activeSectionKey.value)
  if (sec) return sec
  const theme = THEMES.find((t) => t.key === activeTheme.value)
  if (theme) return theme.label
  return '全部示例'
})

function showAll(): void {
  selectSection(null)
}

function setMode(v: 'grid' | 'list'): void {
  viewMode.value = v
  persistViewPrefs()
}

// 下拉变更经函数写回 store（主题 / 质量分随 viewPrefs 持久化，与旧侧栏一致）
function setTheme(v: string): void {
  activeTheme.value = v
  persistViewPrefs()
}
function setRunnable(v: string): void {
  activeRunnable.value = v as RunnableFilter
}
function setQuality(v: string): void {
  minQuality.value = Number(v)
  persistViewPrefs()
}
function setRunStatus(v: string): void {
  activeRunStatus.value = v as RunStatusKey
}
function toggleFavOnly(): void {
  favOnly.value = !favOnly.value
}

// 档位计数后缀：'all' 不显示计数（facet 只对具体档位有意义）
function facetSuffix(has: boolean, n: number | undefined): string {
  return has && n ? ` (${n})` : ''
}
</script>

<template>
  <div class="app-drag select-none shrink-0 bg-panel border-b border-line-subtle">
    <!-- 行 1：面包屑结果条（specs §4.2） -->
    <div class="flex items-center gap-1.5 px-4 h-[var(--statusbar-h)] border-b border-line-hairline text-caption">
      <button
        class="app-no-drag flex items-center gap-1 h-5 px-1.5 rounded-control border-0 bg-transparent text-caption text-ink-mute hover:text-ink hover:bg-hover cursor-pointer shrink-0 transition-colors dur-fast"
        title="全部示例"
        @click="showAll()"
      >
        <ArrowLeft :size="12" /> 示例库
      </button>
      <span class="text-ink-faint" aria-hidden="true">/</span>
      <span class="app-no-drag font-medium text-ink-dim truncate" :title="title">{{ title }}</span>
      <span class="ml-auto text-ink-mute font-mono shrink-0" aria-live="polite">{{ filtered.length }} 个结果</span>
    </div>

    <!-- 行 2：搜索 + 筛选下拉 + 排序 + 密度（flex-wrap：窄窗换行，不横向溢出） -->
    <div
      class="flex flex-wrap items-center gap-x-2 gap-y-1.5 px-4 py-1 min-h-[var(--toolbar-h)]"
      data-testid="browse-toolbar-row"
    >
      <!-- 关键字搜索：元数据 + 源码双通道，与筛选下拉并列（筛选只做维度收窄）。
           宽度加在外层 div——BaseInput 根元素自带 w-full，直接给它 class 会打架 -->
      <div class="app-no-drag w-[184px] shrink-0" data-testid="gallery-search">
        <BaseInput
          v-model="searchQuery"
          placeholder="搜索示例名 / 源码…"
          title="关键字搜索（名称、摘要、标签；≥2 字同时检索源码）"
          aria-label="搜索示例"
        />
      </div>

      <!-- 只看收藏（开关：按钮，不塞进下拉） -->
      <button
        type="button"
        class="app-no-drag inline-flex items-center gap-1.5 h-7 px-2 rounded-control border text-control cursor-pointer transition-colors dur-fast shrink-0"
        :class="
          favOnly
            ? 'border-line-subtle bg-accent/12 text-accent-text'
            : 'border-line bg-page text-ink-dim hover:text-ink'
        "
        :title="favOnly ? '显示全部示例' : '只看收藏'"
        :aria-pressed="favOnly"
        data-testid="filter-fav-toggle"
        @click="toggleFavOnly()"
      >
        <Star :size="13" :class="favOnly ? 'fill-current' : ''" />
        <span>收藏</span>
        <span v-if="favorites.size" class="text-caption text-ink-mute font-mono">{{ favorites.size }}</span>
      </button>

      <!-- 主题：全部主题 + THEMES（与侧栏分区菜单可叠加，两者语义不同，不去重） -->
      <BaseSelect :model-value="activeTheme" title="主题" data-testid="filter-theme" @update:model-value="setTheme">
        <option value="all">全部主题</option>
        <option v-for="t in THEMES" :key="t.key" :value="t.key">
          {{ t.label }}{{ facetSuffix(true, facetCounts.themeCounts.get(t.key)) }}
        </option>
      </BaseSelect>

      <!-- 可运行性 -->
      <BaseSelect
        :model-value="activeRunnable"
        title="可运行性"
        data-testid="filter-runnable"
        @update:model-value="setRunnable"
      >
        <option v-for="r in RUNNABLE_OPTIONS" :key="r.key" :value="r.key">
          {{ r.label }}{{ r.key === 'all' ? '' : facetSuffix(true, facetCounts.runnableCounts.get(r.key)) }}
        </option>
      </BaseSelect>

      <!-- 质量分 -->
      <BaseSelect
        :model-value="String(minQuality)"
        title="质量分"
        data-testid="filter-quality"
        @update:model-value="setQuality"
      >
        <option v-for="q in QUALITY_OPTIONS" :key="q.min" :value="String(q.min)">
          {{ q.label }}{{ q.min > 0 ? facetSuffix(true, facetCounts.qualityCounts.get(q.min)) : '' }}
        </option>
      </BaseSelect>

      <!-- 运行状态 -->
      <BaseSelect
        :model-value="activeRunStatus"
        title="运行状态"
        data-testid="filter-run-status"
        @update:model-value="setRunStatus"
      >
        <option v-for="s in RUN_STATUS_OPTIONS" :key="s.key" :value="s.key">
          {{ s.label }}{{ s.key === 'all' ? '' : facetSuffix(true, facetCounts.runStatusCounts.get(s.key)) }}
        </option>
      </BaseSelect>

      <!-- 标签（多选下拉：checkbox 列表 + 计数） -->
      <TagFilterSelect />

      <!-- 排序 + 密度：右推（不足则整体换行，自身恒一行高，不横向溢出） -->
      <div class="ml-auto flex items-center gap-2 shrink-0 h-[var(--toolbar-h)]">
        <BaseSelect v-model="sortBy" title="排序" data-testid="filter-sort" class="app-no-drag">
          <option value="quality_desc">质量分优先</option>
          <option value="name">按名称</option>
          <option value="last_run">最近运行</option>
        </BaseSelect>

        <div class="app-no-drag seg shrink-0" role="group" aria-label="浏览密度">
          <button title="网格视图" aria-label="网格视图" :aria-pressed="viewMode === 'grid'" @click="setMode('grid')">
            <LayoutGrid :size="13" :stroke-width="1.5" /> 网格
          </button>
          <button title="列表视图" aria-label="列表视图" :aria-pressed="viewMode === 'list'" @click="setMode('list')">
            <List :size="13" :stroke-width="1.5" /> 列表
          </button>
        </div>
      </div>
    </div>

    <!-- 行 3：生效筛选芯片（可移除 + 清空）；无筛选时整行不渲染 -->
    <div
      v-if="galleryChips.length"
      class="app-no-drag flex items-center gap-1.5 px-4 pb-2 overflow-x-auto [scrollbar-width:none]"
    >
      <span
        v-for="chip in galleryChips"
        :key="chip.key + ':' + chip.value"
        class="inline-flex items-center gap-1 h-6 pl-2 pr-1 rounded-control bg-accent/12 text-accent-text text-caption shrink-0 whitespace-nowrap"
      >
        {{ chip.label }}
        <button
          class="w-4 h-4 flex items-center justify-center rounded-control border-0 bg-transparent cursor-pointer text-accent-text hover:text-ink hover:bg-accent/20 transition-colors dur-fast"
          :title="`移除筛选：${chip.label}`"
          :aria-label="`移除筛选：${chip.label}`"
          @click="removeChip(chip)"
        >
          <X :size="10" />
        </button>
      </span>
      <button
        class="shrink-0 border-0 bg-transparent text-caption text-ink-mute hover:text-ink cursor-pointer whitespace-nowrap"
        @click="clearAllFilters()"
      >
        清空
      </button>
    </div>
  </div>
</template>
