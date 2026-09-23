<script setup lang="ts">
// App：Vue 渲染层应用壳（迁移第 2 步：画廊 + 工具箱）
// 顶栏/状态栏视觉对齐旧窗口；视图组件经 store 的 computed 派生数据驱动，
// 无 applyAllFilters 式手动刷新。运行器与详情页按迁移计划在后续步骤落入。
import { computed, onMounted, ref } from 'vue'
import { api } from '../src/sidecar-client'
import { statusDotCls } from '../src/utils'
import { activeView, examples, filtered, loadAll, loading, toolboxItems, toolsTotal, type ViewKey } from './store'
import GalleryView from './components/GalleryView.vue'
import ToolboxView from './components/ToolboxView.vue'

const sidecarReady = ref<'checking' | 'ready' | 'error'>('checking')
const theme = ref(document.documentElement.getAttribute('data-theme') || 'dark')

const statusDot = ref('')

function refreshStatusDot(): void {
  const st = sidecarReady.value === 'ready' ? 'ready' : sidecarReady.value === 'error' ? 'error' : 'connecting'
  statusDot.value = statusDotCls(st as 'ready' | 'error' | 'connecting', 'sm')
}
refreshStatusDot()

function toggleTheme(): void {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  document.documentElement.setAttribute('data-theme', theme.value)
  document.documentElement.classList.toggle('dark', theme.value === 'dark')
  localStorage.setItem('app-theme', theme.value)
}

const NAV_ITEMS: Array<{ key: ViewKey; label: string }> = [
  { key: 'gallery', label: '✨ 示例画廊' },
  { key: 'toolbox', label: '🧰 工具箱' }
]

// 状态栏计数：纯派生数据，依赖变化自动更新（旧版 updateStatusCount 的响应式等价物）
const statusCount = computed(() =>
  activeView.value === 'toolbox'
    ? `${toolboxItems.value.length} / ${toolsTotal.value} 个工具`
    : `${filtered.value.length} / ${examples.value.length} 个示例`
)

onMounted(async () => {
  try {
    await api.ping()
    sidecarReady.value = 'ready'
  } catch {
    sidecarReady.value = 'error'
  }
  refreshStatusDot()

  // sidecar 就绪/重启：重载全部数据（与旧窗口 bootstrap + onStatus 语义一致）
  api.on('status', (data) => {
    sidecarReady.value = data.ready ? 'ready' : 'error'
    refreshStatusDot()
    if (data.ready) loadAll()
  })

  await loadAll()
})
</script>

<template>
  <div class="h-screen flex flex-col bg-page text-ink">
    <!-- 顶栏：导航 + 全局动作（app-drag 无边框拖拽区） -->
    <header class="app-drag flex items-center justify-between gap-3 h-10 px-3 bg-panel border-b border-line-subtle shrink-0">
      <div class="app-no-drag flex items-center gap-2 shrink-0">
        <span class="text-[14px]">🐍</span>
        <span class="font-[510] text-[13px] tracking-[-0.01em] whitespace-nowrap">Python 示例管理器</span>
      </div>

      <nav class="app-no-drag flex gap-0.5 bg-page rounded-md p-0.5 border border-line-subtle">
        <button
          v-for="item in NAV_ITEMS"
          :key="item.key"
          class="flex items-center gap-1 px-3 py-1 rounded bg-transparent border-0 text-[12px] font-[510] font-sans cursor-pointer transition-all duration-[120ms] whitespace-nowrap"
          :class="activeView === item.key ? 'bg-card text-ink shadow-elev-1' : 'text-ink-mute hover:text-ink'"
          @click="activeView = item.key"
        >
          {{ item.label }}
        </button>
        <button
          class="flex items-center gap-1 px-3 py-1 rounded bg-transparent border-0 text-ink-faint text-[12px] font-[510] font-sans cursor-not-allowed whitespace-nowrap"
          title="运行器视图将在迁移步骤 4 落地，当前请使用旧窗口"
          disabled
        >
          ⌨️ 运行器
        </button>
      </nav>

      <div class="app-no-drag flex items-center gap-2 shrink-0">
        <button
          class="inline-flex items-center px-3 py-[5px] border border-line-subtle rounded-md bg-transparent text-ink-dim text-[12px] font-[510] font-sans cursor-pointer transition-all duration-[120ms] hover:bg-hover hover:text-ink disabled:opacity-[0.35]"
          :disabled="loading"
          title="重新加载示例"
          @click="loadAll()"
        >
          ↻
        </button>
        <button
          class="inline-flex items-center px-3 py-[5px] border border-line-subtle rounded-md bg-transparent text-ink-dim text-[12px] font-[510] font-sans cursor-pointer transition-all duration-[120ms] hover:bg-hover hover:text-ink"
          title="切换主题"
          @click="toggleTheme"
        >
          {{ theme === 'dark' ? '🌙' : '☀️' }}
        </button>
      </div>
    </header>

    <!-- 视图主体 -->
    <GalleryView v-show="activeView === 'gallery'" @reload="loadAll()" />
    <ToolboxView v-show="activeView === 'toolbox'" @reload="loadAll()" />

    <!-- 底部状态栏 -->
    <footer class="flex items-center gap-3 h-7 px-3 bg-panel border-t border-line-subtle shrink-0 text-[11px] text-ink-mute">
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-1.5 h-1.5 rounded-full shrink-0" :class="statusDot"></span>
        sidecar {{ sidecarReady === 'ready' ? '已连接' : sidecarReady === 'error' ? '已断开' : '连接中' }}
      </span>
      <span data-testid="status-count">{{ statusCount }}</span>
      <span class="ml-auto">就绪</span>
    </footer>
  </div>
</template>
