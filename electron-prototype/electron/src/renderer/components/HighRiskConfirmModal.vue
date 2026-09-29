<script setup lang="ts">
// HighRiskConfirmModal：高危示例运行前二次确认（视觉基线 v2 / 页稿板 4）
// mac = 图标 + 中性文字（平面）；win = Fluent InfoBar 语义底；
// 危险按钮用红字而非红色填充；按钮序按平台（mac 主操作最右 / win 最左）。
// 文案明确安全边界：子进程隔离不是沙箱，第三方库内部行为不受静态扫描覆盖。
import { computed, ref } from 'vue'
import { ShieldAlert } from 'lucide-vue-next'
import { examples } from '../src/store/catalog'
import { pendingHighRiskRun } from '../src/store/detail'
import { resolveHighRiskRun } from '../src/store/detail'
import BaseButton from './base/BaseButton.vue'
import AppModal from './base/AppModal.vue'

const skip = ref(false)

const target = computed(() => {
  const pending = pendingHighRiskRun.value
  if (!pending) return null
  return examples.value.find((e) => e.id === pending.id) || null
})
const findings = computed(() => target.value?.risk_findings || [])
</script>

<template>
  <AppModal v-if="pendingHighRiskRun && target" title="运行高危示例" width="480px" @close="resolveHighRiskRun(false, false)">
    <div class="flex flex-col gap-3">
      <div class="alertline">
        <ShieldAlert :size="18" :stroke-width="1.5" />
        <div>
          <p class="m-0 font-semibold text-ink">「{{ target.title || target.name }}」包含以下高危操作：</p>
          <ul class="m-0 mt-1.5 pl-4 space-y-1">
            <li v-for="(f, i) in findings" :key="i">{{ f.description }}</li>
          </ul>
        </div>
      </div>
      <p class="m-0 text-control text-ink-dim leading-[1.6]">
        示例将在独立子进程中运行（30 秒超时、环境变量白名单），但<strong class="text-ink">子进程隔离不是安全沙箱</strong>
        ——反射调用、运行时拼接的命令，以及第三方库内部行为不受静态扫描覆盖。请确认你信任这段代码。
      </p>
      <label class="flex items-center gap-2 text-control text-ink-dim cursor-pointer select-none">
        <input v-model="skip" type="checkbox" class="accent-current" />
        本机不再提示（可在「设置 → 安全」中恢复）
      </label>
    </div>
    <template #footer>
      <div class="d-actions">
        <BaseButton variant="ghost" @click="resolveHighRiskRun(false, false)">取消</BaseButton>
        <BaseButton class="d-primary" variant="danger" @click="resolveHighRiskRun(true, skip)">仍要运行</BaseButton>
      </div>
    </template>
  </AppModal>
</template>
