<script setup lang="ts">
// DetailPage：示例详情页（设计规范 v1）
// 头部 44px（返回/图标块/标题/标签/评分 + 收藏/AI/保存/停止/运行）；
// 主体左右分区 3:2——左 Monaco 编辑，右参数面板 + 输出/资源/历史三标签；
// <980px 窄屏由 flex 布局自然挤压（右栏 min-width 约束）。快捷键不变：
// Cmd+S 保存 / Cmd+Enter 运行 / Cmd+. 停止。
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { ArrowLeft, Play, Save, ShieldAlert, Sparkles, Square, Star, Trash2 } from 'lucide-vue-next'
import { qualityBadgeCls, runStatusBadgeCls, runStatusHint, runStatusLabel } from '../src/utils'
import { categoryIcon } from '../src/icons'
import { CATEGORY_META } from '../src/category-meta'
import { exampleVisual } from '../src/overview'
import {
  assets,
  closeDetail,
  clearSurface,
  currentArgs,
  deleteUserExample,
  explainSelectedCode,
  isDirty,
  isFavorite,
  isRunning,
  saving,
  saveExample,
  selectedExample,
  selectedId,
  stopRun,
  surfaceState,
  toggleFavorite,
  runFromDetail,
  runStatusText
} from '../store'
import ArgsForm from './ArgsForm.vue'
import MonacoEditor from './MonacoEditor.vue'
import OutputPanel from './OutputPanel.vue'
import HistoryPanel from './HistoryPanel.vue'
import AssetsPanel from './AssetsPanel.vue'
import AppModal from './base/AppModal.vue'
import BaseButton from './base/BaseButton.vue'

const TAB_IDLE =
  'px-2.5 h-6 inline-flex items-center rounded-[5px] text-control font-[510] font-sans cursor-pointer border border-transparent bg-transparent text-ink-mute hover:text-ink transition-colors duration-[120ms]'
// 激活段不允许出现任何 border 工具类：utilities 层的 border/border-0 会盖过
// components 层 .surface-raised 的 border 简写（Task 4 review 教训），故独立成完整字面量。
const TAB_ACTIVE =
  'px-2.5 h-6 inline-flex items-center rounded-[5px] text-control font-[510] font-sans cursor-pointer surface-raised text-ink transition-colors duration-[120ms]'
const DOT_CLS: Record<string, string> = {
  idle: 'bg-ink-faint',
  running: 'bg-warn animate-pulse',
  success: 'bg-ok',
  error: 'bg-danger'
}

const argsCollapsed = ref(false)
const activeTab = ref<'output' | 'assets' | 'history'>('output')
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
const meta = computed(() => CATEGORY_META[ex.value?.category || ''] || CATEGORY_META.topics)
const metaIcon = computed(() => meta.value?.icon ?? categoryIcon(ex.value?.category || ''))
// 可运行性徽章：与卡片（ExampleCard / ExampleListItem）保持同一口径——
// runnable 是正向状态不占视觉，risky 由高危徽章承担展示（见 utils.ts 中
// RUN_STATUS_LABELS 上方的注释）。若直接拿 runStatusLabel() 判定，详情页会多出一个
// 卡片刻意不显示的「可运行」徽章，risk_high 示例还会出现两个「高危」。
const statusBadge = computed(() =>
  ex.value?.run_status && ex.value.run_status !== 'runnable' && ex.value.run_status !== 'risky'
    ? ex.value.run_status
    : ''
)
// 样张对齐：详情页图标徽章与卡片/分区同源（emoji+分区色相），未命中回退分类；
// 追踪 ex.code：保存后 invalidateExampleVisual 清备忘，此处随之重算，徽章即时刷新
const visual = computed(() => {
  void ex.value?.code
  return ex.value ? exampleVisual(ex.value) : undefined
})
// 路径副标题（specs §4.3）：分类 / 示例 id（无 id 回退文件名）
const pathLabel = computed(() => [ex.value?.category, ex.value?.id || ex.value?.name].filter(Boolean).join(' / '))

