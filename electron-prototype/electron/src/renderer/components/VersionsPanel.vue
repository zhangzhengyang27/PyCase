<script setup lang="ts">
// VersionsPanel：编辑历史（可恢复编辑）。
//
// - 列表：保存前自动留档的版本（时间倒序，含大小）；
// - 预览：选中某版 → 与"当前编辑器内容"做行级差异（+增 / -删），而不是只给一段文本；
// - 还原：写回真实文件；sidecar 侧还原前也会再留一份快照，所以可以反复回退。
import { computed, onMounted } from 'vue'
import { History as HistoryIcon, RotateCcw } from 'lucide-vue-next'
import {
  editor,
  loadVersions,
  previewVersion,
  restoreVersion,
  restoringVersion,
  versionPreview,
  versions,
  versionsLoading
} from '../src/store/detail'
import { diffLines, diffStats } from '../src/diff'
import BaseButton from './base/BaseButton.vue'
import AppEmpty from './base/AppEmpty.vue'

const DIFF_CLS: Record<string, string> = {
  same: 'text-ink-dim',
  add: 'text-ok bg-ok/8',
  del: 'text-danger bg-danger/8'
}

/**
 * 差异方向 = 「还原后会怎么变」：左 = 当前编辑器内容，右 = 历史版本。
 * （反过来读成"从这版到现在的改动"也行，但用户此刻的决策是"要不要还原"，+/- 要对上这个动作）
 */
const diff = computed(() => {
  if (!versionPreview.value) return []
  return diffLines(editor?.getValue() ?? '', versionPreview.value.code)
})
const stats = computed(() => diffStats(diff.value))

function tsLabel(ts: string): string {
  // 20260929-231500-ab12cd → 2026-09-29 23:15:00
  const m = /^(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/.exec(ts)
  return m ? `${m[1]}-${m[2]}-${m[3]} ${m[4]}:${m[5]}:${m[6]}` : ts
}

onMounted(() => {
  void loadVersions()
})
</script>

<template>
  <div class="flex flex-col min-h-0 flex-1" data-testid="versions-panel">
    <div v-if="versionsLoading" class="px-3 py-2 text-caption text-ink-mute">读取编辑历史…</div>
    <template v-else-if="versions.length === 0">
      <AppEmpty title="暂无历史版本" description="保存前会自动留档，可随时回到上一版" />
    </template>
    <template v-else>
      <ul class="m-0 p-0 list-none overflow-y-auto max-h-[40%] shrink-0 border-b border-line-hairline">
        <li v-for="v in versions" :key="v.ts">
          <button
            type="button"
            class="w-full text-left px-3 py-1.5 bg-transparent border-0 cursor-pointer font-sans text-caption text-ink-dim hover:text-ink transition-colors dur-fast"
            :class="{ 'text-ink bg-inset': versionPreview?.ts === v.ts }"
            :data-testid="`version-${v.ts}`"
            @click="previewVersion(v.ts)"
          >
            <span class="inline-flex items-center gap-1.5">
              <HistoryIcon :size="12" :stroke-width="1.5" />
              {{ tsLabel(v.ts) }}
            </span>
            <span class="ml-2 text-ink-mute tabular-nums">{{ (v.bytes / 1024).toFixed(1) }}KB</span>
          </button>
        </li>
      </ul>

      <div v-if="versionPreview" class="flex flex-col min-h-0 flex-1" data-testid="version-diff">
        <div class="flex items-center gap-2 px-3 py-1.5 shrink-0">
          <span class="text-caption text-ink-mute">
            还原后将：<span class="text-ok">+{{ stats.added }}</span>
            <span class="ml-1 text-danger">-{{ stats.removed }}</span>
          </span>
          <BaseButton
            class="ml-auto"
            :loading="restoringVersion"
            data-testid="version-restore"
            @click="restoreVersion(versionPreview.ts)"
          >
            <RotateCcw :size="12" /> 还原此版本
          </BaseButton>
        </div>
        <pre class="m-0 flex-1 overflow-auto px-3 pb-2 font-code text-caption leading-[1.6]"><code
          ><span
            v-for="(line, i) in diff"
            :key="i"
            :class="DIFF_CLS[line.kind]"
            class="block whitespace-pre"
          >{{ line.kind === 'add' ? '+' : line.kind === 'del' ? '-' : ' ' }}{{ line.text }}</span></code></pre>
      </div>
      <p v-else class="m-0 px-3 py-2 text-caption text-ink-mute">选择一个版本查看与当前内容的差异</p>
    </template>
  </div>
</template>
