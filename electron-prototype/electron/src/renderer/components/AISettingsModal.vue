<script setup lang="ts">
// SettingsModal：设置弹窗（App.vue 侧栏「设置」入口，原 AI 设置弹窗扩展而来）。
// 分区：AI 代码解释（key 存 userData，前端不接触明文）+ 运行（超时时长）+
// 安全（高危确认开关，即 HighRiskConfirmModal「不再提示」的恢复入口）。
// 字段输入即时校验，保存时全量拦截，校验失败聚焦第一个错误字段。
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { aiSettings, aiSettingsOpen, closeAISettings } from '../src/store/ai'
import { runTimeout, setRunTimeout, setSkipHighRiskConfirm, skipHighRiskConfirm } from '../src/store/prefs'
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
  }
})

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
</template>
