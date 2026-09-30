<script setup lang="ts">
// DetailPage：示例详情页（设计规范 v1）
// 头部 44px（返回/图标块/标题/标签/评分 + 收藏/AI/保存/停止/运行）；
// 主体左右分区 3:2——左 Monaco 编辑，右参数面板 + 输出/资源/历史/版本 四标签；
// <980px 窄屏由 flex 布局自然挤压（右栏 min-width 约束）。快捷键不变：
// Cmd+S 保存 / Cmd+Enter 运行 / Cmd+. 停止。
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { ArrowLeft, ChevronRight, PackagePlus, Play, Save, Sparkles, Square, Star, Trash2 } from 'lucide-vue-next'
import { qualityTextCls, runStatusDotCls, runStatusHint, runStatusLabel, runStatusTextCls } from '../src/utils'
import { categoryIcon } from '../src/icons'
import { CATEGORY_ICONS } from '../src/category-meta'
import { sectionIcon } from '../src/section-icons'
import { sectionKeyOf } from '../src/overview'
import { explainSelectedCode } from '../src/store/ai'
import { assets } from '../src/store/assets'
import {
  closeDetail,
  clearSurface,
  currentArgs,
  installDepsAndRerun,
  installingDeps,
  isDirty,
  isRunning,
  loadVersions,
  saving,
  saveExample,
  selectedExample,
  selectedId,
  surfaceState,
  runFromDetail,
  runStatusText
} from '../src/store/detail'
import { deleteUserExample } from '../src/store/import'
import { isFavorite, toggleFavorite } from '../src/store/prefs'
import { stopRun } from '../src/store/detail'
import ArgsForm from './ArgsForm.vue'
import MonacoEditor from './MonacoEditor.vue'
import OutputPanel from './OutputPanel.vue'
import HistoryPanel from './HistoryPanel.vue'
import VersionsPanel from './VersionsPanel.vue'
import AssetsPanel from './AssetsPanel.vue'
import AppModal from './base/AppModal.vue'
import BaseButton from './base/BaseButton.vue'

// 标签页走 .tab 组件类（v2：mac 抬起段 / win 强调下划线，与 .seg 同平台语义）
const DOT_CLS: Record<string, string> = {
  idle: 'bg-ink-faint',
  running: 'bg-warn animate-pulse',
  success: 'bg-ok',
  error: 'bg-danger'
}

const argsCollapsed = ref(false)
/**
 * 是否给出「安装依赖」入口：静态判定缺依赖，或本次运行输出出现 ImportError。
 * 后者覆盖"清单没声明依赖、静态也没判定出来"的漏网情况（审计 A3 的核心场景）。
 */
const needsDeps = computed(() => {
  if (selectedExample.value?.run_status === 'missing_deps') return true
  const out = surfaceState('detail').lines
  return out.some((l) => /ModuleNotFoundError|ImportError/.test(l.text))
})
const activeTab = ref<'output' | 'assets' | 'history' | 'versions'>('output')
// 删除用户集合示例（确认弹窗由本组件持有；删除动作在 store，成功后自动关闭详情）
const confirmDelete = ref(false)

async function doDelete(): Promise<void> {
  const id = selectedId.value
  confirmDelete.value = false
  if (id) await deleteUserExample(id)
}

const ex = selectedExample
const title = computed(() => {
  if (!ex.value) return '未选择示例'
  const base = ex.value.title || (ex.value.name || '').replace(/\.py$/i, '').replace(/[-_]/g, ' ')
  return base.replace(/\.py$/i, '') + (isDirty.value ? ' ●' : '')
})
// 分类图标：收录分类走语义图标，未知分类回退 categoryIcon（全部已知分类都有图标）
const metaIcon = computed(() => CATEGORY_ICONS[ex.value?.category || ''] ?? categoryIcon(ex.value?.category || ''))
// 可运行性徽章：与卡片（ExampleCard / ExampleListItem）保持同一口径——
// runnable 是正向状态不占视觉，risky 由高危徽章承担展示（见 utils.ts 中
// RUN_STATUS_LABELS 上方的注释）。若直接拿 runStatusLabel() 判定，详情页会多出一个
// 卡片刻意不显示的「可运行」徽章，risk_high 示例还会出现两个「高危」。
const statusBadge = computed(() =>
  ex.value?.run_status && ex.value.run_status !== 'runnable' && ex.value.run_status !== 'risky'
    ? ex.value.run_status
    : ''
)
// 详情页图标与卡片/分区头同源（分区语义图标），未命中回退分类图标；
// 追踪 ex.code：保存后 invalidateExampleVisual 清备忘，此处随之重算，图标即时刷新
const headIcon = computed(() => {
  void ex.value?.code
  if (!ex.value) return metaIcon.value
  return sectionIcon(sectionKeyOf(ex.value)) ?? metaIcon.value
})
// 路径副标题（specs §4.3）：分类 / 示例 id（无 id 回退文件名）
const pathLabel = computed(() => [ex.value?.category, ex.value?.id || ex.value?.name].filter(Boolean).join(' / '))

