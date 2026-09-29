<script setup lang="ts">
// BrowseToolbar：画廊浏览态双行结果条（总览下钻后的工具条，specs §4.2）
// 行 1：面包屑（示例库 / 当前主题/范围标题）+ 右侧结果计数；
// 行 2：筛选芯片（可逐个移除 + 清空）+ 排序 + 网格/清单密度切换（viewMode 随 viewPrefs 持久化）。
import { computed } from 'vue'
import { ArrowLeft, LayoutGrid, List, X } from 'lucide-vue-next'
import { THEMES } from '../src/themes'
import { tagSectionLabel, PROJECTS_SECTION_META } from '../src/overview'
import {
  activeCategory,
  activeSectionTags,
  activeTheme,
  clearAllFilters,
  filtered,
  galleryChips,
  galleryMode,
  persistViewPrefs,
  removeChip,
  sortBy,
  viewMode
} from '../store'
import BaseSelect from './base/BaseSelect.vue'

// 范围标题：主题 > 分区标签组 > 项目区 > 全部示例（三种范围在 store 内互斥）
const title = computed(() => {
  const theme = THEMES.find((t) => t.key === activeTheme.value)
  if (theme) return theme.label
  if (activeSectionTags.value.length > 0) return tagSectionLabel(activeSectionTags.value) || '全部分区'
  if (activeCategory.value === 'projects') return PROJECTS_SECTION_META.label
  return '全部示例'
})

// 同 FilterSidebar 约定：模板不直接赋值导入的 ref，全部经函数变更
function backToOverview(): void {
  galleryMode.value = 'overview'
}

function setMode(v: 'grid' | 'list'): void {
  viewMode.value = v
  persistViewPrefs()
}
</script>

<template>
  <div class="app-drag select-none shrink-0 bg-panel border-b border-line-subtle">
    <!-- 行 1：面包屑结果条（specs §4.2） -->
    <div class="flex items-center gap-1.5 px-4 h-[var(--statusbar-h)] border-b border-line-hairline text-caption">
      <button
        class="app-no-drag flex items-center gap-1 h-5 px-1.5 rounded-control border-0 bg-transparent text-caption text-ink-mute hover:text-ink hover:bg-hover cursor-pointer shrink-0 transition-colors dur-fast"
        title="返回总览"
        @click="backToOverview()"
      >
        <ArrowLeft :size="12" /> 示例库
      </button>
      <span class="text-ink-faint" aria-hidden="true">/</span>
      <span class="app-no-drag font-medium text-ink-dim truncate" :title="title">{{ title }}</span>
      <span class="ml-auto text-ink-mute font-mono shrink-0" aria-live="polite">{{ filtered.length }} 个结果</span>
    </div>

    <!-- 行 2：筛选芯片 + 排序 + 密度 -->
    <div class="flex items-center gap-2 px-4 h-[var(--toolbar-h)]">
      <div v-if="galleryChips.length" class="app-no-drag flex-1 min-w-0 flex items-center gap-1.5 overflow-x-auto [scrollbar-width:none]">
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
      <div v-else class="flex-1"></div>

      <BaseSelect v-model="sortBy" title="排序" class="app-no-drag shrink-0">
        <option value="quality_desc">质量分优先</option>
        <option value="name">按名称</option>
        <option value="last_run">最近运行</option>
      </BaseSelect>

      <div class="app-no-drag seg shrink-0" role="group" aria-label="浏览密度">
        <button
          title="网格视图"
          aria-label="网格视图"
          :aria-pressed="viewMode === 'grid'"
          @click="setMode('grid')"
        >
          <LayoutGrid :size="13" :stroke-width="1.5" /> 网格
        </button>
        <button
          title="列表视图"
          aria-label="列表视图"
          :aria-pressed="viewMode === 'list'"
          @click="setMode('list')"
        >
          <List :size="13" :stroke-width="1.5" /> 列表
        </button>
      </div>
    </div>
  </div>
</template>
