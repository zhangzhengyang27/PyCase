<script setup lang="ts">
// ToolManualPage：工具手册页（W7 基座）——剩余工具的「页面」底线形态。
// 结构 = 页头（返回/标题/徽章）+ 概述 + 用法 + 参数表 + 注意点 + 运行交接区。
// 手册内容是构建期静态数据（tool-manuals.json）；「运行」交接给详情页的
// ArgsForm/OutputPanel 既有链路（runFromCard = openDetail + 自动运行），本页不重复造运行器。
import { computed } from 'vue'
import { ArrowLeft, BookOpen, Play, SquareTerminal } from 'lucide-vue-next'
import BaseButton from '../base/BaseButton.vue'
import { manualExample, manualExampleId, manualFor } from '../../src/tool-manuals'
import { closeInteractive } from '../../src/store/interactive'
import { openDetail, runFromCard } from '../../src/store/detail'
import { selectedId } from '../../src/store/detail'

const exId = computed(() => manualExampleId(selectedId.value))
const entry = computed(() => (exId.value ? manualFor(exId.value) : undefined))
const title = computed(() => manualExample.value?.title ?? entry.value?.title ?? '工具手册')
const summary = computed(() => manualExample.value?.description ?? entry.value?.summary ?? '')

function fmtDefault(d: unknown): string {
  if (d === undefined) return '—'
  if (typeof d === 'string') return d === '' ? '（空串）' : d
  return JSON.stringify(d)
}
function fmtFlag(p: { flag: string; positional?: boolean; nargs?: string }): string {
  if (p.positional) return p.nargs === '?' ? `[${p.flag}]` : p.flag
  return p.flag
}
</script>

<template>
  <section class="flex-1 min-w-0 min-h-0 flex flex-col bg-page overflow-hidden">
    <div class="app-drag select-none px-8 pt-7 pb-3 flex items-center gap-3">
      <button
        class="app-no-drag border border-line rounded-control bg-transparent text-ink-mute hover:text-accent hover:border-accent cursor-pointer p-1.5"
        data-testid="manual-back"
        aria-label="返回"
        @click="closeInteractive()"
      >
        <ArrowLeft :size="15" />
      </button>
      <h1 class="text-[length:--text-page] font-semibold text-ink m-0 tracking-[-0.02em]">{{ title }}</h1>
      <span class="text-caption text-ink-mute border border-line rounded-control px-2 py-0.5">
        <BookOpen :size="11" class="inline mr-1 -mt-0.5" />工具手册
      </span>
    </div>

    <div class="flex-1 min-h-0 overflow-y-auto app-no-drag">
      <div class="max-w-[900px] mx-auto px-8 pb-8 flex flex-col gap-5">
        <template v-if="entry">
          <p class="text-control text-ink-dim leading-[1.7] m-0" data-testid="manual-summary">{{ summary }}</p>

          <section>
            <h2 class="text-title font-semibold text-ink mb-2">用法</h2>
            <pre
              class="m-0 p-3 bg-page border border-line rounded-control text-control font-mono overflow-auto"
              data-testid="manual-usage"
              >{{ entry.usage }}</pre>
          </section>

          <section v-if="entry.params.length">
            <h2 class="text-title font-semibold text-ink mb-2">参数（{{ entry.params.length }}）</h2>
            <div class="flex flex-col gap-1.5" data-testid="manual-params">
              <div v-for="p in entry.params" :key="p.flag" class="surface-card px-3 py-2 flex items-baseline gap-3">
                <code class="text-control font-mono text-accent shrink-0">{{ fmtFlag(p) }}</code>
                <span v-if="p.type" class="text-caption text-ink-faint shrink-0">{{ p.type }}</span>
                <span class="text-caption text-ink-mute flex-1">{{ p.help || '—' }}</span>
                <span class="text-caption text-ink-faint shrink-0">默认 {{ fmtDefault(p.default) }}</span>
              </div>
            </div>
          </section>

          <section v-if="entry.notes?.length">
            <h2 class="text-title font-semibold text-ink mb-2">注意</h2>
            <ul class="m-0 pl-4 list-disc text-control text-ink-mute flex flex-col gap-1" data-testid="manual-notes">
              <li v-for="(n, i) in entry.notes" :key="i">{{ n }}</li>
            </ul>
          </section>

          <section class="surface-card p-4 flex flex-col gap-3">
            <h2 class="text-title font-semibold text-ink m-0">运行</h2>
            <p class="text-caption text-ink-mute m-0">
              运行在详情页进行：参数表单已按 argparse 自动生成，输出、历史与资源管理齐全。
            </p>
            <div class="flex gap-2">
              <BaseButton
                variant="primary"
                data-testid="manual-run"
                title="打开详情页并按当前参数运行"
                @click="exId && runFromCard(exId)"
              >
                <Play :size="14" /> 在详情页运行
              </BaseButton>
              <BaseButton
                data-testid="manual-open-detail"
                title="打开详情页查看与编辑代码"
                @click="exId && openDetail(exId)"
              >
                <SquareTerminal :size="14" /> 打开详情页
              </BaseButton>
            </div>
          </section>
        </template>

        <div v-else class="text-control text-ink-mute pt-10 text-center" data-testid="manual-ghost">
          该工具暂无手册页
        </div>
      </div>
    </div>
  </section>
</template>
