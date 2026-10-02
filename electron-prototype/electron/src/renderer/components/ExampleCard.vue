<script setup lang="ts">
// ExampleCard：示例卡片（A1 视觉基线 v2 三行结构）
// 行 1 = 分区语义图标 chip + 标题 + ★ 收藏；行 2 = 描述（两行截断）；
// 行 3 = 质量分 + 主标签 + 高危 + 运行（安静按钮）+ 状态（圆点 + 中性文字）。
// interactive 形态（应用内交互工具）：行 3 的质量分与运行按钮退场，换成「交互」
// 徽章——交互工具没有可运行的 .py，运行/评分语义都不成立，卡片安静标记即可。
// 卡片可键盘到达（role=button + Enter 打开详情）。
import { computed } from 'vue'
import { MousePointerClick, Play, Star } from 'lucide-vue-next'
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

const props = defineProps<{
  ex: VExample
  selected?: boolean
  faved?: boolean
  enterIndex?: number
  /** 应用内交互工具形态：隐藏质量分/运行，显示交互徽章（默认 undefined = 普通卡片，零行为变化） */
  interactive?: boolean
}>()
const emit = defineEmits<{ open: []; fav: []; run: [] }>()

const title = computed(() => {
  const fallback = (props.ex.name || '').replace(/\.py$/i, '').replace(/[-_]/g, ' ')
  return (props.ex.title || fallback).replace(/\.py$/i, '')
})
// 图标与分区头同源：命中分区用分区图标，未命中回退分类/主题特征图标
const icon = computed(() => sectionIcon(sectionKeyOf(props.ex)) ?? exampleIcon(props.ex))
// 主标签：只展示第一个（样张卡片底部的依赖名位），避免整排截断标签的噪音
const firstTag = computed(() => (props.ex.tags || [])[0] || '')
// 可运行性状态徽章口径收拢到 utils.statusBadgeOf（与列表行/详情页同源）
const statusBadge = computed(() => statusBadgeOf(props.ex.run_status))

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
    :class="[CARD_CLS, selected ? 'card-sel' : '']"
    :style="enterDelay"
    role="button"
    tabindex="0"
    :aria-label="`${title}（详情）`"
    @click="emit('open')"
    @keydown.enter.self="emit('open')"
    @keydown.space.self.prevent="emit('open')"
  >
    <!-- .self 守卫：焦点在内嵌收藏/运行按钮上时按键只归按钮（原生激活），容器不再冒泡出 open。
         注释须留在 div 内：模板根若是「注释 + div」的 fragment，测试里 wrapper 根会落在注释节点上，
         click 直达容器（emit open）的断言路径就被架空了。 -->
    <!-- 行 1：语义图标 chip + 标题 + 收藏 -->
    <div class="flex items-center gap-2.5 px-3 pt-3 pb-0">
      <span class="chip-ic">
        <component :is="icon" :size="15" :stroke-width="1.5" />
      </span>
      <span class="flex-1 min-w-0 text-body font-semibold text-ink leading-[1.3] truncate capitalize">{{ title }}</span>
      <button
        class="w-6 h-6 flex items-center justify-center rounded-control border-0 bg-transparent cursor-pointer shrink-0 transition-colors dur-fast"
        :class="faved ? 'text-warn' : 'text-ink-faint hover:text-warn'"
        :title="faved ? '取消收藏' : '收藏'"
        :aria-label="faved ? `取消收藏 ${title}` : `收藏 ${title}`"
        @click.stop="emit('fav')"
      >
        <Star :size="14" :stroke-width="1.5" :class="faved ? 'fill-current' : ''" />
      </button>
    </div>
    <!-- 行 2：描述（两行截断） -->
    <div class="flex-1 px-3 py-2">
      <p class="text-caption text-ink-dim leading-[1.6] m-0 line-clamp-2">{{ ex.description || '暂无描述' }}</p>
    </div>
    <!-- 行 3：质量分 + 主标签 + 高危 + 运行 + 状态；interactive 形态下质量分/运行退场，换交互徽章 -->
    <div class="flex items-center gap-2 px-3 pb-2.5 min-w-0">
      <template v-if="!interactive">
        <span
          class="font-mono text-caption shrink-0"
          :class="qualityTextCls(ex.quality_score)"
          title="六维质量评分（0-100）"
        >
          {{ ex.quality_score ?? 0 }}
        </span>
      </template>
      <span v-if="firstTag" class="text-caption font-mono text-ink-mute truncate min-w-0" :title="firstTag">{{
        firstTag
      }}</span>
      <span class="flex-1"></span>
      <template v-if="!interactive">
        <button
          data-testid="card-run"
          class="inline-flex items-center gap-1 h-[var(--ctrl-sm)] px-1.5 rounded-control border-0 bg-transparent text-caption text-ink-dim cursor-pointer transition-colors dur-fast shrink-0 hover:bg-hover hover:text-ink"
          title="运行"
          :aria-label="`运行 ${title}`"
          @click.stop="emit('run')"
        >
          <Play :size="12" :stroke-width="1.5" /> 运行
        </button>
      </template>
      <span
        v-if="interactive"
        data-testid="interactive-badge"
        class="inline-flex items-center justify-center w-[var(--ctrl-sm)] h-[var(--ctrl-sm)] shrink-0 rounded-control border border-line-subtle text-ink-mute"
        title="交互工具：点击直接进入应用内页面"
        aria-label="交互工具"
      >
        <MousePointerClick :size="13" :stroke-width="1.5" />
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
    </div>
  </div>
</template>
