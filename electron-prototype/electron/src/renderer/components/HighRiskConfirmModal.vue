<script setup lang="ts">
// HighRiskConfirmModal：高危示例运行前二次确认（AppModal 基础件，模板沿用 AssetsPanel 删除确认）
// 明确告知安全边界：子进程隔离不是沙箱，第三方库内部行为不受静态扫描覆盖。
import { computed, ref } from 'vue'
import { ShieldAlert } from 'lucide-vue-next'
import { examples, pendingHighRiskRun, resolveHighRiskRun } from '../store'
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
      <div class="flex items-start gap-2.5 p-3 rounded-control bg-danger-bg text-danger">
        <ShieldAlert :size="18" class="shrink-0 mt-0.5" />
        <div class="text-control leading-[1.6]">
          <p class="m-0 font-[590]">「{{ target.title || target.name }}」包含以下高危操作：</p>
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
      <BaseButton variant="ghost" @click="resolveHighRiskRun(false, false)">取消</BaseButton>
      <BaseButton variant="danger" @click="resolveHighRiskRun(true, skip)">仍要运行</BaseButton>
    </template>
  </AppModal>
</template>
