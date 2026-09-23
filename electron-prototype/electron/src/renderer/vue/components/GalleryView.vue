<script setup lang="ts">
// GalleryView：示例画廊（搜索 / 排序 / 收藏开关 / 筛选条 / 卡片流 + 加载更多）
// 视觉与交互从旧 index.html + gallery.ts 移植；分页逻辑保持旧版行为（limit 只增不减）。
import { ElMessage } from 'element-plus'
import {
  examples,
  favOnly,
  filtered,
  galleryLimit,
  isFavorite,
  loadError,
  loading,
  searchQuery,
  shownGallery,
  sortBy,
  toggleFavorite
} from '../store'
import ExampleCard from './ExampleCard.vue'
import FilterBar from './FilterBar.vue'

const emit = defineEmits<{ reload: [] }>()

const PAGE_SIZE = 120
const GRID_CLS = 'flex-1 overflow-y-auto p-4 grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-3 content-start'

function onRun(id: string): void {
  // 运行闭环依赖详情页（步骤 3 迁移），当前窗口为画廊预览
  ElMessage.info('运行闭环将随详情页迁移（步骤 3）启用，当前请使用旧窗口运行')
}

// 注意：script setup 的 inline 模板编译下，模板内不能对导入的 ref 直接赋值
// （ESM 只读绑定），所有状态变更必须收敛为 setup 作用域内的函数
function toggleFavOnly(): void {
  favOnly.value = !favOnly.value
}
</script>

<template>
  <section class="flex-1 min-w-0 min-h-0 flex flex-col bg-page overflow-hidden">
    <!-- 工具栏：搜索 + 收藏开关 + 排序 -->
    <div class="flex flex-wrap items-center gap-2 px-4 py-2 bg-panel border-b border-line-subtle shrink-0">
      <div class="relative flex items-center">
        <span class="absolute left-2 text-[11px] text-ink-faint pointer-events-none z-[1]">🔍</span>
        <input
          v-model="searchQuery"
          type="text"
          class="w-[220px] py-1.5 pl-7 pr-3 bg-page border border-line rounded-md text-ink text-[12px] font-sans font-normal outline-none transition-[border-color,box-shadow] duration-[120ms] placeholder:text-ink-faint hover:border-line-strong focus:border-accent focus:shadow-elev-focus"
          placeholder="搜索名称 / 标签 / 代码…"
        />
      </div>
      <button
        class="inline-flex items-center gap-1 border rounded-full px-[9px] py-0.5 text-[11px] font-sans cursor-pointer transition-all duration-[120ms]"
        :class="favOnly ? 'bg-accent border-accent text-white' : 'border-line-subtle bg-transparent text-ink-dim hover:text-ink'"
        title="只看收藏"
        @click="favOnly = !favOnly"
      >
        ⭐ 收藏{{ favorites.size ? ` ${favorites.size}` : '' }}
      </button>
      <select
        v-model="sortBy"
        class="py-1.5 px-2 bg-page border border-line rounded-md text-ink text-[11px] font-sans outline-none cursor-pointer hover:border-line-strong focus:border-accent"
        title="排序"
      >
        <option value="quality_desc">质量分优先</option>
        <option value="name">按名称</option>
        <option value="last_run">最近运行</option>
      </select>
      <FilterBar scope="gallery" class="flex flex-wrap items-center gap-2 flex-1 min-w-[280px]" />
    </div>

    <!-- 状态：加载 / 错误 / 空态 -->
    <div v-if="loading && examples.length === 0" class="flex-1 flex items-center justify-center">
      <div class="text-ink-faint text-[12px]">加载示例中…（首次加载需物化所有示例，可能较慢）</div>
    </div>
    <div v-else-if="loadError" class="flex-1 flex flex-col items-center justify-center gap-3">
      <ElAlert type="error" :title="`加载失败: ${loadError}`" :closable="false" show-icon class="w-[420px]" />
      <ElButton size="small" @click="$emit('reload')">重试</ElButton>
    </div>
    <div v-else-if="filtered.length === 0" class="flex-1 flex items-center justify-center">
      <ElEmpty description="没有匹配的示例" :image-size="80" />
    </div>

    <!-- 卡片流 -->
    <div v-else :class="GRID_CLS">
      <ExampleCard
        v-for="ex in shownGallery"
        :key="ex.id"
        :ex="ex"
        :faved="isFavorite(ex.id)"
        @fav="toggleFavorite(ex.id)"
        @run="onRun(ex.id)"
      />
      <button
        v-if="filtered.length > shownGallery.length"
        class="col-span-full py-3 text-[12px] text-ink-mute border border-line-subtle rounded-lg bg-panel cursor-pointer hover:text-ink hover:border-line-strong transition-colors"
        @click="galleryLimit += PAGE_SIZE"
      >
        加载更多（还有 {{ filtered.length - shownGallery.length }} 个）
      </button>
    </div>
  </section>
</template>
