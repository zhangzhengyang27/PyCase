<script setup lang="ts">
// SettingsModal：设置弹窗（App.vue 侧栏「设置」入口，原 AI 设置弹窗扩展而来）。
// 分区：AI 代码解释（key 存 userData，前端不接触明文）+ 运行（超时时长）+
// 安全（高危确认开关，即 HighRiskConfirmModal「不再提示」的恢复入口）+
// 存储（工作区占用与两档清理 + v1 旧根回收；数据来自 sidecar storage_report）。
// 字段输入即时校验，保存时全量拦截，校验失败聚焦第一个错误字段。
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { aiSettings, aiSettingsOpen, closeAISettings } from '../src/store/ai'
import { runTimeout, setRunTimeout, setSkipHighRiskConfirm, skipHighRiskConfirm } from '../src/store/prefs'
import {
  cleanWorkspace,
  loadStorageReport,
  reclaimLegacyCache,
  storageBusy,
  storageLoading,
  storageReport
} from '../src/store/storage'
import { pushToast } from '../toast'
import { api } from '../src/sidecar-client'
import AppModal from './base/AppModal.vue'
import BaseButton from './base/BaseButton.vue'
import BaseInput from './base/BaseInput.vue'
import BaseSelect from './base/BaseSelect.vue'

const key = ref('')
const model = ref(aiSettings.model)
const baseUrl = ref(aiSettings.baseUrl)
const saving = ref(false)

const touched = reactive({ model: false, baseUrl: false, apiKey: false })
const attempted = ref(false)

const FIELD_IDS = { model: 'setting-model', baseUrl: 'setting-baseurl', apiKey: 'setting-apikey' } as const

// 每次打开时同步当前设置并复位校验状态
watch(aiSettingsOpen, (open) => {
  if (open) {
    key.value = ''
    model.value = aiSettings.model
    baseUrl.value = aiSettings.baseUrl
    touched.model = touched.baseUrl = touched.apiKey = false
    attempted.value = false
    // 存储分区：打开设置时拉一次占用（数据在 sidecar 侧，前端不缓存）
    void loadStorageReport()
  }
}, { immediate: true })

const MB = 1024 * 1024
const mbText = (bytes: number): string => `${(bytes / MB).toFixed(1)}MB`
const storagePercent = computed(() => {
  const ws = storageReport.value?.workspace
  if (!ws || !ws.max_bytes) return 0
  return Math.min(100, Math.round((ws.bytes / ws.max_bytes) * 100))
})
/** 清理确认：两档语义不同，必须让用户看到差别（clean 保留上传资源与运行产物） */
const cleanMode = ref<'' | 'clean' | 'all'>('')
const legacyConfirmOpen = ref(false)
const cleanableCount = computed(
  () => storageReport.value?.workspace.entries.filter((e) => !e.has_assets).length ?? 0
)

async function confirmClean(): Promise<void> {
  const mode = cleanMode.value || 'clean'
  cleanMode.value = ''
  await cleanWorkspace(mode)
}

async function confirmLegacy(): Promise<void> {
  legacyConfirmOpen.value = false
  await reclaimLegacyCache()
}

const errors = computed(() => ({
  model: model.value.trim() ? '' : '请输入模型名（默认 deepseek-chat）',
  baseUrl: !baseUrl.value.trim()
    ? '请输入 Base URL'
    : /^https?:\/\/\S+\.\S+/.test(baseUrl.value.trim())
      ? ''
      : '需为 http(s):// 开头的合法地址',
  apiKey: !key.value || key.value.length >= 8 ? '' : 'Key 至少 8 个字符'
}))
const visibleErrors = computed(() => ({
  model: touched.model || attempted.value ? errors.value.model : '',
  baseUrl: touched.baseUrl || attempted.value ? errors.value.baseUrl : '',
  apiKey: touched.apiKey || attempted.value ? errors.value.apiKey : ''
}))
const hasErrors = computed(() => Object.values(errors.value).some(Boolean))

// 高危确认开关：读 store（loadAll 时从 safetyPrefs 载入），写入走统一 setter 持久化
const highRiskConfirm = computed({
  get: () => !skipHighRiskConfirm.value,
  set: (v: boolean) => setSkipHighRiskConfirm(!v)
})

function onInput(field: 'model' | 'baseUrl' | 'apiKey', value: string): void {
  touched[field] = true
  if (field === 'model') model.value = value
  else if (field === 'baseUrl') baseUrl.value = value
  else key.value = value
}

