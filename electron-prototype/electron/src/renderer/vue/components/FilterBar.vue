<script setup lang="ts">
// FilterBar：筛选条芯片组（运行状态 × 主题 × 质量分 × 标签 × 清除筛选）
// 数据与口径全部来自 store（computed 派生），本组件只负责渲染与交互；
// 计数基准 = 剥离 theme/quality/tags 自身维度（与旧 facets.ts 口径一致）。
import { computed } from 'vue'
import { THEMES } from '../../src/themes'
import {
  activeRunStatus,
  activeTags,
  activeTheme,
  clearFilters,
  examples,
  facetCounts,
  favOnly,
  minQuality,
  persistViewPrefs,
  tagFacets,
  toolboxItems
} from '../store'

const props = defineProps<{ scope: 'gallery' | 'toolbox' }>()

const RUN_STATUS_FACETS = [
  { key: 'all', label: '全部' },
  { key: 'ok', label: '成功过' },
  { key: 'failed', label: '失败过' },
  { key: 'never', label: '未运行' }
] as const
const QUALITY_FACETS = [
  { min: 0, label: '全部' },
  { min: 90, label: '90+' },
  { min: 80, label: '80+' },
  { min: 60, label: '60+' }
]

const CHIP_CLS =
  'facet-chip border rounded-full px-[9px] py-0.5 text-[11px] font-sans cursor-pointer transition-all duration-[120ms]'
const CHIP_IDLE = `${CHIP_CLS} border-line-subtle bg-transparent text-ink-dim hover:text-ink`
const CHIP_ACTIVE = `${CHIP_CLS} bg-accent border-accent text-white`
const GROUP_LABEL_CLS = 'facet-label shrink-0 text-[10.5px] text-ink-mute leading-5 w-[30px]'

const scopeList = computed(() => (props.scope === 'toolbox' ? toolboxItems.value : examples.value))

const baseQuery = computed(() => ({
  favOnly: favOnly.value,
  runStatus: activeRunStatus.value,
  tags: [],
  theme: 'all',
  minQuality: 0
}))

const tags = computed(() => (examples.value.length === 0 ? [] : tagFacets(scopeList.value, baseQuery.value)))

const hasExtraFilters = computed(() => {
  // 主题/质量分是画廊专属维度，不参与工具箱的「清除筛选」显示判定
  if (props.scope === 'gallery' && (activeTheme.value !== 'all' || minQuality.value > 0)) return true
  return activeRunStatus.value !== 'all' || activeTags.value.size > 0
})
</script>

<template>
  <template v-if="examples.length > 0">
    <!-- 运行状态 -->
    <div class="flex items-start gap-2">
      <span :class="GROUP_LABEL_CLS">运行</span>
      <div class="flex flex-wrap gap-1 flex-1">
        <button
          v-for="s in RUN_STATUS_FACETS"
          :key="s.key"
          :class="activeRunStatus === s.key ? CHIP_ACTIVE : CHIP_IDLE"
          @click="activeRunStatus = s.key"
        >
          {{ s.label }}
        </button>
      </div>
    </div>

    <!-- 主题 / 质量（画廊专属） -->
    <template v-if="scope === 'gallery'">
      <div class="flex items-start gap-2">
        <span :class="GROUP_LABEL_CLS">主题</span>
        <div class="flex flex-wrap gap-1 flex-1">
          <button :class="activeTheme === 'all' ? CHIP_ACTIVE : CHIP_IDLE" @click="activeTheme = 'all'; $persist?.()">
            全部主题
          </button>
          <button
            v-for="t in THEMES"
            :key="t.key"
            :class="activeTheme === t.key ? CHIP_ACTIVE : CHIP_IDLE"
            :title="t.placeholder"
            @click="activeTheme = t.key; $persist?.()"
          >
            {{ t.icon }} {{ t.label }} {{ facetCounts.themeCounts.get(t.key) || 0 }}
          </button>
        </div>
      </div>
      <div class="flex items-start gap-2">
        <span :class="GROUP_LABEL_CLS">质量</span>
        <div class="flex flex-wrap gap-1 flex-1">
          <button
            v-for="qf in QUALITY_FACETS"
            :key="qf.min"
            :class="minQuality === qf.min ? CHIP_ACTIVE : CHIP_IDLE"
            @click="minQuality = qf.min; $persist?.()"
          >
            {{ qf.min === 0 ? qf.label : `${qf.label} ${facetCounts.qualityCounts.get(qf.min) || 0}` }}
          </button>
        </div>
      </div>
    </template>

    <!-- 标签 -->
    <div v-if="tags.length > 0" class="flex items-start gap-2">
      <span :class="GROUP_LABEL_CLS">标签</span>
      <div class="flex flex-wrap gap-1 flex-1">
        <button
          v-for="f in tags"
          :key="f.tag"
          :class="activeTags.has(f.tag) ? CHIP_ACTIVE : CHIP_IDLE"
          @click="
            activeTags.has(f.tag) ? activeTags.delete(f.tag) : activeTags.add(f.tag)
          "
        >
          {{ f.tag }} {{ f.count }}
        </button>
      </div>
    </div>

    <!-- 清除筛选 -->
    <button
      v-if="hasExtraFilters"
      class="self-start border-0 bg-transparent text-ink-mute text-[11px] cursor-pointer py-0.5 underline hover:text-ink"
      @click="clearFilters()"
    >
      清除筛选
    </button>
  </template>
</template>
