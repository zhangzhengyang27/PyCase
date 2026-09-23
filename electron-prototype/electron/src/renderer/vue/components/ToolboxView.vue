<script setup lang="ts">
// ToolboxView：工具箱（tools 分类子集，共用筛选引擎与卡片；无主题/质量维度）
import { ElMessage } from 'element-plus'
import {
  examples,
  favOnly,
  isFavorite,
  loadError,
  loading,
  toggleFavorite,
  toolSearchQuery,
  toolboxItems
} from '../store'
import ExampleCard from './ExampleCard.vue'
import FilterBar from './FilterBar.vue'

const emit = defineEmits<{ reload: [] }>()

const GRID_CLS = 'flex-1 overflow-y-auto p-4 grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-3 content-start'

function onRun(id: string): void {
  ElMessage.info('运行闭环将随详情页迁移（步骤 3）启用，当前请使用旧窗口运行')
}
</script>

<template>
  <section class="flex-1 min-w-0 min-h-0 flex flex-col bg-page overflow-hidden">
    <div class="flex flex-wrap items-center gap-2 px-4 py-2 bg-panel border-b border-line-subtle shrink-0">
      <div class="relative flex items-center">
        <span class="absolute left-2 text-[11px] text-ink-faint pointer-events-none z-[1]">🔍</span>
        <input
          v-model="toolSearchQuery"
          type="text"
          class="w-[220px] py-1.5 pl-7 pr-3 bg-page border border-line rounded-md text-ink text-[12px] font-sans font-normal outline-none transition-[border-color,box-shadow] duration-[120ms] placeholder:text-ink-faint hover:border-line-strong focus:border-accent focus:shadow-elev-focus"
          placeholder="搜索工具…"
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
      <FilterBar scope="toolbox" class="flex flex-wrap items-center gap-2 flex-1 min-w-[280px]" />
    </div>

    <div v-if="loading && examples.length === 0" class="flex-1 flex items-center justify-center">
      <div class="text-ink-faint text-[12px]">加载工具中…</div>
    </div>
    <div v-else-if="loadError" class="flex-1 flex flex-col items-center justify-center gap-3">
      <ElAlert type="error" :title="`加载失败: ${loadError}`" :closable="false" show-icon class="w-[420px]" />
      <ElButton size="small" @click="$emit('reload')">重试</ElButton>
    </div>
    <div v-else-if="toolboxItems.length === 0" class="flex-1 flex items-center justify-center">
      <ElEmpty description="没有匹配的工具" :image-size="80" />
    </div>

    <div v-else :class="GRID_CLS">
      <ExampleCard
        v-for="ex in toolboxItems"
        :key="ex.id"
        :ex="ex"
        :faved="isFavorite(ex.id)"
        @fav="toggleFavorite(ex.id)"
        @run="onRun(ex.id)"
      />
    </div>
  </section>
</template>
