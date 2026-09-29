<script setup lang="ts">
// OutputPanel：终端输出（行数上限 + 近底部自动滚动）与结果图片预览下载
// surface 决定读取哪个输出汇（detail / runner）；运行中顶部显示不确定进度条。
import { computed, nextTick, ref, watch } from 'vue'
import { Download } from 'lucide-vue-next'
import { downloadImage, isRunning, surfaceState, type OutputSurface } from '../store'

const props = defineProps<{ surface: OutputSurface }>()

const viewer = ref<HTMLDivElement | null>(null)
const state = computed(() => surfaceState(props.surface))
const DOT_CLS: Record<string, string> = {
  idle: 'bg-ink-faint',
  running: 'bg-warn animate-pulse',
  success: 'bg-ok',
  error: 'bg-danger'
}
// 终端行：底/正文用 --text-console（跟随主题），系统提示降到 gutter 级，错误/成功保留语义色
const LINE_CLS: Record<string, string> = {
  base: 'text-console',
  system: 'text-gutter italic text-caption',
  error: 'text-danger',
  success: 'text-ok'
}

// 仅当用户本就停留在底部时才自动滚底（上翻查看历史输出不被拽回）
watch(
  () => state.value.lines.length,
  async () => {
    await nextTick()
    const el = viewer.value
    if (!el) return
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40
    if (nearBottom) el.scrollTop = el.scrollHeight
  }
)
</script>

<template>
  <div class="flex-1 min-h-0 flex flex-col">
    <!-- 运行中：不确定进度条 -->
    <div v-if="isRunning" class="h-0.5 shrink-0 overflow-hidden" role="progressbar" aria-label="示例运行中">
      <div class="h-full w-1/3 rounded-full bg-accent animate-indeterminate"></div>
    </div>
    <div class="flex-1 min-h-0 m-2 rounded-card border border-line-hairline console overflow-hidden flex flex-col">
      <div ref="viewer" class="flex-1 min-h-0 overflow-auto px-3.5 py-3 font-mono text-control">
        <div v-if="state.lines.length === 0" class="text-gutter text-caption">点击「运行」，输出将实时显示在这里</div>
        <div v-if="state.truncated" class="text-gutter italic text-caption whitespace-pre-wrap break-all">
          [系统] 输出超过上限，已自动截断，仅保留最近的输出
        </div>
        <div v-for="(line, i) in state.lines" :key="i" class="whitespace-pre-wrap break-all" :class="LINE_CLS[line.cls]">
          {{ line.text }}
        </div>
      </div>
    </div>
    <div
      v-if="state.images.length > 0"
      class="shrink-0 max-h-[32vh] border-t border-line-hairline px-4 py-3 overflow-y-auto"
    >
      <div class="text-control font-medium text-ink-dim mb-2">运行结果图片</div>
      <div class="grid grid-cols-[repeat(auto-fill,minmax(180px,1fr))] gap-3">
        <figure v-for="img in state.images" :key="img.url" class="m-0 border border-line-hairline rounded-card overflow-hidden bg-panel">
          <img :src="img.url" :alt="img.name" loading="lazy" class="block w-full h-[150px] object-contain bg-page" />
          <figcaption class="flex items-center justify-between gap-1.5 px-2 py-1 text-caption text-ink-mute">
            <span class="truncate" :title="img.name">{{ img.name }}</span>
            <button
              class="shrink-0 inline-flex items-center gap-1 px-2 py-0.5 text-caption border border-line-hairline rounded-control bg-panel text-ink-dim cursor-pointer transition-colors dur-fast hover:bg-hover hover:text-ink"
              type="button"
              @click="downloadImage(img.url, img.name)"
            >
              <Download :size="11" /> 下载
            </button>
          </figcaption>
        </figure>
      </div>
    </div>
  </div>
</template>
