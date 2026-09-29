<script setup lang="ts">
// GalleryOverview：画廊总览态（默认落地页）
// 头区一句话回答「这个库里有什么」；主体按主题分区横向带——先看结构，再下钻看条目。
// 分区成员来自 assignSections（互斥分配 + 质量降序预览），计数与成员同口径。
import { computed } from 'vue'
import { ArrowRight } from 'lucide-vue-next'
import { assignSections, type OverviewSection } from '../src/overview'
import { sectionIcon } from '../src/section-icons'
import { THEMES } from '../src/themes'
import { facetCounts, galleryExamples, openGalleryBrowse } from '../src/store/catalog'
import { openDetail, runFromCard } from '../src/store/detail'
import { favorites, isFavorite, toggleFavorite } from '../src/store/prefs'
import ExampleCard from './ExampleCard.vue'
import BaseButton from './base/BaseButton.vue'

const PREVIEW_COUNT = 6

const sections = computed(() => assignSections(galleryExamples.value))
const runnablePct = computed(() => {
  const total = galleryExamples.value.length
  if (!total) return 0
  return Math.round(((facetCounts.value.runnableCounts.get('runnable') || 0) / total) * 100)
})

function moreCount(sec: OverviewSection): number {
  return sec.items.length - PREVIEW_COUNT
}

/** 分区下钻：按 kind 预置对应范围（主题 / 分区标签组 / 项目类目 / 全部） */
function browseSection(sec: OverviewSection): void {
  if (sec.kind === 'tags') openGalleryBrowse({ tags: sec.tags })
  else if (sec.kind === 'projects') openGalleryBrowse({ category: 'projects' })
  else openGalleryBrowse({ theme: sec.kind === 'theme' ? sec.key : 'all' })
}

function onRun(id: string): void {
  void runFromCard(id)
}
</script>

<template>
  <!-- 页头固定、独立于滚动层：app-drag 在滚动容器内不生效（Electron 限制），
       顺带让标题常驻——分区滚动时页头不消失 -->
  <div class="flex-1 min-h-0 flex flex-col">
    <div class="app-drag select-none px-8 pt-7 pb-3">
      <div class="max-w-[1200px] mx-auto flex items-end justify-between gap-4">
        <div>
          <h1 class="text-page font-semibold text-ink m-0 tracking-[-0.02em]">示例库</h1>
          <div class="flex items-center gap-1.5 mt-2.5 app-no-drag">
            <span class="stat-chip"><b class="font-mono">{{ galleryExamples.length }}</b> 个示例</span>
            <span class="stat-chip"><b class="font-mono">{{ THEMES.length }}</b> 大主题</span>
            <span class="stat-chip stat-chip-ok"><b class="font-mono">{{ runnablePct }}%</b> 可运行</span>
            <span class="stat-chip"><b class="font-mono">{{ favorites.size }}</b> 收藏</span>
          </div>
        </div>
        <div class="app-no-drag flex items-center gap-2 shrink-0">
          <BaseButton @click="openGalleryBrowse({ theme: 'all' })">浏览全部</BaseButton>
          <BaseButton variant="primary" @click="openGalleryBrowse({ favOnly: true })">我的收藏</BaseButton>
        </div>
      </div>
    </div>

    <!-- 分区横向带（滚动层） -->
    <div class="flex-1 min-h-0 overflow-y-auto">
      <div class="max-w-[1200px] mx-auto px-8 pb-12">
        <section v-for="sec in sections" :key="sec.key" class="mb-9">
          <div class="flex items-center gap-2 mb-3">
            <span class="chip-ic !w-[22px] !h-[22px]" aria-hidden="true">
              <component :is="sectionIcon(sec.key)" :size="13" :stroke-width="1.5" />
            </span>
            <h2 class="text-title font-semibold text-ink m-0">{{ sec.label }}</h2>
            <span class="text-caption text-ink-mute">{{ sec.items.length }} 个</span>
            <button
              class="ml-auto flex items-center gap-1 border-0 bg-transparent text-control text-ink-mute hover:text-accent cursor-pointer transition-colors dur-fast"
              @click="browseSection(sec)"
            >
              查看全部 <ArrowRight :size="13" />
            </button>
          </div>
          <div class="flex gap-3 overflow-x-auto pb-1 [scrollbar-width:none]">
            <div v-for="(ex, i) in sec.items.slice(0, PREVIEW_COUNT)" :key="ex.id" class="w-[300px] shrink-0 flex">
              <ExampleCard
                :ex="ex"
                :enter-index="i"
                :faved="isFavorite(ex.id)"
                @open="openDetail(ex.id)"
                @fav="toggleFavorite(ex.id)"
                @run="onRun(ex.id)"
              />
            </div>
            <button
              v-if="sec.items.length > PREVIEW_COUNT"
              class="w-[300px] shrink-0 self-stretch min-h-[110px] rounded-panel border border-dashed border-line-strong bg-transparent flex items-center justify-center gap-1 text-control text-ink-mute hover:text-ink hover:border-accent/60 cursor-pointer transition-colors dur-fast"
              :title="`浏览${sec.label}全部示例`"
              @click="browseSection(sec)"
            >
              还有 {{ moreCount(sec) }} 个 <ArrowRight :size="13" />
            </button>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>
