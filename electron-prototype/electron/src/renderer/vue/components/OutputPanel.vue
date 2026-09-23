<script setup lang="ts">
// OutputPanel：终端输出（行数上限 + 近底部自动滚动）与结果图片预览下载
// 行数截断与"仅用户停留在底部时才滚底"从旧 output.ts 移植。
import { nextTick, ref, watch } from 'vue'
import { clearOutput, downloadImage, outputDot, outputImages, outputLines, outputTruncated } from '../store'

const viewer = ref<HTMLDivElement | null>(null)
const DOT_CLS: Record<string, string> = {
  idle: 'bg-ink-faint',
  running: 'bg-warn animate-pulse',
  success: 'bg-ok',
  error: 'bg-danger'
}
const LINE_CLS: Record<string, string> = {
  base: 'text-ink-dim',
  system: 'text-ink-faint italic text-[11px]',
  error: 'text-danger',
  success: 'text-ok'
}

// 仅当用户本就停留在底部时才自动滚底（上翻查看历史输出不被拽回）
watch(
  outputLines,
  async () => {
    await nextTick()
    const el = viewer.value
    if (!el) return
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40
    if (nearBottom) el.scrollTop = el.scrollHeight
  },
  { deep: true }
)
</script>

<template>
  <div class="flex-1 min-h-0 flex flex-col">
    <div ref="viewer" class="flex-1 min-h-0 overflow-auto bg-inset px-4 py-3 font-mono text-[12px] leading-[1.6]">
      <div v-if="outputLines.length === 0" class="text-ink-faint text-[11px]">点击「运行」，输出将实时显示在这里</div>
      <div v-if="outputTruncated" class="text-ink-faint italic text-[11px] whitespace-pre-wrap break-all">
        [系统] 输出超过上限，已自动截断，仅保留最近的输出
      </div>
      <div v-for="(line, i) in outputLines" :key="i" class="whitespace-pre-wrap break-all" :class="LINE_CLS[line.cls]">
        {{ line.text }}
      </div>
    </div>
    <div
      v-if="outputImages.length > 0"
      class="shrink-0 max-h-[32vh] border-t border-line-subtle px-4 py-3 bg-[rgba(127,127,127,0.06)] overflow-y-auto"
    >
      <div class="text-[12px] font-[590] text-ink-dim mb-2">运行结果图片</div>
      <div class="grid grid-cols-[repeat(auto-fill,minmax(180px,1fr))] gap-3">
        <figure
          v-for="img in outputImages"
          :key="img.url"
          class="m-0 border border-line-subtle rounded-lg overflow-hidden bg-panel"
        >
          <img :src="img.url" :alt="img.name" loading="lazy" class="block w-full h-[150px] object-contain bg-[#fafafa]" />
          <figcaption class="flex items-center justify-between gap-1.5 px-2 py-1 text-[11px] text-ink-mute">
            <span class="truncate" :title="img.name">{{ img.name }}</span>
            <button
              class="shrink-0 px-2 py-0.5 text-[11px] border border-line-subtle rounded-md bg-panel text-ink-dim cursor-pointer hover:bg-[rgba(94,106,210,0.12)] hover:text-accent"
              type="button"
              @click="downloadImage(img.url, img.name)"
            >
              ⬇ 下载
            </button>
          </figcaption>
        </figure>
      </div>
    </div>
  </div>
</template>
