<script setup lang="ts">
// App：应用壳（视觉基线 v2 / A1）
// 三层绑定：html[data-platform]（平台几何与选中语义）× html[data-theme]（主题）
// × html[data-accent]（强调色），均由 preload/main.ts 在首帧前写入，模板只消费。
// 平台差异一律走 token 与 data-platform 选择器，模板内不再出现平台判断分支以外的硬编码。
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import {
  CircleHelp,
  Copy,
  FolderUp,
  Layers,
  LayoutGrid,
  LibraryBig,
  Minus,
  Monitor,
  Moon,
  RefreshCw,
  Search,
  Settings,
  Square,
  SquareTerminal,
  SunMedium,
  Wrench,
  X,
  type LucideIcon
} from 'lucide-vue-next'
import { api } from './src/sidecar-client'
import { createWindowControls, modKeyLabel } from './src/platform'
import { sectionIcon } from './src/section-icons'
import AlertBanner from './components/base/AlertBanner.vue'
import AppModal from './components/base/AppModal.vue'
import BaseButton from './components/base/BaseButton.vue'
import { statusDotCls } from './src/utils'
import { applyMonacoTheme } from './monaco'
import { aiPanelOpen, aiSettingsOpen, initAIEvents, loadAISettings, openAISettings } from './src/store/ai'
import {
  activeSectionKey,
  activeView,
  examples,
  filtered,
  galleryExamples,
  gallerySectionNav,
  loading,
  selectSection,
  toolboxItems,
  toolsTotal,
  type ViewKey
} from './src/store/catalog'
import { initRunEvents, runStatusText, selectedId } from './src/store/detail'
import {
  closeHelp,
  dismissOnboarding,
  helpOpen,
  initEnvEvents,
  loadAppInfo,
  loadOnboarding,
  onboardingOpen,
  openHelp,
  openLog,
  retryEnvPrepare
} from './src/store/env'
import { confirmPrompt, resolveConfirm } from './src/store/detail'
import { openImportWizard } from './src/store/import'
import { loadAll } from './src/store/index'
import GalleryView from './components/GalleryView.vue'
import HelpSheet from './components/HelpSheet.vue'
import OnboardingView from './components/OnboardingView.vue'
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
/** sidecar 退出信息（失败恢复出口的数据源）：熔断时给"重启/看日志"，未熔断则说明会自动重启 */
const sidecarExit = ref<{ code: number | null; crashed: boolean; autoRestartDisabled: boolean }>({
  code: null,
  crashed: false,
  autoRestartDisabled: false
})
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
  // theme-color 跟随窗口底色令牌（与 main.ts 启动路径同一口径，不留字面值）
  document
    .querySelector('meta[name="theme-color"]')
    ?.setAttribute('content', getComputedStyle(document.documentElement).getPropertyValue('--bg-window').trim())
  applyMonacoTheme()
}

// 平台来自 preload（process.platform 写入的 data-platform），渲染层不猜平台：
// 键盘提示、平台专属文案都经 src/platform.ts 派生（窗口三键在 CSS 层按平台显隐）
const modKey = ref(modKeyLabel())

// Windows 自绘标题栏：最大化状态由主进程回推
const maximized = ref(false)
let offMaximized: (() => void) | null = null
// 平台适配层：窗口三键（Windows 自绘标题栏）——组件不直接摸 window.sidecar
const windowControls = createWindowControls({
  minimize: () => api.win.minimize(),
  toggleMaximize: () => api.win.toggleMaximize(),
  close: () => api.win.close(),
  isMaximized: () => api.win.isMaximized(),
  onMaximized: (fn) => api.on('maximized', (data) => fn(!!data?.maximized))
})
function windowAction(action: 'minimize' | 'toggleMaximize' | 'close'): void {
  if (action === 'minimize') windowControls.minimize()
  else if (action === 'toggleMaximize') void windowControls.toggleMaximize().then((v) => (maximized.value = !!v))
  else windowControls.close()
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

// 侧栏导航计数徽章：与状态栏同源（分母口径，表示该视图的总量）
const navBadge = computed<Record<ViewKey, string>>(() => ({
  gallery: galleryExamples.value.length.toLocaleString('zh-CN'),
  toolbox: toolsTotal.value.toLocaleString('zh-CN'),
  runner: ''
}))

// Cmd/Ctrl+K 全局命令面板
function onGlobalKey(e: KeyboardEvent): void {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    paletteOpen.value = !paletteOpen.value
  } else if ((e.metaKey || e.ctrlKey) && e.key === '/') {
    // ⌘/ · Ctrl / 打开/关闭帮助（与 ⌘K 同族，不冲突）
    e.preventDefault()
    if (helpOpen.value) closeHelp()
    else openHelp()
  }
}

