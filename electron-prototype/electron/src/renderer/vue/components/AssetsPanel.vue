<script setup lang="ts">
// AssetsPanel：资源上传 / 列举 /删除（上传写入示例运行目录，脚本可按文件名引用）
import { ref } from 'vue'
import { assets, assetsLoading, deleteAsset, selectedId, uploadAssets } from '../store'
import { formatFileSize } from '../../src/utils'

const fileInput = ref<HTMLInputElement | null>(null)

function onPickFiles(e: Event): void {
  const input = e.target as HTMLInputElement
  const files = Array.from(input.files || [])
  input.value = ''
  if (selectedId.value && files.length) void uploadAssets(selectedId.value, files)
}

function onRemove(filename: string): void {
  if (window.confirm(`删除资源 ${filename}？`)) void deleteAsset(filename)
}
</script>

<template>
  <div class="p-3 overflow-y-auto h-full">
    <input
      ref="fileInput"
      type="file"
      multiple
      accept="image/*,.pdf,.txt,.csv,.xls,.xlsx,.doc,.docx,.md,.json,.zip,.gif"
      class="hidden"
      @change="onPickFiles"
    />
    <div class="flex items-center gap-2">
      <button
        class="inline-flex items-center gap-1 px-3 py-[5px] border border-accent rounded-md bg-accent text-white text-[12px] font-[510] font-sans cursor-pointer shadow-elev-1 transition-all duration-[120ms] active:scale-[0.97] enabled:hover:bg-accent-hover disabled:opacity-[0.35] disabled:cursor-not-allowed"
        :disabled="assetsLoading || !selectedId"
        @click="fileInput?.click()"
      >
        📤 上传图片 / 文档
      </button>
      <span class="text-[11px] text-ink-mute">上传后示例可在运行目录直接按文件名引用处理</span>
    </div>
    <div v-if="assets.length === 0" class="mt-3 text-ink-mute text-[12px]">尚未上传资源</div>
    <div v-else class="mt-2">
      <template v-for="(group, gi) in [['图片', true], ['文档', false]]" :key="gi">
        <template v-if="assets.some((a) => a.is_image === group[1])">
          <div class="text-[11px] text-ink-mute mt-2 mb-1">{{ group[0] }}</div>
          <div
            v-for="a in assets.filter((a) => a.is_image === group[1])"
            :key="a.filename"
            class="flex items-center gap-2 px-2 py-1.5 border-b border-line-subtle"
          >
            <span>{{ a.is_image ? '🖼️' : '📄' }}</span>
            <span class="text-[12px] text-ink-dim truncate flex-1" :title="a.filename">{{ a.filename }}</span>
            <span class="text-[11px] text-ink-mute shrink-0">{{ formatFileSize(a.size) }}</span>
            <button
              class="shrink-0 px-2 py-0.5 text-[11px] border border-line-subtle rounded-md bg-transparent text-ink-mute cursor-pointer hover:text-danger hover:border-danger"
              @click="onRemove(a.filename)"
            >
              删除
            </button>
          </div>
        </template>
      </template>
    </div>
  </div>
</template>
