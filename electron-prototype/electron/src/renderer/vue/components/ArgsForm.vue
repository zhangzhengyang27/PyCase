<script setup lang="ts">
// ArgsForm：参数表单（渲染 / 收集 / 历史参数回填）
// 收集与回填语义从旧 args-form.ts 的 collectArgsFromForm / applyArgsToForm 移植：
// - 收集：布尔开关按 checked 推 flag；其余非空值按位置/选项展开
// - 回填：-开头 token 匹配 spec.flags（布尔开关勾选，其余取下一个 token），非 - 按位置顺序
import { reactive, watch } from 'vue'
import {
  argsLoading,
  currentArgs,
  pendingBackfillTokens,
  registerArgsCollector,
  requiredArgsMissing,
  type ArgSpec
} from '../store'

const ARG_FIELD_CLS = 'flex flex-col gap-1 min-w-[160px] flex-1'
const ARG_FIELD_CHECKBOX_CLS = 'flex flex-row items-center gap-2 flex-1'
const ARG_LABEL_CLS = 'text-[11px] font-[590] text-ink-mute font-mono flex items-center gap-2 lowercase tracking-[0.01em]'
const ARG_INPUT_CLS =
  'px-2 py-1 bg-page border border-line rounded-md text-ink text-[12px] font-mono outline-none transition-[border-color,box-shadow] duration-[120ms] hover:border-line-strong focus:border-accent focus:shadow-elev-focus placeholder:text-ink-faint'
const ARG_CHECKBOX_CLS = 'w-4 h-4 accent-accent cursor-pointer rounded'
const ARG_REQUIRED_CLS = 'text-danger'
const ARG_HELP_CLS = 'text-[10px] text-ink-faint font-sans normal-case tracking-normal'

// 字段值：与 currentArgs 按下标对齐；布尔字段值为 boolean，其余为 string
const values = reactive<{ list: Array<string | boolean> }>({ list: [] })

function isBool(spec: ArgSpec): boolean {
  return spec.type === 'bool' || spec.action === 'store_true' || spec.action === 'store_false'
}

watch(
  currentArgs,
  (specs) => {
    values.list = specs.map((spec) => {
      if (isBool(spec)) return spec.action === 'store_false' ? spec.default !== false : spec.default === true
      return spec.default !== undefined && spec.default !== null ? String(spec.default) : ''
    })
    // 历史重跑的回填令牌：参数装载完成后消费
    const tokens = pendingBackfillTokens.value
    if (tokens) {
      pendingBackfillTokens.value = null
      applyTokens(tokens)
    }
  },
  { immediate: true }
)

function applyTokens(tokens: string[]): void {
  const specs = currentArgs.value
  const positionalIdx: number[] = []
  specs.forEach((spec, i) => {
    if (spec.is_positional) positionalIdx.push(i)
  })
  let posIdx = 0
  for (let i = 0; i < tokens.length; i++) {
    const token = String(tokens[i] ?? '')
    if (!token) continue
    if (token.startsWith('-')) {
      const fieldIdx = specs.findIndex(
        (spec) => Array.isArray(spec.flags) && spec.flags.includes(token)
      )
      if (fieldIdx < 0) continue
      const spec = specs[fieldIdx]
      if (isBool(spec)) {
        const isStoreTrue = spec.action === 'store_true'
        values.list[fieldIdx] = isStoreTrue
      } else {
        const next = tokens[i + 1]
        if (next !== undefined && !String(next).startsWith('-')) {
          values.list[fieldIdx] = String(next)
          i++
        }
      }
    } else {
      const fieldIdx = positionalIdx[posIdx++]
      if (fieldIdx !== undefined) values.list[fieldIdx] = token
    }
  }
}

function collectArgs(): string[] {
  const args: string[] = []
  currentArgs.value.forEach((spec, idx) => {
    if (!spec) return
    if (isBool(spec)) {
      const checked = values.list[idx] === true
      const isStoreTrue = spec.action === 'store_true'
      const isStoreFalse = spec.action === 'store_false'
      if (isStoreTrue && checked) args.push(spec.flags[0] || `--${spec.dest}`)
      if (isStoreFalse && !checked) args.push(spec.flags[0] || `--${spec.dest}`)
    } else {
      const value = String(values.list[idx] ?? '').trim()
      if (value === '') return
      if (spec.is_positional) args.push(value)
      else args.push(spec.flags[0] || `--${spec.dest.replace(/_/g, '-')}`, value)
    }
  })
  return args
}

registerArgsCollector(collectArgs)
</script>

<template>
  <div v-if="argsLoading" class="px-3 py-2 text-[11px] text-ink-faint">解析参数中…</div>
  <template v-else-if="currentArgs.length > 0">
    <div class="px-3 pt-2 pb-3 flex flex-wrap gap-x-5 gap-y-3 border-t border-line-subtle">
      <div v-for="(spec, idx) in currentArgs" :key="spec.dest + idx" :class="isBool(spec) ? ARG_FIELD_CHECKBOX_CLS : ARG_FIELD_CLS">
        <!-- 布尔开关 -->
        <template v-if="isBool(spec)">
          <input :id="`arg-${idx}`" v-model="values.list[idx]" type="checkbox" :class="ARG_CHECKBOX_CLS" />
          <label :for="`arg-${idx}`" :class="`${ARG_LABEL_CLS} cursor-pointer`">
            {{ spec.name }} <span v-if="spec.required" :class="ARG_REQUIRED_CLS">*</span>
            <span v-if="spec.help" :class="ARG_HELP_CLS">{{ spec.help }}</span>
          </label>
        </template>
        <!-- 文本 / 数字 / 下拉 -->
        <template v-else>
          <label :for="`arg-${idx}`" :class="ARG_LABEL_CLS">
            {{ spec.name }} <span v-if="spec.required" :class="ARG_REQUIRED_CLS">*</span>
            <span v-if="spec.help" :class="ARG_HELP_CLS">{{ spec.help }}</span>
          </label>
          <select
            v-if="spec.choices && spec.choices.length > 0"
            :id="`arg-${idx}`"
            v-model="values.list[idx]"
            :class="ARG_INPUT_CLS"
          >
            <option v-for="choice in spec.choices" :key="String(choice)" :value="String(choice)">{{ String(choice) }}</option>
          </select>
          <input
            v-else
            :id="`arg-${idx}`"
            v-model="values.list[idx]"
            :type="spec.type === 'int' || spec.type === 'float' ? 'number' : 'text'"
            :step="spec.type === 'int' ? '1' : spec.type === 'float' ? 'any' : undefined"
            :class="ARG_INPUT_CLS"
            :placeholder="spec.metavar || spec.dest"
          />
        </template>
      </div>
      <span v-if="requiredArgsMissing" class="text-[11px] text-danger self-center">存在必填参数，请填写后再运行</span>
    </div>
  </template>
</template>
