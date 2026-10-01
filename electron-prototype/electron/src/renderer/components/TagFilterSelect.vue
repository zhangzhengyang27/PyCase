<script setup lang="ts">
// TagFilterSelect：工具栏「标签」多选下拉（checkbox 列表 + 计数）。
//
// 由旧 FilterSidebar 的标签分组迁出——筛选收成工具栏下拉后，标签是唯一的多选维度，
// 故独立成组件；单个标签的开关语义（activeTags 集合增删）与旧侧栏完全一致。
// 底座 = reka-ui Popover（不套 Portal：菜单是工具栏上的锚定浮层）——开合、
// Esc / 外点关闭、焦点圈定与归还、aria-expanded 由 reka-ui 承担。
import { computed, ref } from 'vue'
import { PopoverContent, PopoverRoot, PopoverTrigger } from 'reka-ui'
import { ChevronDown } from 'lucide-vue-next'
import { activeTags, examples, tagFacetsFor } from '../src/store/catalog'

const TAG_TOP_N = 10

const open = ref(false)
const showAll = ref(false)

// 画廊池为空时不起 facet（与旧侧栏同口径）；否则 TopN + 已选保底（tagFacetsFor 已处理保底）
const tags = computed(() => (examples.value.length === 0 ? [] : tagFacetsFor('gallery')))
const visibleTags = computed(() => (showAll.value ? tags.value : tags.value.slice(0, TAG_TOP_N)))
const hiddenCount = computed(() => Math.max(0, tags.value.length - TAG_TOP_N))
const activeCount = computed(() => activeTags.value.size)

function toggleTag(tag: string): void {
  const next = new Set(activeTags.value)
  if (next.has(tag)) next.delete(tag)
  else next.add(tag)
  activeTags.value = next
}
</script>

<template>
  <div class="relative shrink-0 app-no-drag">
    <PopoverRoot v-model:open="open">
      <PopoverTrigger as-child>
        <button
          type="button"
          class="inline-flex items-center gap-1.5 h-7 pl-2 pr-1.5 rounded-control border text-control cursor-pointer transition-colors dur-fast"
          :class="
            activeCount
              ? 'border-line-subtle bg-accent/12 text-accent-text'
              : 'border-line bg-page text-ink-dim hover:text-ink'
          "
          data-testid="tag-filter-select"
          :title="activeCount ? `标签（已选 ${activeCount} 个）` : '标签'"
        >
          <span>标签</span>
          <span
            v-if="activeCount"
            class="min-w-[16px] h-[16px] px-1 flex items-center justify-center rounded-control bg-accent text-on-accent text-badge font-mono"
            >{{ activeCount }}</span
          >
          <ChevronDown :size="13" class="shrink-0" />
        </button>
      </PopoverTrigger>

      <PopoverContent
        side="bottom"
        align="start"
        :side-offset="4"
        data-testid="tag-filter-menu"
        aria-label="标签筛选"
        class="z-50 w-64 max-h-[320px] overflow-y-auto bg-panel border border-line-subtle rounded-panel shadow-elev-3 py-1 outline-none"
      >
        <p v-if="tags.length === 0" class="px-3 py-2 m-0 text-control text-ink-faint">暂无标签</p>
        <label
          v-for="f in visibleTags"
          :key="f.tag"
          class="flex items-center gap-2 px-3 py-1 cursor-pointer text-control text-ink-dim hover:bg-hover hover:text-ink"
          :title="f.tag"
        >
          <input
            type="checkbox"
            class="accent-accent w-3.5 h-3.5 cursor-pointer shrink-0"
            :checked="activeTags.has(f.tag)"
            @change="toggleTag(f.tag)"
          />
          <span class="truncate font-mono lowercase">{{ f.tag }}</span>
          <span class="ml-auto shrink-0 text-caption text-ink-mute font-mono">{{ f.count }}</span>
        </label>
        <button
          v-if="hiddenCount > 0 || showAll"
          type="button"
          class="w-full flex items-center gap-1 h-6 px-3 mt-0.5 border-0 bg-transparent text-caption text-ink-mute hover:text-ink cursor-pointer"
          @click="showAll = !showAll"
        >
          {{ showAll ? '收起标签' : `展开全部（+${hiddenCount}）` }}
        </button>
      </PopoverContent>
    </PopoverRoot>
  </div>
</template>
