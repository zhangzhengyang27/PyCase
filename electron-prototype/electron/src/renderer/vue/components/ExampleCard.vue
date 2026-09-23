<script setup lang="ts">
// ExampleCard：示例卡片（视觉从旧 gallery.ts cardHtml 1:1 移植为声明式模板）
// innerHTML 拼接 + escapeHtml 被 Vue 模板自动转义取代，XSS 加固面自然消失。
import { computed } from 'vue'
import { getToolIcon, qualityBadgeCls } from '../../src/utils'
import { CATEGORY_META } from '../../src/category-meta'
import type { VExample } from '../store'

const props = defineProps<{ ex: VExample; selected?: boolean; faved?: boolean }>()
const emit = defineEmits<{ open: []; fav: []; run: [] }>()

const title = computed(() => props.ex.title || (props.ex.name || '').replace(/\.py$/i, '').replace(/[-_]/g, ' '))
const icon = computed(() => (props.ex.category === 'tools' ? getToolIcon(props.ex.name) : '🐍'))

const CARD_CLS =
  'card group bg-panel border rounded-xl cursor-pointer transition-all duration-200 flex flex-col hover:border-line-strong hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)]'
const CARD_SELECTED_CLS =
  'card group bg-panel border border-accent rounded-xl cursor-pointer transition-all duration-200 flex flex-col shadow-[0_0_0_2px_rgba(94,106,210,0.3)] hover:border-line-strong'
const CARD_BTN_CLS =
  'card-btn flex-1 flex items-center justify-center gap-1.5 px-3 py-2 border border-line-subtle rounded-md text-[12px] font-[510] cursor-pointer transition-all duration-150 bg-panel text-ink-dim hover:border-line-strong hover:text-ink hover:bg-card'
const CARD_BTN_FAV_CLS =
  'card-btn flex-none basis-[34px] flex items-center justify-center gap-1.5 px-3 py-2 border rounded-md text-[12px] font-[510] cursor-pointer transition-all duration-150 bg-panel hover:border-line-strong hover:text-ink hover:bg-card'
</script>

<template>
  <div :class="selected ? CARD_SELECTED_CLS : CARD_CLS" @click="emit('open')">
    <div class="card-header flex items-center gap-3 p-4 border-b border-line-subtle">
      <div
        class="card-icon w-10 h-10 rounded-[10px] flex items-center justify-center text-[20px] shrink-0 bg-card border border-line-subtle"
      >
        {{ icon }}
      </div>
      <div class="card-info flex-1 min-w-0 flex flex-col gap-1">
        <div class="flex items-center gap-2 min-w-0">
          <span class="card-title text-[14px] font-[590] text-ink leading-[1.3] truncate capitalize">{{ title }}</span>
          <span
            class="card-category inline-flex items-center px-1.5 py-px rounded-sm text-[9px] font-[590] uppercase tracking-[0.03em] shrink-0"
            :class="(CATEGORY_META[ex.category] || {}).cls || ''"
            >{{ ex.category }}</span
          >
        </div>
        <div class="card-meta flex items-center gap-1.5">
          <span
            v-for="tag in (ex.tags || []).slice(0, 2)"
            :key="tag"
            class="card-tag inline-block text-[10px] px-2 py-0.5 bg-card rounded text-ink-dim font-mono font-[510]"
            >{{ tag }}</span
          >
        </div>
      </div>
      <span
        class="card-quality inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full text-[11px] font-[510] font-mono shrink-0"
        :class="qualityBadgeCls(ex.quality_score)"
        title="六维质量评分（0-100）"
        >★ {{ ex.quality_score ?? 0 }}</span
      >
    </div>
    <div class="card-body flex-1 px-4 py-3">
      <p class="card-description text-[12px] text-ink-dim leading-[1.6] m-0 line-clamp-3">
        {{ ex.description || '暂无描述' }}
      </p>
    </div>
    <div
      class="card-actions flex gap-2 px-4 pt-3 pb-4 opacity-0 translate-y-1 transition-all duration-200 group-hover:opacity-100 group-hover:translate-y-0"
    >
      <button
        :class="`${CARD_BTN_FAV_CLS} ${faved ? ' text-[#e3a008] border-[#e3a008]' : ' border-line-subtle text-ink-mute'}`"
        :title="faved ? '取消收藏' : '收藏'"
        @click.stop="emit('fav')"
      >
        {{ faved ? '★' : '☆' }}
      </button>
      <button
        :class="`${CARD_BTN_CLS} bg-accent text-white border-accent font-[590] enabled:hover:bg-accent-hover enabled:hover:border-accent-hover`"
        title="运行（详情页迁移后可用）"
        @click.stop="emit('run')"
      >
        ▶ 运行
      </button>
      <button :class="CARD_BTN_CLS" @click.stop="emit('open')">详情</button>
    </div>
  </div>
</template>
