<script setup lang="ts">
// App：应用壳（设计规范 v1：hiddenInset + Linear 式左侧导航栏 + Cmd+K 命令面板）
// 视图组件经 store 的 computed 派生数据驱动，无 applyAllFilters 式手动刷新。
// macOS 下导航栏兼任窗口标题栏：头区左侧为红绿灯留白，空区 app-drag、按钮 app-no-drag。
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import {
  FolderUp,
  LayoutGrid,
  LibraryBig,
  Monitor,
  Moon,
  RefreshCw,
  Search,
  Settings,
  SquareTerminal,
  SunMedium,
  Wrench,
  type LucideIcon
} from 'lucide-vue-next'
import { api } from './src/sidecar-client'
import { statusDotCls } from './src/utils'
import { applyMonacoTheme } from './monaco'
import {
  activeView,
  aiPanelOpen,
  aiSettingsOpen,
  examples,
  filtered,
  galleryExamples,
  initAIEvents,
  initRunEvents,
  loadAISettings,
  loadAll,
  loading,
  openAISettings,
  openImportWizard,
  runStatusText,
  selectedId,
  toolboxItems,
  toolsTotal,
  type ViewKey
} from './store'
import GalleryView from './components/GalleryView.vue'
import ToolboxView from './components/ToolboxView.vue'
import DetailPage from './components/DetailPage.vue'
import RunnerView from './components/RunnerView.vue'
import AIExplainPanel from './components/AIExplainPanel.vue'
import AISettingsModal from './components/AISettingsModal.vue'
import HighRiskConfirmModal from './components/HighRiskConfirmModal.vue'
import ImportWizardModal from './components/ImportWizardModal.vue'
import CommandPalette from './components/CommandPalette.vue'
import AppToast from './components/base/AppToast.vue'

const sidecarReady = ref<'checking' | 'ready' | 'error'>('checking')
// 主题三态偏好（dark/light/system）；appliedTheme 是 system 解析后的实际生效主题
type ThemePref = 'dark' | 'light' | 'system'
const systemDark = window.matchMedia('(prefers-color-scheme: dark)')
const storedTheme = localStorage.getItem('app-theme')
const themePref = ref<ThemePref>(storedTheme === 'light' || storedTheme === 'system' ? storedTheme : 'dark')
const appliedTheme = ref(document.documentElement.getAttribute('data-theme') || 'dark')
const paletteOpen = ref(false)

const statusDot = ref('')

function refreshStatusDot(): void {
  const st = sidecarReady.value === 'ready' ? 'ready' : sidecarReady.value === 'error' ? 'error' : 'connecting'
  statusDot.value = statusDotCls(st as 'ready' | 'error' | 'connecting', 'sm')
}
refreshStatusDot()

function applyTheme(pref: ThemePref): void {
  appliedTheme.value = pref === 'system' ? (systemDark.matches ? 'dark' : 'light') : pref
  document.documentElement.setAttribute('data-theme', appliedTheme.value)
  document
    .querySelector('meta[name="theme-color"]')
    ?.setAttribute('content', appliedTheme.value === 'light' ? '#f7f8f8' : '#08090a')
  applyMonacoTheme()
}

const THEME_META: Record<ThemePref, { label: string; icon: LucideIcon }> = {
  dark: { label: '主题：深色', icon: Moon },
  light: { label: '主题：浅色', icon: SunMedium },
  system: { label: '主题：跟随系统', icon: Monitor }
}

function toggleTheme(): void {
  themePref.value = themePref.value === 'dark' ? 'light' : themePref.value === 'light' ? 'system' : 'dark'
  localStorage.setItem('app-theme', themePref.value)
  applyTheme(themePref.value)
}

// system 模式下，系统外观切换即时生效
function onSystemThemeChange(): void {
  if (themePref.value === 'system') applyTheme('system')
}

const NAV_ITEMS: Array<{ key: ViewKey; label: string; icon: LucideIcon }> = [
  { key: 'gallery', label: '示例画廊', icon: LayoutGrid },
  { key: 'toolbox', label: '工具箱', icon: Wrench },
  { key: 'runner', label: '运行器', icon: SquareTerminal }
]

function setView(key: ViewKey): void {
  activeView.value = key
}

