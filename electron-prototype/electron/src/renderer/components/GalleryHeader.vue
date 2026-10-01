<script setup lang="ts">
// GalleryHeader：画廊页头（原总览落地页头区，随落地页退役抽为独立组件）
// 一句话回答「这个库里有什么」：统计 chip（示例数 / 主题数 / 可运行率 / 收藏数）+ 两个入口按钮。
// 落地页的横向卡片带已退役，页头位置与外观保持不变——它是浏览态常驻的定位条。
import { computed } from 'vue'
import { THEMES } from '../src/themes'
import { facetCounts, galleryExamples, openGallery } from '../src/store/catalog'
import { favorites } from '../src/store/prefs'
import BaseButton from './base/BaseButton.vue'

const runnablePct = computed(() => {
  const total = galleryExamples.value.length
  if (!total) return 0
  return Math.round(((facetCounts.value.runnableCounts.get('runnable') || 0) / total) * 100)
})
</script>

<template>
  <!-- 页头固定、独立于滚动层：app-drag 在滚动容器内不生效（Electron 限制），顺带让标题常驻 -->
  <div class="app-drag select-none px-8 pt-7 pb-3 shrink-0">
    <div class="max-w-[1200px] mx-auto flex items-end justify-between gap-4">
      <div>
        <h1 class="text-page font-semibold text-ink m-0 tracking-[-0.02em]">示例库</h1>
        <div class="flex items-center gap-1.5 mt-2.5 app-no-drag">
          <span class="stat-chip"
            ><b class="font-mono">{{ galleryExamples.length }}</b> 个示例</span
          >
          <span class="stat-chip"
            ><b class="font-mono">{{ THEMES.length }}</b> 大主题</span
          >
          <span class="stat-chip stat-chip-ok"
            ><b class="font-mono">{{ runnablePct }}%</b> 可运行</span
          >
          <span class="stat-chip"
            ><b class="font-mono">{{ favorites.size }}</b> 收藏</span
          >
        </div>
      </div>
      <div class="app-no-drag flex items-center gap-2 shrink-0">
        <BaseButton @click="openGallery()">浏览全部</BaseButton>
        <BaseButton variant="primary" @click="openGallery({ favOnly: true })">我的收藏</BaseButton>
      </div>
    </div>
  </div>
</template>
