<script setup lang="ts">
// ToolResultPanel：ToolResult → 结构化渲染（schema 驱动工具的结果区）。
// 四种形态互斥共存：error 出现时只渲染引导文案；primary 大数字；rows 键值行；
// text 等宽文本块；list 批量列表（行尾复制）。
import { ref } from 'vue'
import { Check, Copy } from 'lucide-vue-next'
import { pushToast } from '../../toast'
import type { ToolResult } from '../../src/interactive-tools'

defineProps<{ result: ToolResult }>()

const copiedKey = ref<string | null>(null)
async function copyText(key: string, text: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(text)
    copiedKey.value = key
    pushToast('success', '已复制')
    setTimeout(() => {
      if (copiedKey.value === key) copiedKey.value = null
    }, 1500)
  } catch {
    pushToast('error', '复制失败')
  }
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <div v-if="result.error" class="text-control text-ink-mute pt-6 text-center" data-testid="tool-error">
      {{ result.error }}
    </div>
    <template v-else>
      <div v-if="result.primary" class="text-center pt-1" data-testid="tool-primary">
        <span class="font-semibold text-ink leading-none" style="font-size: 40px">{{ result.primary.value }}</span>
        <span v-if="result.primary.unit" class="text-control text-ink-mute ml-1.5">{{ result.primary.unit }}</span>
      </div>

      <div
        v-if="result.rows?.length"
        class="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-2"
        data-testid="tool-rows"
      >
        <div
          v-for="r in result.rows"
          :key="r.label"
          class="surface-card px-3 py-2 flex items-center justify-between gap-2"
        >
          <span class="text-caption text-ink-mute shrink-0">{{ r.label }}</span>
          <span class="text-control text-ink font-mono truncate" :title="r.value">{{ r.value }}</span>
          <button
            v-if="r.copy"
            class="border-0 bg-transparent text-ink-faint hover:text-accent cursor-pointer shrink-0"
            :aria-label="`复制 ${r.label}`"
            @click="copyText(r.label, r.value)"
          >
            <Check v-if="copiedKey === r.label" :size="13" />
            <Copy v-else :size="13" />
          </button>
        </div>
      </div>

      <pre
        v-if="result.text"
        class="m-0 p-3 surface-card text-control font-mono whitespace-pre-wrap overflow-auto max-h-[320px]"
        data-testid="tool-text"
        >{{ result.text }}</pre>

      <ul v-if="result.list?.length" class="m-0 pl-0 list-none flex flex-col gap-1" data-testid="tool-list">
        <li
          v-for="(item, i) in result.list"
          :key="`${i}-${item}`"
          class="flex items-center gap-2 surface-card px-3 py-1.5"
        >
          <span class="text-control font-mono text-ink flex-1 truncate">{{ item }}</span>
          <button
            class="border-0 bg-transparent text-ink-faint hover:text-accent cursor-pointer shrink-0"
            :aria-label="`复制第 ${i + 1} 项`"
            @click="copyText(String(i), item)"
          >
            <Check v-if="copiedKey === String(i)" :size="13" />
            <Copy v-else :size="13" />
          </button>
        </li>
      </ul>
    </template>
  </div>
</template>
