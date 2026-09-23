<script setup lang="ts">
// ExampleListItem：浏览态列表视图的单行条目（画廊/工具箱共用）
// 一行一例：小色块图标 + 名称 + 一行描述 + 负面徽章 + 低分质量提示；
// 收藏/运行操作 hover 浮现（占位不位移），行点击进详情，可键盘到达。
import { computed } from 'vue'
import { Play, ShieldAlert, Star } from 'lucide-vue-next'
import { exampleIcon } from '../src/icons'
import { qualityBadgeCls, runStatusBadgeCls, runStatusHint, runStatusLabel } from '../src/utils'
import { CATEGORY_META } from '../src/category-meta'
import { exampleVisual } from '../src/overview'
import type { VExample } from '../store'

const props = defineProps<{ ex: VExample; faved?: boolean; enterIndex?: number }>()
const emit = defineEmits<{ open: []; fav: []; run: [] }>()

const title = computed(() => {
  const fallback = (props.ex.name || '').replace(/\.py$/i, '').replace(/[-_]/g, ' ')
  return (props.ex.title || fallback).replace(/\.py$/i, '')
})
const icon = computed(() => exampleIcon(props.ex))
const meta = computed(() => CATEGORY_META[props.ex.category] || CATEGORY_META.topics)
const visual = computed(() => exampleVisual(props.ex))
// 与 ExampleCard 同口径：只显示负面可运行性状态；risky 由高危徽章承担展示
const statusBadge = computed(() =>
  props.ex.run_status && props.ex.run_status !== 'runnable' && props.ex.run_status !== 'risky'
    ? props.ex.run_status
    : ''
)
// 列表行的质量提示：仅低分（<80）显示，高分不打扰扫读
const lowQuality = computed(() => (props.ex.quality_score ?? 0) < 80)

// 入场 stagger：每屏前 8 项依次延迟 20ms，其后不延迟（specs §5）
const enterDelay = computed(() => ({
  animationDelay: `${props.enterIndex !== undefined && props.enterIndex < 8 ? props.enterIndex * 20 : 0}ms`
}))

const ICON_BTN =
  'w-6 h-6 flex items-center justify-center rounded-control cursor-pointer transition-colors duration-150 shrink-0 text-ink-mute hover:text-ink hover:bg-surface'
const BADGE_CLS = 'inline-flex items-center gap-0.5 px-1.5 py-px rounded-badge text-badge font-[590] shrink-0'
</script>

<template>
  <div
    class="group flex items-center gap-2.5 h-11 px-3 bg-panel cursor-pointer transition-colors duration-150 border-b border-line-subtle/50 hover:bg-hover animate-card-in [content-visibility:auto] [contain-intrinsic-size:auto_45px]"
    :style="enterDelay"
    role="button"
    tabindex="0"
    :aria-label="`${title}（详情）`"
    @click="emit('open')"
    @keydown.enter="emit('open')"
    @keydown.space.prevent="emit('open')"
  >
    <div class="hue-chip w-6 h-6 rounded-control flex items-center justify-center shrink-0" :style="{ '--hue': visual?.hue || meta.hue }">
      <span v-if="visual" class="text-[11px] leading-none" aria-hidden="true">{{ visual.emoji }}</span>
      <component :is="icon" v-else :size="13" />
    </div>
    <span class="text-control font-[590] text-ink truncate w-[190px] shrink-0 capitalize" :title="title">{{ title }}</span>
    <span class="flex-1 min-w-0 text-caption text-ink-faint truncate" :title="ex.description || ''">
      {{ ex.description || '暂无描述' }}
    </span>
    <span
      v-if="ex.risk_high"
      :class="BADGE_CLS"
      class="bg-danger-bg text-danger"
      title="含高危操作（系统命令/文件删除等），运行前请先审阅代码"
    >
      <ShieldAlert :size="10" /> 高危
    </span>
    <span
      v-if="statusBadge"
      :class="[BADGE_CLS, runStatusBadgeCls(statusBadge)]"
      :title="runStatusHint(statusBadge)"
      >{{ runStatusLabel(statusBadge) }}</span
    >
    <span class="hidden lg:flex items-center gap-2 min-w-0 shrink-0">
      <span
        v-for="tag in (ex.tags || []).slice(0, 2)"
        :key="tag"
        class="text-caption font-mono text-ink-mute max-w-[110px] truncate"
        >{{ tag }}</span
      >
    </span>
    <span
      v-if="lowQuality"
      class="inline-flex items-center px-1.5 h-5 rounded-badge text-caption font-mono shrink-0"
      :class="qualityBadgeCls(ex.quality_score)"
      title="六维质量评分（0-100）"
      >{{ ex.quality_score ?? 0 }}</span
    >
    <div class="flex items-center gap-0.5 shrink-0 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity duration-150">
      <button
        :class="ICON_BTN"
        :title="faved ? '取消收藏' : '收藏'"
        :aria-label="faved ? `取消收藏 ${title}` : `收藏 ${title}`"
        @click.stop="emit('fav')"
      >
        <Star :size="12" :class="faved ? 'text-warn fill-current' : ''" />
      </button>
      <button
        :class="[ICON_BTN, 'text-accent']"
        title="运行"
        :aria-label="`运行 ${title}`"
        @click.stop="emit('run')"
      >
        <Play :size="12" />
      </button>
    </div>
  </div>
</template>