function switchTab(tab: 'output' | 'assets' | 'history'): void {
  activeTab.value = tab
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

      <!-- 图标与色相取分区视觉（exampleVisual）；未命中分区回退分类 metaIcon/色相。
           --hue 为 undefined→'' 时 Chromium 视为移除声明，.hue-chip 的 var() 回退生效 -->
      <div class="hue-chip w-7 h-7 rounded-control flex items-center justify-center shrink-0" :style="{ '--hue': visual?.hue || meta?.hue }">
        <span v-if="visual" class="text-[13px] leading-none" aria-hidden="true">{{ visual.emoji }}</span>
        <component :is="metaIcon" v-else :size="15" />
      </div>

      <div class="min-w-0 flex-1 flex flex-col justify-center gap-0.5">
        <div class="flex items-center gap-2 min-w-0">
          <span class="text-title font-[590] text-ink truncate tracking-[-0.005em]" :title="title">{{ title }}</span>
          <span
            v-if="meta"
            class="hue-chip inline-flex items-center px-1.5 py-px rounded-badge text-badge font-[590] uppercase tracking-[0.03em] shrink-0"
            :style="{ '--hue': visual?.hue || meta?.hue }"
            >{{ ex.category }}</span
          >
          <span
            v-if="ex.risk_high"
            class="inline-flex items-center gap-0.5 px-1.5 py-px rounded-badge text-badge font-[590] shrink-0 bg-danger-bg text-danger"
            title="含高危操作（系统命令/文件删除等），运行前请先审阅代码"
          >
            <ShieldAlert :size="10" /> 高危
          </span>
          <span
            v-if="statusBadge"
            class="inline-flex items-center px-1.5 py-px rounded-badge text-badge font-[590] shrink-0"
            :class="runStatusBadgeCls(statusBadge)"
            :title="runStatusHint(statusBadge)"
            >{{ runStatusLabel(statusBadge) }}</span
          >
        </div>
        <div class="flex items-center gap-1.5 min-w-0">
          <span class="text-badge font-mono text-ink-faint truncate lowercase tracking-[0.02em]" :title="pathLabel">{{ pathLabel }}</span>
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
        class="app-no-drag inline-flex items-center gap-1 px-2 h-6 rounded-full text-caption font-[510] font-mono shrink-0"
        :class="qualityBadgeCls(ex.quality_score)"
        title="六维质量评分（0-100）"
        ><Star :size="10" /> {{ ex.quality_score ?? 0 }}</span
      >

      <div class="app-no-drag flex items-center gap-1.5 shrink-0">
        <BaseButton square :title="isFavorite(ex.id) ? '取消收藏' : '收藏'" :aria-label="isFavorite(ex.id) ? '取消收藏' : '收藏'" @click="toggleFavorite(ex.id)">
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
        <BaseButton v-if="isRunning" variant="danger" title="停止 (Cmd+.)" @click="stopRun()">
          <Square :size="13" /> 停止
        </BaseButton>
        <BaseButton v-else variant="primary" size="lg" :disabled="!selectedId" title="运行 (Cmd+Enter)" @click="runFromDetail()">
          <Play :size="13" /> 运行
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
            class="w-full flex items-center gap-1.5 px-3 h-8 border-0 bg-transparent cursor-pointer select-none text-control font-[590] text-ink-dim hover:text-ink"
            :aria-expanded="!argsCollapsed"
            @click="argsCollapsed = !argsCollapsed"
          >
            <span class="transition-transform duration-[120ms]" :class="argsCollapsed ? '' : 'rotate-90'">▶</span>
            <span>命令行参数</span>
            <span class="text-caption text-ink-faint font-mono">({{ currentArgs.length }})</span>
          </button>
          <ArgsForm v-show="!argsCollapsed" />
        </div>

        <!-- 三标签行 -->
        <div class="flex items-center gap-0.5 px-2 h-8 border-b border-line-subtle shrink-0" role="tablist" aria-label="输出面板">
          <button
            id="detail-tab-output"
            :class="activeTab === 'output' ? TAB_ACTIVE : TAB_IDLE"
            role="tab"
            :aria-selected="activeTab === 'output'"
            aria-controls="detail-panel-output"
            @click="switchTab('output')"
          >
            终端输出
          </button>
          <button
            id="detail-tab-assets"
            :class="activeTab === 'assets' ? TAB_ACTIVE : TAB_IDLE"
            role="tab"
            :aria-selected="activeTab === 'assets'"
            aria-controls="detail-panel-assets"
            @click="switchTab('assets')"
          >
            资源 <span v-if="assets.length" class="text-ink-faint font-mono">({{ assets.length }})</span>
          </button>
          <button
            id="detail-tab-history"
            :class="activeTab === 'history' ? TAB_ACTIVE : TAB_IDLE"
            role="tab"
            :aria-selected="activeTab === 'history'"
            aria-controls="detail-panel-history"
            @click="switchTab('history')"
          >
            历史
          </button>
          <div class="flex-1"></div>
          <span class="inline-block w-2 h-2 rounded-full shrink-0" :class="DOT_CLS[surfaceState('detail').dot]" :title="runStatusText"></span>
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
