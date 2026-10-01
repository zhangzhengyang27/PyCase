<script setup lang="ts">
// GalleryView：画廊单态视图（原「总览 ↔ 下钻」双态退役，统一为浏览态）
// 结构：页头（GalleryHeader，常驻定位条）→ 结果条（BrowseToolbar，筛选维度收成工具栏下拉）
//       → 网格/清单（响应式 auto-fill）。
// 上一版的并排筛选栏与 <1100px 浮层已退役——筛选改由工具栏下拉承担（见 BrowseToolbar）。
// 状态齐备：加载（骨架）/ 错误（横幅 + 重试）/ 库空 / 筛选无结果 / 有内容。
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { SearchX } from 'lucide-vue-next'
import { examples, filtered, galleryLimit, loadError, loading, shownGallery, viewMode } from '../src/store/catalog'
import { openDetail, runFromCard } from '../src/store/detail'
import { isFavorite, toggleFavorite } from '../src/store/prefs'
import ExampleCard from './ExampleCard.vue'
import ExampleListItem from './ExampleListItem.vue'
import BrowseToolbar from './BrowseToolbar.vue'
import GalleryHeader from './GalleryHeader.vue'
import SkeletonCard from './base/SkeletonCard.vue'
import AppEmpty from './base/AppEmpty.vue'
import AlertBanner from './base/AlertBanner.vue'
import BaseButton from './base/BaseButton.vue'

const emit = defineEmits<{ reload: [] }>()

// minmax 由 300px 降到 260px：窄窗下也能落下一列，避免 auto-fill 找不到列而横向溢出
const GRID_CLS =
  'flex-1 overflow-y-auto min-h-0 p-4 grid grid-cols-[repeat(auto-fill,minmax(260px,1fr))] gap-4 content-start'
const LIST_CLS = 'flex-1 overflow-y-auto min-h-0'

function onRun(id: string): void {
  void runFromCard(id)
}

// 触底无限加载（网格/清单共用一个哨兵；清单行更轻，单步扩更多）
const sentinelEl = ref<HTMLElement | null>(null)
let io: IntersectionObserver | null = null

watch(sentinelEl, (el) => {
  if (el) io?.observe(el)
})

onMounted(() => {
  io = new IntersectionObserver(
    (entries) => {
      if (entries.some((e) => e.isIntersecting) && filtered.value.length > shownGallery.value.length) {
        galleryLimit.value += viewMode.value === 'list' ? 160 : 120
      }
    },
    { rootMargin: '320px' }
  )
  if (sentinelEl.value) io.observe(sentinelEl.value)
})
onBeforeUnmount(() => io?.disconnect())
</script>

<template>
  <section class="flex-1 min-w-0 min-h-0 flex flex-col bg-page overflow-hidden">
    <!-- 页头：全宽定位条（统计 chip + 浏览全部 / 我的收藏），与旧总览页头同位置外观 -->
    <GalleryHeader />

    <!-- 结果条：筛选维度收成工具栏下拉（工具栏常驻，空态下仍是清筛选的入口） -->
    <BrowseToolbar />

    <!-- 状态：加载 / 错误 / 库空 / 筛选无结果 -->
    <div v-if="loading && examples.length === 0" :class="GRID_CLS">
      <SkeletonCard v-for="i in 8" :key="i" />
    </div>
    <div v-else-if="loadError" class="flex-1 flex flex-col items-center justify-center gap-3">
      <AlertBanner :title="`加载失败: ${loadError}`" class="w-[420px]" />
      <BaseButton variant="primary" @click="emit('reload')">重试</BaseButton>
    </div>
    <AppEmpty
      v-else-if="examples.length === 0"
      :icon="SearchX"
      title="示例库为空"
      description="检查 sidecar 与内置示例集合后重试"
    />
    <div v-else-if="filtered.length === 0" class="flex-1 flex items-center justify-center">
      <AppEmpty :icon="SearchX" title="没有匹配的示例" description="调整筛选条件或搜索词试试" />
    </div>

    <!-- 内容流：网格 / 清单 -->
    <div v-else :class="viewMode === 'list' ? LIST_CLS : GRID_CLS">
      <template v-if="viewMode === 'grid'">
        <ExampleCard
          v-for="(ex, i) in shownGallery"
          :key="ex.id"
          :ex="ex"
          :enter-index="i"
          :faved="isFavorite(ex.id)"
          @open="openDetail(ex.id)"
          @fav="toggleFavorite(ex.id)"
          @run="onRun(ex.id)"
        />
      </template>
      <template v-else>
        <ExampleListItem
          v-for="(ex, i) in shownGallery"
          :key="ex.id"
          :ex="ex"
          :enter-index="i"
          :faved="isFavorite(ex.id)"
          @open="openDetail(ex.id)"
          @fav="toggleFavorite(ex.id)"
          @run="onRun(ex.id)"
        />
      </template>
      <div ref="sentinelEl" class="col-span-full h-4" aria-hidden="true"></div>
    </div>
  </section>
</template>