function switchTab(tab: 'output' | 'assets' | 'history' | 'versions'): void {
  activeTab.value = tab
  // 版本页每次进入都刷新：刚保存过的示例在这里要能看到新快照
  if (tab === 'versions') void loadVersions()
}

function onKeydown(e: KeyboardEvent): void {
  if (!(e.ctrlKey || e.metaKey)) return
  if (e.key === 's') {
    e.preventDefault()
    void saveExample()
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (!isRunning.value) runFromDetail()
  } else if (e.key === '.') {
    e.preventDefault()
    if (isRunning.value) void stopRun()
  }
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <section v-if="ex" class="flex-1 min-w-0 min-h-0 flex flex-col bg-page overflow-hidden">
    <!-- 头部 44px（空白区兼作窗口拖拽面，返回/操作钮已排除） -->
    <div class="app-drag select-none flex items-center gap-2 px-3 h-11 bg-panel border-b border-line-subtle shrink-0">
      <BaseButton square class="app-no-drag" title="返回画廊" aria-label="返回画廊" @click="closeDetail()">
        <ArrowLeft :size="15" />
      </BaseButton>

      <!-- 图标取分区语义图标（与卡片/分区头同源），未命中回退分类图标 -->
      <span class="chip-ic">
        <component :is="headIcon" :size="15" :stroke-width="1.5" />
      </span>

      <div class="min-w-0 flex-1 flex flex-col justify-center gap-0.5">
        <div class="flex items-center gap-2 min-w-0">
          <span class="text-title font-semibold text-ink truncate tracking-[-0.005em]" :title="title">{{ title }}</span>
          <span
            class="inline-flex items-center px-1.5 py-px rounded-control border border-line-hairline text-caption uppercase tracking-[0.03em] text-ink-mute shrink-0"
            >{{ ex.category }}</span
          >
          <span
            v-if="ex.risk_high"
            class="inline-flex items-center gap-1 shrink-0 text-caption text-danger"
            title="含高危操作（系统命令/文件删除等），运行前请先审阅代码"
          >
            <span class="stat-dot bg-danger"></span>高危
          </span>
          <span
            v-if="statusBadge"
            class="inline-flex items-center gap-1 shrink-0 text-caption"
            :class="runStatusTextCls(statusBadge)"
            :title="runStatusHint(statusBadge)"
          >
            <span class="stat-dot" :class="runStatusDotCls(statusBadge)"></span>{{ runStatusLabel(statusBadge) }}
          </span>
        </div>
        <div class="flex items-center gap-1.5 min-w-0">
          <span class="text-badge font-mono text-ink-faint truncate lowercase tracking-[0.02em]" :title="pathLabel">{{
            pathLabel
          }}</span>
          <span
            v-for="tag in (ex.tags || []).slice(0, 3)"
            :key="tag"
            class="text-caption px-1.5 py-px bg-card rounded-badge text-ink-mute font-mono truncate shrink-0"
            >{{ tag }}</span
          >
          <span v-if="(ex.tags || []).length > 3" class="text-caption text-ink-faint shrink-0"
            >+{{ (ex.tags || []).length - 3 }}</span
          >
        </div>
      </div>

      <span
        class="app-no-drag inline-flex items-center gap-1 shrink-0 text-caption font-mono"
        :class="qualityTextCls(ex.quality_score)"
        title="六维质量评分（0-100）"
        ><Star :size="11" :stroke-width="1.5" /> {{ ex.quality_score ?? 0 }}</span
      >

      <div class="app-no-drag flex items-center gap-1.5 shrink-0">
        <BaseButton
          square
          :title="isFavorite(ex.id) ? '取消收藏' : '收藏'"
          :aria-label="isFavorite(ex.id) ? '取消收藏' : '收藏'"
          @click="toggleFavorite(ex.id)"
        >
          <Star :size="15" :class="isFavorite(ex.id) ? 'text-warn fill-current' : ''" />
        </BaseButton>
        <BaseButton
          v-if="ex.user_collection"
          square
          title="从你的集合中删除此示例"
          aria-label="删除此示例"
          @click="confirmDelete = true"
        >
          <Trash2 :size="15" />
        </BaseButton>
        <BaseButton title="AI 解释选中或全部代码（DeepSeek）" @click="explainSelectedCode()">
          <Sparkles :size="13" /> AI 解释
        </BaseButton>
        <BaseButton :disabled="!isDirty || saving" title="保存 (Cmd+S)" @click="saveExample()">
          <Save :size="13" /> {{ saving ? '保存中…' : '保存' }}
        </BaseButton>
        <BaseButton v-if="isRunning" title="停止 (Cmd+.)" @click="stopRun()"> <Square :size="13" /> 停止 </BaseButton>
        <BaseButton
          v-else
          variant="primary"
          size="lg"
          :disabled="!selectedId"
          title="运行 (Cmd+Enter)"
          @click="runFromDetail()"
        >
          <Play :size="13" /> 运行
        </BaseButton>
        <!-- 缺依赖修复路径（审计 A3）：装完自动重跑，让"体检结论"有出口 -->
        <BaseButton
          v-if="needsDeps"
          :loading="installingDeps"
          :disabled="isRunning"
          title="把该示例的第三方依赖装进共享环境后重跑"
          data-testid="install-deps"
          @click="installDepsAndRerun()"
        >
          <PackagePlus :size="13" /> 安装依赖
        </BaseButton>
      </div>
    </div>

    <!-- 主体左右分区 3:2：左 Monaco，右参数 + 输出三标签 -->
    <div class="flex-1 min-h-0 flex">
      <!-- 源码（Monaco，可编辑 + 保存回写） -->
      <div class="flex-[3] min-w-0 relative bg-page overflow-hidden">
        <MonacoEditor />
      </div>

      <!-- 右栏：参数（可折叠）+ 三标签 -->
      <div class="w-[38%] min-w-[320px] max-w-[460px] flex flex-col border-l border-line-subtle bg-panel min-h-0">
        <!-- 参数面板（argparse 静态解析；无参数整区隐藏） -->
        <div v-if="currentArgs.length > 0" class="border-b border-line-subtle shrink-0">
          <button
            class="w-full flex items-center gap-1.5 px-3 h-8 border-0 bg-transparent cursor-pointer select-none text-control font-medium text-ink-dim hover:text-ink"
            :aria-expanded="!argsCollapsed"
            @click="argsCollapsed = !argsCollapsed"
          >
            <ChevronRight
              :size="13"
              class="shrink-0 transition-transform dur-fast"
              :class="argsCollapsed ? '' : 'rotate-90'"
            />
            <span>命令行参数</span>
            <span class="text-caption text-ink-mute font-mono">({{ currentArgs.length }})</span>
          </button>
          <ArgsForm v-show="!argsCollapsed" />
        </div>

        <!-- 三标签行 -->
        <div class="tab-row shrink-0" role="tablist" aria-label="输出面板">
          <button
            id="detail-tab-output"
            class="tab"
            role="tab"
            :aria-selected="activeTab === 'output'"
            aria-controls="detail-panel-output"
            @click="switchTab('output')"
          >
            终端输出
          </button>
          <button
            id="detail-tab-assets"
            class="tab"
            role="tab"
            :aria-selected="activeTab === 'assets'"
            aria-controls="detail-panel-assets"
            @click="switchTab('assets')"
          >
            资源 <span v-if="assets.length" class="text-ink-mute font-mono">({{ assets.length }})</span>
          </button>
          <button
            id="detail-tab-history"
            class="tab"
            role="tab"
            :aria-selected="activeTab === 'history'"
            aria-controls="detail-panel-history"
            @click="switchTab('history')"
          >
            运行历史
          </button>
          <button
            id="detail-tab-versions"
            class="tab"
            role="tab"
            :aria-selected="activeTab === 'versions'"
            aria-controls="detail-panel-versions"
            @click="switchTab('versions')"
          >
            版本
          </button>
          <div class="flex-1"></div>
          <span class="stat-dot" :class="DOT_CLS[surfaceState('detail').dot]" :title="runStatusText"></span>
          <BaseButton size="sm" title="清空输出" @click="clearSurface('detail')">清空</BaseButton>
        </div>
        <OutputPanel
          v-show="activeTab === 'output'"
          id="detail-panel-output"
          role="tabpanel"
          aria-labelledby="detail-tab-output"
          surface="detail"
        />
        <AssetsPanel
          v-show="activeTab === 'assets'"
          id="detail-panel-assets"
          role="tabpanel"
          aria-labelledby="detail-tab-assets"
          class="flex-1 min-h-0"
        />
        <HistoryPanel
          v-show="activeTab === 'history'"
          id="detail-panel-history"
          role="tabpanel"
          aria-labelledby="detail-tab-history"
        />
        <VersionsPanel
          v-show="activeTab === 'versions'"
          id="detail-panel-versions"
          role="tabpanel"
          aria-labelledby="detail-tab-versions"
          class="flex-1 min-h-0"
        />
      </div>
    </div>

    <!-- 删除确认（仅用户集合示例可删） -->
    <AppModal v-if="confirmDelete && ex" title="删除示例" width="440px" @close="confirmDelete = false">
      <p class="m-0 text-control text-ink-dim leading-[1.6]">
        将从你的集合「{{ ex.collection }}」中删除
        <strong class="text-ink">{{ ex.title || ex.name }}</strong>
        ，并清理其运行缓存。内置示例库不受影响，此操作不可撤销。
      </p>
      <template #footer>
        <BaseButton variant="ghost" @click="confirmDelete = false">取消</BaseButton>
        <BaseButton variant="danger" @click="doDelete()">删除</BaseButton>
      </template>
    </AppModal>
  </section>
</template>