onMounted(async () => {
  window.addEventListener('keydown', onGlobalKey)
  systemDark.addEventListener('change', onSystemThemeChange)
  // 自绘标题栏最大化状态：主进程事件 + 首帧对齐（win 专用按钮，mac 下按钮不渲染）
  offMaximized = windowControls.onMaximizedChange((v) => (maximized.value = v))
  void windowControls.isMaximized().then((v) => (maximized.value = v))
  // 运行输出/结束/图片通知订阅 + AI 流式事件订阅（全局一次）
  initRunEvents()
  initAIEvents()
  // 环境阶段订阅（首启页/帮助面板）+ 应用信息 + 首启标记（首帧后，不等 sidecar ready）
  initEnvEvents()
  void loadAppInfo()
  void loadOnboarding()
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
    if (data.ready) {
      sidecarExit.value = { code: null, crashed: false, autoRestartDisabled: false }
      loadAll()
    } else {
      sidecarExit.value = {
        code: data.code ?? null,
        crashed: !!data.crashed,
        autoRestartDisabled: !!data.autoRestartDisabled
      }
    }
    refreshStatusDot()
  })

  await loadAll()
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onGlobalKey)
  systemDark.removeEventListener('change', onSystemThemeChange)
  offMaximized?.()
})
</script>

