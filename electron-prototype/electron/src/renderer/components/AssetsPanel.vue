<script setup lang="ts">
// AssetsPanel：资源上传 / 列举 / 删除（上传写入示例运行目录，脚本可按文件名引用）
// 删除确认由原生 window.confirm 改为 AppModal；上传钮改用 BaseButton。
import { ref } from 'vue'
import { FileText, Image as ImageIcon, Upload } from 'lucide-vue-next'
import { assets, assetsLoading, deleteAsset, uploadAssets } from '../src/store/assets'
import { selectedId } from '../src/store/detail'
import { formatFileSize } from '../src/utils'
import AppModal from './base/AppModal.vue'
import BaseButton from './base/BaseButton.vue'

const GROUPS = [
  { label: '图片', image: true },
  { label: '文档', image: false }
] as const

const fileInput = ref<HTMLInputElement | null>(null)
const confirmName = ref<string | null>(null)

function onPickFiles(e: Event): void {
  const input = e.target as HTMLInputElement
  const files = Array.from(input.files || [])
  input.value = ''
  if (selectedId.value && files.length) void uploadAssets(selectedId.value, files)
}

function onRemove(filename: string): void {
  confirmName.value = filename
}

async function doRemove(): Promise<void> {
  const filename = confirmName.value
  confirmName.value = null
  if (filename) await deleteAsset(filename)
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
      <BaseButton variant="primary" :disabled="assetsLoading || !selectedId" @click="fileInput?.click()">
        <Upload :size="13" /> 上传图片 / 文档
      </BaseButton>
      <span class="text-caption text-ink-mute">上传后示例可在运行目录直接按文件名引用处理</span>
    </div>
    <div v-if="assets.length === 0" class="mt-3 text-ink-mute text-control">尚未上传资源</div>
    <div v-else class="mt-2">
      <template v-for="group in GROUPS" :key="group.label">
        <template v-if="assets.some((a) => a.is_image === group.image)">
          <div class="text-caption text-ink-mute mt-2 mb-1">{{ group.label }}</div>
          <div
            v-for="a in assets.filter((a) => a.is_image === group.image)"
            :key="a.filename"
            class="flex items-center gap-2 px-2 py-1.5 border-b border-line-subtle"
          >
            <component :is="a.is_image ? ImageIcon : FileText" :size="13" class="shrink-0 text-ink-faint" />
            <span class="text-control text-ink-dim truncate flex-1" :title="a.filename">{{ a.filename }}</span>
            <span class="text-caption text-ink-mute shrink-0">{{ formatFileSize(a.size) }}</span>
            <button
              class="shrink-0 px-2 py-0.5 text-caption border border-line-subtle rounded-control bg-transparent text-ink-mute cursor-pointer hover:text-danger hover:border-danger"
              @click="onRemove(a.filename)"
            >
              删除
            </button>
          </div>
        </template>
      </template>
    </div>

    <!-- 删除确认 -->
    <AppModal v-if="confirmName" title="删除资源" @close="confirmName = null">
      <p class="text-control text-ink-dim leading-[1.6]">
        确定删除 <span class="font-mono text-ink">{{ confirmName }}</span
        >？该操作不可撤销。
      </p>
      <template #footer>
        <BaseButton @click="confirmName = null">取消</BaseButton>
        <BaseButton variant="danger" @click="doRemove()">删除</BaseButton>
      </template>
    </AppModal>
  </div>
</template>
