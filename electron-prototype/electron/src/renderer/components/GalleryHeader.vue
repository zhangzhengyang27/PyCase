<script setup lang="ts">
// GalleryHeader：画廊页头（原总览落地页头区，随落地页退役抽为独立组件）
// 一句话回答「这里是什么」：标题 + 统计 chip + 两个入口按钮。
// 页头跟随侧栏二级分区（用户语义：选了分区，右侧就是分区的示例）——
// 无分区时讲全局（示例库 / 1330 / N 大主题），有分区时标题即分区名、
// 统计收窄到分区内（主题 chip 退场：分区本身就是分组）。
// 分区池取 gallerySections（与侧栏二级菜单计数严格同源）。
import { computed } from 'vue'
import { THEMES } from '../src/themes'
import { sectionLabelOf } from '../src/overview'
import { activeSectionKey, galleryExamples, galleryPool, gallerySections, openGallery } from '../src/store/catalog'
import { favorites } from '../src/store/prefs'
import BaseButton from './base/BaseButton.vue'

// 当前语境的样本池：无分区 = 全库；有分区 = 该分区的成员（与侧栏计数同源）
const pool = computed(() => {
  if (!activeSectionKey.value) return galleryPool.value
  return gallerySections.value.find((s) => s.key === activeSectionKey.value)?.items ?? []
})

// 归并口径下补一句「多少变体收进了多少张卡」（仅全局语境展示）
const mergedNote = computed(() => {
  if (activeSectionKey.value) return null
  const merged = galleryExamples.value.length - pool.value.length
  return merged > 0 ? merged : null
})

const title = computed(() => (activeSectionKey.value ? sectionLabelOf(activeSectionKey.value) : '示例库') ?? '示例库')

const runnablePct = computed(() => {
  const total = pool.value.length
  if (!total) return 0
  const runnable = pool.value.filter((e) => e.run_status === 'runnable').length
  return Math.round((runnable / total) * 100)
})

// 全局语境才讲「N 大主题」；分区语境主题 chip 退场（分区即分组）
const scoped = computed(() => activeSectionKey.value !== null)

const favCount = computed(() => pool.value.filter((e) => favorites.value.has(e.id)).length)
</script>

<template>
  <!-- 页头固定、独立于滚动层：app-drag 在滚动容器内不生效（Electron 限制），顺带让标题常驻 -->
  <div class="app-drag select-none px-8 pt-7 pb-3 shrink-0">
    <div class="max-w-[1200px] mx-auto flex items-end justify-between gap-4">
      <div>
        <h1 class="text-[length:--text-page] font-semibold text-ink m-0 tracking-[-0.02em]">{{ title }}</h1>
        <div class="flex items-center gap-1.5 mt-2.5 app-no-drag">
          <span class="stat-chip"
            ><b class="font-mono">{{ pool.length }}</b> 个示例</span
          >
          <span v-if="mergedNote" class="stat-chip" title="同族变体已归并进实验室页，可在浏览工具栏关闭归并">
            已归并 <b class="font-mono">{{ mergedNote }}</b> 个变体</span
          >
          <span v-if="!scoped" class="stat-chip"
            ><b class="font-mono">{{ THEMES.length }}</b> 大主题</span
          >
          <span class="stat-chip stat-chip-ok"
            ><b class="font-mono">{{ runnablePct }}%</b> 可运行</span
          >
          <span class="stat-chip"
            ><b class="font-mono">{{ favCount }}</b> 收藏</span
          >
        </div>
      </div>
      <div class="app-no-drag flex items-center gap-2 shrink-0">
        <!-- 浏览全部只在分区语境出现（退出分区入口）；全局态再放「浏览全部」是死按钮 -->
        <BaseButton v-if="scoped" @click="openGallery()">浏览全部</BaseButton>
        <BaseButton variant="primary" @click="openGallery({ favOnly: true })">我的收藏</BaseButton>
      </div>
    </div>
  </div>
</template>
