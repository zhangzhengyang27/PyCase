<script setup lang="ts">
// GalleryView：画廊两级浏览——总览分区落地页（默认）↔ 下钻浏览态
// 浏览态保留旧行为：FilterSidebar + 触底无限加载（galleryLimit 只增不减）；
// 新增清单密度（viewMode）与筛选芯片结果条（BrowseToolbar）。
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { SearchX } from 'lucide-vue-next'
import { examples, filtered, galleryLimit, galleryMode, loadError, loading, shownGallery, viewMode } from '../src/store/catalog'
import { openDetail, runFromCard } from '../src/store/detail'
import { isFavorite, toggleFavorite } from '../src/store/prefs'
import ExampleCard from './ExampleCard.vue'
import ExampleListItem from './ExampleListItem.vue'
import BrowseToolbar from './BrowseToolbar.vue'
import GalleryOverview from './GalleryOverview.vue'
import FilterSidebar from './FilterSidebar.vue'
import SkeletonCard from './base/SkeletonCard.vue'
import AppEmpty from './base/AppEmpty.vue'
import AlertBanner from './base/AlertBanner.vue'
import BaseButton from './base/BaseButton.vue'

const emit = defineEmits<{ reload: [] }>()

const GRID_CLS = 'flex-1 overflow-y-auto min-h-0 p-4 grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-4 content-start'
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
  <section class="flex-1 min-w-0 min-h-0 flex bg-page overflow-hidden">
    <!-- 总览态：全宽分区落地页（侧栏仅在下钻浏览态出现） -->
    <div v-show="galleryMode === 'overview'" class="flex-1 min-w-0 flex flex-col min-h-0 animate-view-in">
      <div
        v-if="loading && examples.length === 0"
        class="flex-1 min-h-0 p-8 grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-4 content-start"
      >
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
      <GalleryOverview v-else />
    </div>

    <!-- 浏览态：侧栏 + 结果条 + 网格/清单 -->
    <div v-show="galleryMode === 'browse'" class="flex-1 min-w-0 flex min-h-0 animate-view-in">
      <FilterSidebar scope="gallery" />

      <div class="flex-1 min-w-0 flex flex-col min-h-0">
        <BrowseToolbar />

        <!-- 状态：加载 / 错误 / 空态 -->
        <div v-if="loading && examples.length === 0" :class="GRID_CLS">
          <SkeletonCard v-for="i in 8" :key="i" />
        </div>
        <div v-else-if="loadError" class="flex-1 flex flex-col items-center justify-center gap-3">
          <AlertBanner :title="`加载失败: ${loadError}`" class="w-[420px]" />
          <BaseButton variant="primary" @click="emit('reload')">重试</BaseButton>
        </div>
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
      </div>
    </div>
  </section>
</template>
