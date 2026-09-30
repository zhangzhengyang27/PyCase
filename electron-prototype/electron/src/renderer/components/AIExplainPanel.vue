<script setup lang="ts">
// AIExplainPanel：AI 代码解释侧栏（流式输出 / 停止 / 复制）
// 视觉对齐设计规范 v1：rounded-panel + shadow-elev-3，尺寸/字号走令牌。
import { X } from 'lucide-vue-next'
import { copyAIOutput, closeAIPanel, stopAI, aiOutputText, aiStatus, aiStatusError, aiShowStop } from '../src/store/ai'

const PANEL_CLS =
  'fixed top-[52px] right-4 w-[420px] max-w-[40vw] h-[calc(100vh-92px)] bg-panel border border-line-subtle rounded-card shadow-elev-3 flex flex-col z-[900] animate-modal-in'
const BTN_CLS =
  'border border-line-subtle bg-transparent text-ink-dim rounded-control px-2 h-6 inline-flex items-center text-caption cursor-pointer hover:text-ink hover:bg-hover'
</script>

<template>
  <div :class="PANEL_CLS">
    <div
      class="flex items-center justify-between px-3.5 py-2.5 border-b border-line-subtle font-semibold text-body shrink-0"
    >
      <span>AI 代码解释（DeepSeek）</span>
      <div class="flex gap-1.5">
        <button v-show="aiShowStop" :class="BTN_CLS" title="停止解释" @click="stopAI()">停止</button>
        <button :class="BTN_CLS" title="复制解释" @click="copyAIOutput()">复制</button>
        <button
          class="w-6 h-6 inline-flex items-center justify-center border-0 bg-transparent rounded-control text-ink-mute cursor-pointer hover:text-ink hover:bg-hover"
          title="关闭"
          aria-label="关闭 AI 解释面板"
          @click="closeAIPanel()"
        >
          <X :size="13" />
        </button>
      </div>
    </div>
    <div
      class="px-3.5 py-1.5 text-caption border-b border-line-subtle shrink-0"
      :class="aiStatusError ? 'text-danger' : 'text-ink-mute'"
    >
      {{ aiStatus }}
    </div>
    <div
      class="flex-1 overflow-auto px-3.5 py-3 text-body leading-[1.65] text-ink whitespace-pre-wrap break-words font-sans"
    >
      {{ aiOutputText }}
    </div>
  </div>
</template>
