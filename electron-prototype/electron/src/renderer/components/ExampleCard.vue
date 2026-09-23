<script setup lang="ts">
// ExampleCard：示例卡片（对齐定稿样张的三行结构）
// 行 1 = 分区 emoji 徽章 + 标题 + ★ 收藏角标；行 2 = 描述（两行截断）；
// 行 3 = 质量分 + 主标签 + 负面状态徽章 + 运行 pill。
// 卡片可键盘到达（role=button + Enter 打开详情）。
import { computed } from 'vue'
import { Play, ShieldAlert, Star } from 'lucide-vue-next'
import { exampleIcon } from '../src/icons'
import { qualityBadgeCls, runStatusBadgeCls, runStatusHint, runStatusLabel } from '../src/utils'
import { CATEGORY_META } from '../src/category-meta'
import { exampleVisual } from '../src/overview'
import type { VExample } from '../store'

const props = defineProps<{ ex: VExample; selected?: boolean; faved?: boolean; enterIndex?: number }>()
const emit = defineEmits<{ open: []; fav: []; run: [] }>()

const title = computed(() => {
  const fallback = (props.ex.name || '').replace(/\.py$/i, '').replace(/[-_]/g, ' ')
  return (props.ex.title || fallback).replace(/\.py$/i, '')
})
const icon = computed(() => exampleIcon(props.ex))
const meta = computed(() => CATEGORY_META[props.ex.category] || CATEGORY_META.topics)
// 样张对齐：图标徽章优先用分区 emoji+色相（与画廊分区头一致），未命中回退分类
const visual = computed(() => exampleVisual(props.ex))
// 主标签：只展示第一个（样张卡片底部的依赖名位），避免整排截断标签的噪音
const firstTag = computed(() => (props.ex.tags || [])[0] || '')
// 可运行性徽章：只显示负面状态（缺依赖/空壳/语法损坏）；runnable 正向不占视觉，
// risky 由高危徽章承担展示，避免同一问题两个徽章重复
const statusBadge = computed(() =>
  props.ex.run_status && props.ex.run_status !== 'runnable' && props.ex.run_status !== 'risky'
    ? props.ex.run_status
    : ''
)

// content-visibility：触底加载后 DOM 只增不减（可能上千张卡），屏外卡片跳过布局/绘制；
// contain-intrinsic-size 的 auto 让渲染过的卡片记住真实高度，滚动条不跳动。
// 表面语言（边框/圆角/阴影/hover 抬升）由 .surface-card 全权负责（specs §3.1）
const CARD_CLS =
  'surface-card group cursor-pointer animate-card-in flex flex-col text-left w-full [content-visibility:auto] [contain-intrinsic-size:auto_150px]'
// 入场 stagger：每屏前 8 项依次延迟 20ms，其后不延迟（specs §5）
const enterDelay = computed(() => ({
  animationDelay: `${props.enterIndex !== undefined && props.enterIndex < 8 ? props.enterIndex * 20 : 0}ms`
}))
</script>

<template>
  <div
    :class="[CARD_CLS, selected ? 'border-accent shadow-[0_0_0_2px_rgba(94,106,210,0.3)]' : '']"
    :style="enterDelay"
    role="button"
    tabindex="0"
    :aria-label="`${title}（详情）`"
    @click="emit('open')"
    @keydown.enter="emit('open')"
    @keydown.space.prevent="emit('open')"
  >
    <!-- 行 1：徽章 + 标题 + 收藏角标 -->
    <div class="flex items-center gap-2.5 p-3.5 pb-0">
      <div
        class="hue-chip w-9 h-9 rounded-control flex items-center justify-center shrink-0"
        :style="{ '--hue': visual?.hue || meta.hue }"
      >
        <span v-if="visual" class="text-[15px] leading-none" aria-hidden="true">{{ visual.emoji }}</span>
        <component :is="icon" v-else :size="17" />
      </div>
      <span class="flex-1 min-w-0 text-body font-[590] text-ink leading-[1.3] truncate capitalize">{{ title }}</span>
      <button
        class="w-6 h-6 flex items-center justify-center rounded-control border-0 bg-transparent cursor-pointer shrink-0 transition-colors duration-150"
        :class="faved ? 'text-warn' : 'text-ink-faint/70 hover:text-warn'"
        :title="faved ? '取消收藏' : '收藏'"
        :aria-label="faved ? `取消收藏 ${title}` : `收藏 ${title}`"
        @click.stop="emit('fav')"
      >
        <Star :size="14" :class="faved ? 'fill-current' : ''" />
      </button>
    </div>
    <!-- 行 2：描述 -->
    <div class="flex-1 px-3.5 py-2.5">
      <p class="text-control text-ink-dim leading-[1.6] m-0 line-clamp-2">{{ ex.description || '暂无描述' }}</p>
    </div>
    <!-- 行 3：评分 + 主标签 + 负面徽章 + 运行 -->
    <div class="flex items-center gap-1.5 px-3.5 pb-3 min-w-0">
      <span
        class="inline-flex items-center px-1.5 h-5 rounded-full text-caption font-[510] font-mono shrink-0"
        :class="qualityBadgeCls(ex.quality_score)"
        title="六维质量评分（0-100）"
        >{{ ex.quality_score ?? 0 }}</span
      >
      <span v-if="firstTag" class="text-caption font-mono text-ink-mute truncate min-w-0" :title="firstTag">{{
        firstTag
      }}</span>
      <span
        v-if="ex.risk_high"
        class="inline-flex items-center gap-0.5 px-1.5 py-px rounded-badge text-badge font-[590] shrink-0 bg-danger-bg text-danger"
        title="含高危操作（系统命令/文件删除等），运行前请先审阅代码"
      >
        <ShieldAlert :size="10" /> 高危
      </span>
      <span
        v-if="statusBadge"
        class="inline-flex items-center px-1.5 py-px rounded-badge text-badge font-[590] shrink-0"
        :class="runStatusBadgeCls(statusBadge)"
        :title="runStatusHint(statusBadge)"
        >{{ runStatusLabel(statusBadge) }}</span
      >
      <span class="flex-1"></span>
      <button
        class="inline-flex items-center gap-1 h-5 px-1.5 rounded-control border border-accent/40 bg-accent/15 text-accent-strong text-badge font-[590] cursor-pointer transition-colors duration-150 shrink-0 hover:bg-accent/25 hover:text-ink"
        title="运行"
        :aria-label="`运行 ${title}`"
        @click.stop="emit('run')"
      >
        <Play :size="10" /> 运行
      </button>
    </div>
  </div>
</template>