// 状态栏计数：纯派生数据，依赖变化自动更新（各视图口径不同：
// 工具箱 = 工具池，运行器可搜全集，画廊不含工具与工具箱互为补集）
const statusCount = computed(() => {
  if (activeView.value === 'toolbox') return `${toolboxItems.value.length} / ${toolsTotal.value} 个工具`
  if (activeView.value === 'runner') return `${examples.value.length} 个示例`
  return `${filtered.value.length} / ${galleryExamples.value.length} 个示例`
})

// Cmd/Ctrl+K 全局命令面板
function onGlobalKey(e: KeyboardEvent): void {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    paletteOpen.value = !paletteOpen.value
  }
}

onMounted(async () => {
  window.addEventListener('keydown', onGlobalKey)
  systemDark.addEventListener('change', onSystemThemeChange)
  // 运行输出/结束/图片通知订阅 + AI 流式事件订阅（全局一次）
  initRunEvents()
  initAIEvents()
  void loadAISettings()
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

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onGlobalKey)
  systemDark.removeEventListener('change', onSystemThemeChange)
})
</script>

<template>
  <div class="h-screen flex bg-page text-ink">
    <!-- 左侧导航栏（Linear 式宽侧栏）：macOS hiddenInset 下兼任标题栏，
         红绿灯悬浮于头区左侧留白，头区与栏内空区 app-drag -->
    <nav class="app-drag flex flex-col w-44 shrink-0 bg-panel border-r border-line-subtle select-none">
      <!-- 头区：红绿灯（trafficLightPosition 8,12，右缘 ≈60px）右侧放品牌行 -->
      <div class="flex items-center gap-2 h-10 pl-[72px] pr-2 shrink-0" title="Python 示例管理器">
        <div class="w-[18px] h-[18px] rounded-[5px] bg-ok-bg text-ok border border-ok/25 flex items-center justify-center shrink-0">
          <LibraryBig :size="11" />
        </div>
        <span class="text-body font-medium text-ink-dim truncate">示例管理器</span>
      </div>

      <!-- 搜索：内嵌输入槽质感 -->
      <div class="flex flex-col gap-0.5 px-2 pt-1 shrink-0">
        <button
          class="app-no-drag flex items-center gap-2 w-full h-8 px-2.5 rounded-control border border-line-subtle bg-inset cursor-pointer font-sans text-body font-normal text-ink-faint hover:text-ink-dim transition-colors duration-[120ms]"
          title="全局搜索（⌘K）"
          @click="paletteOpen = true"
        >
          <Search :size="16" :stroke-width="1.8" class="shrink-0" />
          <span>搜索</span>
          <kbd class="ml-auto px-1 py-px text-badge font-mono bg-card border border-line-subtle rounded-badge text-ink-faint">⌘&nbsp;K</kbd>
        </button>
      </div>

      <div class="h-px bg-line mx-3 my-2 shrink-0" aria-hidden="true"></div>

      <!-- 主视图导航：行式（图标 + 文字同行），标准字重（400/500，非标中间字重会触发苹方合成加粗发虚），
           激活态 = 卡片底胶囊 + 左缘强调条 -->
      <div class="flex flex-col gap-0.5 px-2 shrink-0">
        <button
          v-for="item in NAV_ITEMS"
          :key="item.key"
          class="app-no-drag relative flex items-center gap-2 w-full h-8 px-2.5 rounded-control cursor-pointer font-sans text-body transition-colors duration-[120ms]"
          :class="activeView === item.key
            ? 'surface-raised text-ink font-medium'
            : 'border-0 bg-transparent text-ink-mute hover:text-ink hover:bg-hover font-normal'"
          :aria-current="activeView === item.key ? 'page' : undefined"
          @click="setView(item.key)"
        >
          <span
            class="absolute -left-2 top-1/2 -translate-y-1/2 w-0.5 h-4 rounded-full bg-accent transition-[opacity,transform] duration-[180ms]"
            :class="activeView === item.key ? 'opacity-100' : 'opacity-0 scale-y-50'"
            aria-hidden="true"
          ></span>
          <component :is="item.icon" :size="16" :stroke-width="1.8" class="shrink-0" />
          <span class="truncate">{{ item.label }}</span>
        </button>
      </div>

      <div class="flex-1 min-h-3" aria-hidden="true"></div>

      <div class="h-px bg-line mx-3 mb-2 shrink-0" aria-hidden="true"></div>

      <!-- 全局工具 -->
      <div class="flex flex-col gap-0.5 px-2 pb-2 shrink-0">
        <button
          class="app-no-drag flex items-center gap-2 w-full h-8 px-2.5 rounded-control border-0 bg-transparent cursor-pointer font-sans text-body font-normal text-ink-mute hover:text-ink hover:bg-hover transition-colors duration-[120ms]"
          @click="openImportWizard()"
        >
          <FolderUp :size="16" :stroke-width="1.8" class="shrink-0" />
          <span class="truncate">导入示例目录</span>
        </button>
        <button
          class="app-no-drag flex items-center gap-2 w-full h-8 px-2.5 rounded-control border-0 bg-transparent cursor-pointer font-sans text-body font-normal text-ink-mute hover:text-ink hover:bg-hover transition-colors duration-[120ms]"
          @click="openAISettings()"
        >
          <Settings :size="16" :stroke-width="1.8" class="shrink-0" />
          <span class="truncate">设置</span>
        </button>
        <button
          class="app-no-drag flex items-center gap-2 w-full h-8 px-2.5 rounded-control border-0 bg-transparent cursor-pointer font-sans text-body font-normal text-ink-mute hover:text-ink hover:bg-hover transition-colors duration-[120ms]"
          title="切换主题（深色 / 浅色 / 跟随系统）"
          @click="toggleTheme"
        >
          <component :is="THEME_META[themePref].icon" :size="16" :stroke-width="1.8" class="shrink-0" />
          <span class="truncate">{{ THEME_META[themePref].label }}</span>
        </button>
        <button
          class="app-no-drag flex items-center gap-2 w-full h-8 px-2.5 rounded-control border-0 bg-transparent cursor-pointer font-sans text-body font-normal text-ink-mute hover:text-ink hover:bg-hover transition-colors duration-[120ms] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent disabled:hover:text-ink-mute"
          :disabled="loading"
          @click="loadAll()"
        >
          <RefreshCw :size="16" :stroke-width="1.8" class="shrink-0" :class="{ 'animate-spin': loading }" />
          <span class="truncate">重新加载示例</span>
        </button>
      </div>
    </nav>

    <!-- 视图主体（详情页打开时隐藏来源视图，与旧窗口行为一致） -->
    <div class="flex-1 min-w-0 min-h-0 flex flex-col">
      <div class="flex-1 min-h-0 flex">
        <GalleryView v-show="!selectedId && activeView === 'gallery'" class="animate-view-in" @reload="loadAll()" />
        <ToolboxView v-show="!selectedId && activeView === 'toolbox'" class="animate-view-in" @reload="loadAll()" />
        <RunnerView v-show="!selectedId && activeView === 'runner'" class="animate-view-in" />
        <DetailPage v-if="selectedId" class="animate-view-in" />
      </div>

      <!-- 底部状态栏（空区兼作拖拽面） -->
      <footer class="app-drag flex items-center gap-3 h-7 px-3 bg-panel border-t border-line-subtle shrink-0 text-caption text-ink-mute select-none">
        <span class="app-no-drag flex items-center gap-1.5">
          <span class="inline-block w-1.5 h-1.5 rounded-full shrink-0" :class="statusDot"></span>
          sidecar {{ sidecarReady === 'ready' ? '已连接' : sidecarReady === 'error' ? '已断开' : '连接中' }}
        </span>
        <span v-if="!selectedId" data-testid="status-count" class="app-no-drag">{{ statusCount }}</span>
        <span class="ml-auto app-no-drag" aria-live="polite">{{ runStatusText }}</span>
      </footer>
    </div>

    <!-- AI 解释侧栏与设置弹窗 -->
    <AIExplainPanel v-if="aiPanelOpen" />
    <AISettingsModal v-if="aiSettingsOpen" />
    <HighRiskConfirmModal />
    <ImportWizardModal />
    <CommandPalette v-if="paletteOpen" @close="paletteOpen = false" />
    <AppToast />
  </div>
</template>
