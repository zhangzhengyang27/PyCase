<script setup lang="ts">
// ImportWizardModal：导入用户示例目录为集合（三步：选目录 → 预览 → 结果）。
// 骨架照 AISettingsModal（store 可见性 + watch 复位），列表行样式照 CommandPalette。
import { computed, ref, watch } from 'vue'
import { CheckCircle2, FolderOpen } from 'lucide-vue-next'
import { closeImportWizard, importWizardOpen, loadAll } from '../store'
import { pushToast } from '../toast'
import { api } from '../src/sidecar-client'
import { formatFileSize } from '../src/utils'
import AppModal from './base/AppModal.vue'
import BaseButton from './base/BaseButton.vue'
import BaseInput from './base/BaseInput.vue'

type Step = 'pick' | 'preview' | 'done'

interface PreviewFile {
  id: string
  name: string
  tags: string[]
  requirements: string[]
  bytes: number
}
interface SkippedFile {
  file: string
  reason: string
}

const step = ref<Step>('pick')
const dirPath = ref('')
const collName = ref('')
const scanning = ref(false)
const importing = ref(false)
const scanError = ref('')
const files = ref<PreviewFile[]>([])
const skipped = ref<SkippedFile[]>([])
const result = ref<{ imported: number; skippedCount: number; collection: string | null } | null>(null)

const canScan = computed(() => !!dirPath.value && !scanning.value)
const title = computed(() => (step.value === 'pick' ? '导入示例目录' : step.value === 'preview' ? '确认导入' : '导入完成'))

watch(importWizardOpen, (open) => {
  if (open) reset()
})

function reset(): void {
  step.value = 'pick'
  dirPath.value = ''
  collName.value = ''
  scanning.value = false
  importing.value = false
  scanError.value = ''
  files.value = []
  skipped.value = []
  result.value = null
}

async function pickDirectory(): Promise<void> {
  const res = (await api.pickDirectory()) as { canceled: boolean; path?: string }
  if (res.canceled || !res.path) return
  dirPath.value = res.path
  if (!collName.value) collName.value = res.path.split('/').filter(Boolean).pop() || ''
  await scan()
}

async function scan(): Promise<void> {
  if (!canScan.value) return
  scanning.value = true
  scanError.value = ''
  try {
    const res = (await api.scanImportSource(dirPath.value)) as {
      total: number
      files: PreviewFile[]
      skipped: SkippedFile[]
    }
    files.value = res.files || []
    skipped.value = res.skipped || []
    if (files.value.length === 0) {
      scanError.value = '该目录下没有可导入的 .py 文件'
      return
    }
    step.value = 'preview'
  } catch (err) {
    scanError.value = (err as Error).message
  } finally {
    scanning.value = false
  }
}

async function runImport(): Promise<void> {
  importing.value = true
  try {
    const res = (await api.importExamples({ sourcePath: dirPath.value, name: collName.value || undefined })) as {
      imported: number
      skipped: SkippedFile[]
      collection: string | null
    }
    result.value = { imported: res.imported, skippedCount: (res.skipped || []).length, collection: res.collection }
    await loadAll()
    pushToast('success', `已导入 ${res.imported} 个示例到「${res.collection || collName.value}」`)
    step.value = 'done'
  } catch (err) {
    pushToast('error', `导入失败: ${(err as Error).message}`)
  } finally {
    importing.value = false
  }
}
</script>

<template>
  <AppModal v-if="importWizardOpen" :title="title" width="560px" @close="closeImportWizard()">
    <!-- 第 1 步：选择目录 -->
    <div v-if="step === 'pick'" class="flex flex-col gap-3">
      <p class="m-0 text-control text-ink-dim leading-[1.6]">
        选择一个包含 Python 脚本的目录，扫描后导入为「我的示例集合」。内置示例库不受影响，导入的示例可随时在详情页删除。
      </p>
      <div class="flex items-center gap-2">
        <BaseButton :disabled="scanning" @click="pickDirectory()">
          <FolderOpen :size="14" /> 选择目录…
        </BaseButton>
        <span class="text-caption text-ink-mute truncate flex-1" :title="dirPath">{{ dirPath || '尚未选择目录' }}</span>
      </div>
      <label class="flex flex-col gap-1.5 text-control text-ink-dim">
        集合名称
        <BaseInput v-model="collName" placeholder="默认使用目录名" />
      </label>
      <p v-if="scanError" class="m-0 text-control text-danger">{{ scanError }}</p>
      <p v-if="scanning" class="m-0 text-control text-ink-mute">正在扫描目录…</p>
    </div>

    <!-- 第 2 步：预览确认 -->
    <div v-else-if="step === 'preview'" class="flex flex-col gap-3">
      <p class="m-0 text-control text-ink-dim">
        扫描到 <strong class="text-ink">{{ files.length }}</strong> 个可导入的 .py 文件
        <span v-if="skipped.length">，跳过 {{ skipped.length }} 个（空文件 / 缓存目录）</span>。
        与现有示例同名的 id 会自动加后缀，不会覆盖内置库。
      </p>
      <div class="max-h-[320px] overflow-y-auto border border-line-hairline rounded-card divide-y divide-line-hairline">
        <div v-for="f in files" :key="f.id" class="flex items-center gap-2.5 h-9 px-2.5 text-control">
          <span class="font-mono text-[11px] text-ink truncate flex-1" :title="f.id">{{ f.id }}</span>
          <span
            v-for="req in f.requirements.slice(0, 2)"
            :key="req"
            class="inline-flex items-center gap-1 shrink-0 text-caption text-warn"
            >{{ req }}</span
          >
          <span class="text-caption text-ink-mute font-mono shrink-0">{{ formatFileSize(f.bytes) }}</span>
        </div>
      </div>
    </div>

    <!-- 第 3 步：结果 -->
    <div v-else class="flex flex-col items-center gap-3 py-4">
      <CheckCircle2 :size="36" class="text-ok" />
      <p class="m-0 text-body font-semibold text-ink">已导入 {{ result?.imported }} 个示例</p>
      <p class="m-0 text-control text-ink-dim">
        集合「{{ result?.collection || collName }}」已加入画廊
        <span v-if="result?.skippedCount">，跳过 {{ result?.skippedCount }} 个文件</span>。
      </p>
    </div>

    <template #footer>
      <template v-if="step === 'pick'">
        <BaseButton variant="ghost" @click="closeImportWizard()">取消</BaseButton>
        <BaseButton :disabled="!canScan" @click="scan()">{{ scanning ? '扫描中…' : '扫描并预览' }}</BaseButton>
      </template>
      <template v-else-if="step === 'preview'">
        <BaseButton variant="ghost" :disabled="importing" @click="step = 'pick'">上一步</BaseButton>
        <BaseButton :disabled="importing" @click="runImport()">
          {{ importing ? '导入中…' : `导入 ${files.length} 个示例` }}
        </BaseButton>
      </template>
      <template v-else>
        <BaseButton @click="closeImportWizard()">完成</BaseButton>
      </template>
    </template>
  </AppModal>
</template>