<template>
  <div class="h-screen flex text-ink">
    <!-- 侧栏（材质面）：macOS 下兼任标题栏——红绿灯由系统绘制在 --titlebar-lead 留白内，
         win 下同样高度的头区只放应用名。空区 app-drag，交互件 app-no-drag。 -->
    <nav class="app-drag sidebar flex flex-col shrink-0 select-none">
      <div class="side-head titlebar-lead flex items-center gap-2 pr-3 shrink-0">
        <span class="appname truncate">示例库</span>
      </div>

      <!-- 搜索槽：打开命令面板（v2 不用内嵌真实输入框，避免与面板双入口） -->
      <div class="px-2.5 pt-1 pb-2 shrink-0">
        <button
          class="app-no-drag flex items-center gap-2 w-full h-[var(--ctrl-md)] px-2 rounded-control border border-line-subtle bg-inset cursor-pointer font-sans text-body text-ink-mute hover:text-ink-dim transition-colors dur-fast"
          :title="`全局搜索（${modKey} K）`"
          @click="paletteOpen = true"
        >
          <Search :size="16" :stroke-width="1.5" class="shrink-0" />
          <span class="truncate">搜索</span>
          <kbd
            class="ml-auto shrink-0 px-1 py-px text-caption font-mono border border-line-subtle rounded-control text-ink-mute"
          >
            {{ modKey }} K
          </kbd>
        </button>
      </div>

      <!-- 主视图导航（「示例画廊」下挂二级分区菜单：全部示例 + 15 分区） -->
      <div class="px-2.5 shrink-0">
        <div class="px-2 pb-1 text-caption text-ink-mute">浏览</div>
        <div class="flex flex-col gap-px">
          <template v-for="item in NAV_ITEMS" :key="item.key">
            <button
              class="navitem app-no-drag"
              :class="{ sel: activeView === item.key }"
              :aria-current="activeView === item.key ? 'page' : undefined"
              @click="setView(item.key)"
            >
              <span class="accent-bar" aria-hidden="true"></span>
              <component :is="item.icon" :size="16" :stroke-width="1.5" class="shrink-0" />
              <span class="truncate">{{ item.label }}</span>
              <span v-if="navBadge[item.key]" class="badge-n">{{ navBadge[item.key] }}</span>
            </button>

            <!-- 画廊二级分区菜单：仅画廊视图展开；每项 label + 计数，当前分区有激活态；
                 全部示例置首（activeSectionKey === null）。菜单超高时内部滚动，不吃掉下方工具区 -->
            <div
              v-if="item.key === 'gallery' && activeView === 'gallery'"
              class="flex flex-col gap-px mt-0.5 mb-1 pl-3 max-h-[42vh] overflow-y-auto [scrollbar-width:thin]"
              data-testid="gallery-subnav"
            >
              <button
                class="subnav app-no-drag"
                :class="{ sel: activeSectionKey === null }"
                :aria-current="activeSectionKey === null ? 'true' : undefined"
                data-testid="gallery-subnav-all"
                data-section-key="all"
                data-section-label="全部示例"
                :data-section-count="galleryExamples.length"
                @click="selectSection(null)"
              >
                <Layers :size="14" :stroke-width="1.5" class="shrink-0" />
                <span class="truncate">全部示例</span>
                <span class="badge-n">{{ galleryExamples.length.toLocaleString('zh-CN') }}</span>
              </button>
              <button
                v-for="sec in gallerySectionNav"
                :key="sec.key"
                class="subnav app-no-drag"
                :class="{ sel: activeSectionKey === sec.key }"
                :aria-current="activeSectionKey === sec.key ? 'true' : undefined"
                data-testid="gallery-subnav-item"
                :data-section-key="sec.key"
                :data-section-label="sec.label"
                :data-section-count="sec.count"
                @click="selectSection(sec.key)"
              >
                <component :is="sectionIcon(sec.key)" :size="14" :stroke-width="1.5" class="shrink-0" />
                <span class="truncate">{{ sec.label }}</span>
                <span class="badge-n">{{ sec.count.toLocaleString('zh-CN') }}</span>
              </button>
            </div>
          </template>
        </div>
      </div>

      <div class="flex-1 min-h-3" aria-hidden="true"></div>

      <!-- 全局工具 -->
      <div class="flex flex-col gap-px px-2.5 pb-2.5 shrink-0">
        <button class="navitem app-no-drag" @click="openImportWizard()">
          <FolderUp :size="16" :stroke-width="1.5" class="shrink-0" />
          <span class="truncate">导入示例目录</span>
        </button>
        <button class="navitem app-no-drag" @click="openAISettings()">
          <Settings :size="16" :stroke-width="1.5" class="shrink-0" />
          <span class="truncate">设置</span>
        </button>
        <button class="navitem app-no-drag" title="帮助与快捷键（⌘/）" @click="openHelp()">
          <CircleHelp :size="16" :stroke-width="1.5" class="shrink-0" />
          <span class="truncate">帮助</span>
        </button>
        <button class="navitem app-no-drag" :title="`当前：${THEME_META[themePref].label}`" @click="toggleTheme">
          <component :is="THEME_META[themePref].icon" :size="16" :stroke-width="1.5" class="shrink-0" />
          <span class="truncate">{{ THEME_META[themePref].label }}</span>
        </button>
        <button class="navitem app-no-drag" :disabled="loading" @click="loadAll()">
          <RefreshCw :size="16" :stroke-width="1.5" class="shrink-0" :class="{ 'animate-spin': loading }" />
          <span class="truncate">重新加载示例</span>
        </button>
      </div>
    </nav>

    <!-- 视图主体（详情页打开时隐藏来源视图，与旧窗口行为一致） -->
    <div class="flex-1 min-w-0 min-h-0 flex flex-col">
      <!-- Windows 自绘标题栏：mac 下 display:none 交还系统红绿灯 -->
      <div class="titlebar-win app-drag items-center shrink-0">
        <span class="titlebar-lead flex items-center gap-2 text-caption text-ink-dim">
          <span class="w-4 h-4 rounded-[4px] bg-accent text-on-accent inline-flex items-center justify-center shrink-0">
            <LibraryBig :size="10" :stroke-width="2" />
          </span>
          PyCase
        </span>
        <span class="ml-auto flex">
          <button class="caption-btn app-no-drag" title="最小化" aria-label="最小化" @click="windowAction('minimize')">
            <Minus :size="14" :stroke-width="1.5" />
          </button>
          <button
            class="caption-btn app-no-drag"
            :title="maximized ? '向下还原' : '最大化'"
            :aria-label="maximized ? '向下还原' : '最大化'"
            @click="windowAction('toggleMaximize')"
          >
            <Copy v-if="maximized" :size="12" :stroke-width="1.5" />
            <Square v-else :size="12" :stroke-width="1.5" />
          </button>
          <button class="caption-btn close app-no-drag" title="关闭" aria-label="关闭" @click="windowAction('close')">
            <X :size="15" :stroke-width="1.5" />
          </button>
        </span>
      </div>

      <!-- 失败恢复出口（审计 A2）：崩溃/熔断事件原先渲染层零订阅者，现在给出动作 -->
      <div v-if="sidecarReady === 'error'" class="px-3 pt-2.5 shrink-0" data-testid="sidecar-down">
        <AlertBanner
          :title="
            sidecarExit.crashed
              ? `示例引擎已停止运行（退出码 ${sidecarExit.code ?? '未知'}）。${
                  sidecarExit.autoRestartDisabled ? '短时间多次崩溃，已停止自动重启。' : ''
                }`
              : `示例引擎已断开（退出码 ${sidecarExit.code ?? '未知'}），正在自动重启…`
          "
        >
          <button
            class="ml-2 text-caption text-accent hover:underline cursor-pointer bg-transparent border-0 p-0 shrink-0"
            data-testid="sidecar-restart"
            @click="retryEnvPrepare()"
          >
            重启引擎
          </button>
          <button
            class="ml-3 text-caption text-ink-dim hover:underline cursor-pointer bg-transparent border-0 p-0 shrink-0"
            @click="openLog()"
          >
            查看日志
          </button>
        </AlertBanner>
      </div>

      <!-- 应用内确认弹窗（A6 产品化：替换原生 confirm；未保存守卫与 AI 首次外发共用） -->
      <AppModal v-if="confirmPrompt" :title="confirmPrompt.title" :max-width="440" @close="resolveConfirm(false)">
        <p class="m-0 text-control text-ink-dim leading-[1.6]">{{ confirmPrompt.message }}</p>
        <template #footer>
          <BaseButton data-testid="confirm-cancel" @click="resolveConfirm(false)">取消</BaseButton>
          <BaseButton variant="danger" data-testid="confirm-ok" @click="resolveConfirm(true)">
            {{ confirmPrompt.confirmLabel }}
          </BaseButton>
        </template>
      </AppModal>

      <main class="flex-1 min-h-0 min-w-0 flex bg-page">
        <GalleryView v-show="!selectedId && activeView === 'gallery'" class="animate-view-in" @reload="loadAll()" />
        <ToolboxView v-show="!selectedId && activeView === 'toolbox'" class="animate-view-in" @reload="loadAll()" />
        <RunnerView v-show="!selectedId && activeView === 'runner'" class="animate-view-in" />
        <DetailPage v-if="selectedId" class="animate-view-in" />
      </main>

      <!-- 底部状态栏（空区兼作拖拽面） -->
      <footer class="statusbar app-drag flex items-center gap-3 px-3.5 shrink-0 select-none">
        <span class="app-no-drag flex items-center gap-1.5">
          <span class="inline-block w-1.5 h-1.5 rounded-full shrink-0" :class="statusDot"></span>
          {{ sidecarReady === 'ready' ? '已连接' : sidecarReady === 'error' ? '已断开' : '连接中' }}
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
    <HelpSheet v-if="helpOpen" @close="closeHelp()" />
    <OnboardingView v-if="onboardingOpen" @dismiss="dismissOnboarding()" />
    <AppToast />
  </div>
</template>
