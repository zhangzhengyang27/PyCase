<script setup lang="ts">
// ExampleListItem：浏览态列表视图的单行条目（画廊/工具箱共用）
// 一行一例：语义图标 chip + 名称 + 一行描述 + 圆点状态 + 低分提示；
// 收藏/运行操作 hover 浮现（占位不位移），行点击进详情，可键盘到达。
import { computed } from 'vue'
import { Play, Star } from 'lucide-vue-next'
import { exampleIcon } from '../src/icons'
import {
  qualityTextCls,
  runStatusDotCls,
  runStatusHint,
  runStatusLabel,
  runStatusTextCls,
  statusBadgeOf
} from '../src/utils'
import { sectionIcon } from '../src/section-icons'
import { sectionKeyOf } from '../src/overview'
import type { VExample } from '../src/store/catalog'

const props = defineProps<{ ex: VExample; faved?: boolean; enterIndex?: number }>()
const emit = defineEmits<{ open: []; fav: []; run: [] }>()

const title = computed(() => {
  const fallback = (props.ex.name || '').replace(/\.py$/i, '').replace(/[-_]/g, ' ')
  return (props.ex.title || fallback).replace(/\.py$/i, '')
})
// 图标与分区头同源（与 ExampleCard 一致）
const icon = computed(() => sectionIcon(sectionKeyOf(props.ex)) ?? exampleIcon(props.ex))
// 与 ExampleCard 同口径（utils.statusBadgeOf 同源收拢）：只显示负面状态，risky 由高危标记承担展示
const statusBadge = computed(() => statusBadgeOf(props.ex.run_status))
// 列表行的质量提示：仅低分（<80）显示，高分不打扰扫读
const lowQuality = computed(() => (props.ex.quality_score ?? 0) < 80)

// 入场 stagger：每屏前 8 项依次延迟 20ms，其后不延迟（specs §5）
const enterDelay = computed(() => ({
  animationDelay: `${props.enterIndex !== undefined && props.enterIndex < 8 ? props.enterIndex * 20 : 0}ms`
}))

const ICON_BTN =
  'w-6 h-6 flex items-center justify-center rounded-control cursor-pointer transition-colors dur-fast shrink-0 text-ink-mute hover:text-ink hover:bg-hover'
</script>

<template>
  <!-- .self 守卫：焦点在内嵌收藏/运行按钮上时按键只归按钮（原生激活），容器不再冒泡出 open -->
  <div
    class="group flex items-center gap-2.5 h-11 px-3 cursor-pointer transition-colors dur-fast border-b border-line-subtle hover:bg-hover animate-card-in [content-visibility:auto] [contain-intrinsic-size:auto_45px]"
    :style="enterDelay"
    role="button"
    tabindex="0"
    :aria-label="`${title}（详情）`"
    @click="emit('open')"
    @keydown.enter.self="emit('open')"
    @keydown.space.self.prevent="emit('open')"
  >
    <span class="chip-ic !w-6 !h-6">
      <component :is="icon" :size="13" :stroke-width="1.5" />
    </span>
    <span class="text-control font-medium text-ink truncate w-[190px] shrink-0 capitalize" :title="title">{{
      title
    }}</span>
    <span class="flex-1 min-w-0 text-caption text-ink-mute truncate" :title="ex.description || ''">
      {{ ex.description || '暂无描述' }}
    </span>
    <span
      v-if="ex.risk_high"
      class="inline-flex items-center gap-1 shrink-0 text-caption text-danger"
      title="含高危操作（系统命令/文件删除等），运行前请先审阅代码"
    >
      <span class="stat-dot bg-danger"></span>高危
    </span>
    <span
      v-else-if="statusBadge"
      class="inline-flex items-center gap-1 shrink-0 text-caption"
      :class="runStatusTextCls(statusBadge)"
      :title="runStatusHint(statusBadge)"
    >
      <span class="stat-dot" :class="runStatusDotCls(statusBadge)"></span>{{ runStatusLabel(statusBadge) }}
    </span>
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
      class="font-mono text-caption shrink-0"
      :class="qualityTextCls(ex.quality_score)"
      title="六维质量评分（0-100）"
      >{{ ex.quality_score ?? 0 }}</span
    >
    <div
      class="flex items-center gap-0.5 shrink-0 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity dur-fast"
    >
      <button
        :class="ICON_BTN"
        :title="faved ? '取消收藏' : '收藏'"
        :aria-label="faved ? `取消收藏 ${title}` : `收藏 ${title}`"
        @click.stop="emit('fav')"
      >
        <Star :size="12" :class="faved ? 'text-warn fill-current' : ''" />
      </button>
      <button :class="[ICON_BTN, 'text-accent']" title="运行" :aria-label="`运行 ${title}`" @click.stop="emit('run')">
        <Play :size="12" />
      </button>
    </div>
  </div>
</template>
