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
import { LayoutGrid, List, Star, X } from 'lucide-vue-next'
import { THEMES } from '../src/themes'
import {
  activeSectionKey,
  activeTheme,
  clearAllFilters,
  facetCounts,
  favOnly,
  filtered,
  galleryChips,
  persistViewPrefs,
  removeChip,
  searchQuery,
  sortBy,
  viewMode
} from '../src/store/catalog'
import { favorites } from '../src/store/prefs'
import BaseInput from './base/BaseInput.vue'
import BaseSelectMenu from './base/BaseSelectMenu.vue'
import TagFilterSelect from './TagFilterSelect.vue'

function setMode(v: 'grid' | 'list'): void {
  viewMode.value = v
  persistViewPrefs()
}

// 下拉变更经函数写回 store（主题随 viewPrefs 持久化，与旧侧栏一致）
function setTheme(v: string): void {
  activeTheme.value = v
  persistViewPrefs()
}
function toggleFavOnly(): void {
  favOnly.value = !favOnly.value
}

// 主题型分区（Turtle/Pygame/OpenCV/PIL/数据可视化）激活时，分区即主题——
// 主题维度被完全决定，下拉退场；再选主题只会叠出空集（selectSection 切换时也会清主题）
const THEME_KEYS = new Set(THEMES.map((t) => t.key))
const themeDropdownVisible = computed(() => !THEME_KEYS.has(activeSectionKey.value ?? ''))

// 档位计数后缀：'all' 不显示计数（facet 只对具体档位有意义）
function facetSuffix(has: boolean, n: number | undefined): string {
  return has && n ? ` (${n})` : ''
}
</script>

<template>
  <div class="app-drag select-none shrink-0 bg-panel border-b border-line-subtle">
    <!-- 工具行：搜索 + 筛选下拉 + 排序 + 密度（flex-wrap：窄窗换行，不横向溢出）。
         不再有面包屑行：分区名由页头标题表达、计数由芯片行承担——同一信息不出现第二遍 -->
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

      <!-- 主题：全部主题 + THEMES。主题型分区激活时退场（分区即主题）；
           非主题分区（标签组/项目/其他）保留——跨维度收窄仍有意义 -->
      <BaseSelectMenu
        v-if="themeDropdownVisible"
        :model-value="activeTheme"
        title="主题"
        aria-label="按主题筛选"
        testid="filter-theme"
        :active="activeTheme !== 'all'"
        :options="[
          { value: 'all', label: '全部主题' },
          ...THEMES.map((t) => ({
            value: t.key,
            label: t.label,
            hint: facetSuffix(true, facetCounts.themeCounts.get(t.key)) || undefined
          }))
        ]"
        @update:model-value="setTheme"
      />

      <!-- 标签（多选下拉：checkbox 列表 + 计数） -->
      <TagFilterSelect />

      <!-- 排序 + 密度：右推（不足则整体换行，自身恒一行高，不横向溢出）。
           组高恒等于 --toolbar-h（走查探针量这里）：控件 28px 居中，行几何不随内容漂 -->
      <div class="ml-auto flex items-center gap-2 shrink-0 h-[var(--toolbar-h)]">
        <BaseSelectMenu
          v-model="sortBy"
          title="排序"
          aria-label="排序方式"
          testid="filter-sort"
          :active="sortBy !== 'quality_desc'"
          align="end"
          :options="[
            { value: 'quality_desc', label: '质量分优先' },
            { value: 'name', label: '按名称' },
            { value: 'last_run', label: '最近运行' }
          ]"
        />

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

    <!-- 结果行：计数 + 生效筛选芯片（可移除 + 清空）。仅在有筛选/搜索时渲染——
         纯分区浏览时计数与页头统计重复，整行退场 -->
    <div
      v-if="galleryChips.length"
      class="app-no-drag flex items-center gap-1.5 px-4 pb-2 overflow-x-auto [scrollbar-width:none]"
    >
      <span class="shrink-0 text-caption text-ink-mute font-mono" aria-live="polite">{{ filtered.length }} 个结果</span>
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
        title="清空筛选（不退出当前分区）"
        @click="clearAllFilters()"
      >
        清空
      </button>
    </div>
  </div>
</template>