async function save(): Promise<void> {
  attempted.value = true
  if (hasErrors.value) {
    // 聚焦第一个未通过的字段，键盘/读屏用户不必扫码找错
    await nextTick()
    const first = (['model', 'baseUrl', 'apiKey'] as const).find((f) => errors.value[f])
    if (first) document.getElementById(FIELD_IDS[first])?.focus()
    return
  }
  saving.value = true
  const patch: Record<string, unknown> = {
    model: model.value.trim() || 'deepseek-chat',
    baseUrl: baseUrl.value.trim() || 'https://api.deepseek.com'
  }
  if (key.value) patch.apiKey = key.value // 空字符串不覆盖（主进程会清除 ""，这里只在有值时传）
  try {
    const res = (await api.aiSetSettings(patch)) as { hasKey?: boolean }
    aiSettings.hasKey = !!res.hasKey
    aiSettings.model = patch.model as string
    aiSettings.baseUrl = patch.baseUrl as string
    pushToast('success', 'AI 设置已保存')
    closeAISettings()
  } catch (err) {
    pushToast('error', '保存 AI 设置失败：' + (err as Error).message)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <AppModal v-if="aiSettingsOpen" title="设置" width="440px" @close="closeAISettings()">
    <div class="flex flex-col gap-3.5">
      <section>
        <h3 class="m-0 mb-2 text-control font-semibold text-ink">AI 代码解释</h3>
        <p class="text-control text-ink-mute mb-3 leading-[1.5]">
          API Key 仅保存在本机 userData，不会写入代码、日志或上传。请求会发送到 DeepSeek 服务器。
        </p>
        <div class="flex flex-col gap-3.5">
          <label class="flex flex-col gap-1.5">
            <span class="text-caption font-semibold text-ink-dim">模型 <span class="text-danger">*</span></span>
            <BaseInput
              :id="FIELD_IDS.model"
              :model-value="model"
              placeholder="deepseek-chat"
              :spellcheck="false"
              :error="visibleErrors.model"
              @update:model-value="onInput('model', $event)"
            />
          </label>
          <label class="flex flex-col gap-1.5">
            <span class="text-caption font-semibold text-ink-dim">Base URL <span class="text-danger">*</span></span>
            <BaseInput
              :id="FIELD_IDS.baseUrl"
              :model-value="baseUrl"
              type="url"
              placeholder="https://api.deepseek.com"
              :spellcheck="false"
              :error="visibleErrors.baseUrl"
              @update:model-value="onInput('baseUrl', $event)"
            />
          </label>
          <label class="flex flex-col gap-1.5">
            <span class="text-caption font-semibold text-ink-dim">API Key（已配置时留空保持不变）</span>
            <BaseInput
              :id="FIELD_IDS.apiKey"
              :model-value="key"
              type="password"
              show-password
              placeholder="sk-..."
              autocomplete="off"
              :spellcheck="false"
              :error="visibleErrors.apiKey"
              @update:model-value="onInput('apiKey', $event)"
            />
          </label>
        </div>
      </section>

      <section class="border-t border-line-hairline pt-3.5">
        <h3 class="m-0 mb-2 text-control font-semibold text-ink">运行</h3>
        <div class="flex items-center gap-2">
          <span class="shrink-0 text-control text-ink-dim">超时</span>
          <BaseSelect
            class="w-[130px]"
            title="运行超时时长"
            aria-label="运行超时时长"
            :model-value="String(runTimeout)"
            @update:model-value="setRunTimeout(Number($event))"
          >
            <option value="15">15 秒</option>
            <option value="30">30 秒（默认）</option>
            <option value="60">60 秒</option>
            <option value="120">2 分钟</option>
            <option value="300">5 分钟</option>
          </BaseSelect>
        </div>
        <p class="m-0 mt-1.5 text-caption text-ink-mute leading-[1.5]">
          运行超过该时长将被强制终止。长动画、游戏类示例（Pygame）建议放宽。
        </p>
      </section>

      <section class="border-t border-line-hairline pt-3.5" data-testid="settings-storage">
        <h3 class="m-0 mb-2 text-control font-semibold text-ink">存储</h3>
        <p class="m-0 mb-2 text-caption text-ink-mute leading-[1.5]">
          运行示例会在本地生成工作区副本。清理只动副本，不改示例源码。
        </p>
        <div v-if="storageReport" class="flex flex-col gap-1.5">
          <div class="flex items-baseline justify-between text-control">
            <span class="text-ink-dim">示例工作区</span>
            <span class="text-ink tabular-nums" data-testid="storage-workspace">
              {{ mbText(storageReport.workspace.bytes) }} / {{ mbText(storageReport.workspace.max_bytes) }}
            </span>
          </div>
          <div class="h-1 rounded-full bg-fill-subtle overflow-hidden" role="progressbar"
               :aria-valuenow="storagePercent" aria-valuemin="0" aria-valuemax="100">
            <div class="h-full bg-accent" :style="{ width: storagePercent + '%' }"></div>
          </div>
          <div class="flex items-baseline justify-between text-caption text-ink-mute">
            <span>{{ storageReport.workspace.entries.length }} 个工作区</span>
            <span v-if="storageReport.workspace.asset_entries > 0" data-testid="storage-assets">
              {{ storageReport.workspace.asset_entries }} 个含上传资源/运行产物
            </span>
          </div>
          <div v-if="storageReport.legacy.entries > 0" class="flex items-baseline justify-between text-caption text-ink-mute">
            <span>旧版缓存（v1 遗留）</span>
            <span data-testid="storage-legacy">{{ mbText(storageReport.legacy.bytes) }} · {{ storageReport.legacy.entries }} 项</span>
          </div>
          <div v-if="storageReport.history.bytes > 0" class="flex items-baseline justify-between text-caption text-ink-mute">
            <span>编辑历史（可恢复编辑的快照）</span>
            <span data-testid="storage-history">{{ mbText(storageReport.history.bytes) }}</span>
          </div>
        </div>
        <p v-else-if="storageLoading" class="m-0 text-caption text-ink-mute">正在读取占用…</p>
        <p v-else class="m-0 text-caption text-ink-mute">暂时读不到占用信息（sidecar 未就绪）</p>
        <div class="flex flex-wrap gap-2 mt-2.5">
          <BaseButton :loading="storageBusy === 'clean'" @click="cleanMode = 'clean'">
            清理干净工作区
          </BaseButton>
          <BaseButton v-if="storageReport && storageReport.legacy.entries > 0"
                      :loading="storageBusy === 'legacy'" @click="legacyConfirmOpen = true">
            回收旧版缓存
          </BaseButton>
          <BaseButton variant="danger" :loading="storageBusy === 'all'"
                      @click="cleanMode = 'all'" data-testid="storage-clean-all">
            全部清理
          </BaseButton>
        </div>
      </section>

      <section class="border-t border-line-hairline pt-3.5">
        <h3 class="m-0 mb-2 text-control font-semibold text-ink">安全</h3>
        <label class="flex items-center gap-2 text-control text-ink-dim cursor-pointer select-none">
          <input v-model="highRiskConfirm" type="checkbox" class="w-4 h-4 accent-accent cursor-pointer rounded" />
          高危示例运行前弹出确认
        </label>
        <p class="m-0 mt-1.5 text-caption text-ink-mute leading-[1.5]">
          关闭后，含高危操作（系统命令 / 文件删除等）的示例将不经确认直接运行。
        </p>
      </section>
    </div>
    <template #footer>
      <BaseButton @click="closeAISettings()">取消</BaseButton>
      <BaseButton variant="primary" :loading="saving" @click="save()">保存</BaseButton>
    </template>
  </AppModal>

  <!-- 清理确认：两档语义差别要讲清（clean 保留上传资源与运行产物；all 连资产一起删） -->
  <AppModal v-if="cleanMode" title="清理工作区" :max-width="420" @close="cleanMode = ''">
    <p class="m-0 text-control text-ink-dim leading-[1.6]">
      <template v-if="cleanMode === 'clean'">
        将删除<strong class="text-ink">{{ cleanableCount }} 个干净工作区副本</strong>，
        保留含上传资源/运行产物的条目；示例源码不受影响，下次运行会重新生成副本。
      </template>
      <template v-else>
        将删除<strong class="text-ink text-danger">全部 {{ storageReport?.workspace.entries.length ?? 0 }} 个工作区副本</strong>，
        <strong class="text-ink">包含你上传的资源与运行产物</strong>——此操作不可撤销。
      </template>
    </p>
    <template #footer>
      <BaseButton @click="cleanMode = ''">取消</BaseButton>
      <BaseButton :variant="cleanMode === 'all' ? 'danger' : 'primary'" @click="confirmClean()">
        {{ cleanMode === 'all' ? '全部清理' : '清理' }}
      </BaseButton>
    </template>
  </AppModal>

  <AppModal v-if="legacyConfirmOpen" title="回收旧版缓存" :max-width="420" @close="legacyConfirmOpen = false">
    <p class="m-0 text-control text-ink-dim leading-[1.6]">
      将回收旧版（v1）遗留的
      <strong class="text-ink">{{ storageReport?.legacy.entries ?? 0 }} 项</strong>
      缓存（约 {{ mbText(storageReport?.legacy.bytes ?? 0) }}）。这些目录是旧版本的按示例缓存，
      当前版本不再使用；回收不影响示例源码与当前工作区。
    </p>
    <template #footer>
      <BaseButton @click="legacyConfirmOpen = false">取消</BaseButton>
      <BaseButton variant="primary" @click="confirmLegacy()">回收</BaseButton>
    </template>
  </AppModal>
</template>
