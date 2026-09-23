// args-form.ts：详情页参数表单（argparse 静态解析结果的渲染与值收集）
// 打开详情页时解析并渲染；无参数整区隐藏；收集值转为命令行参数数组。
// 依赖：els、state（state.ts）、escapeHtml（utils.ts）、api（sidecar-client.ts）

import { els, state } from './state'
import { escapeHtml } from './utils'
import { api } from './sidecar-client'

// ---------------------------------------------------------------------------
// 加载并渲染参数表单（Promise 复用：卡片「运行」与 openDetail 共享同一次解析）
// ---------------------------------------------------------------------------
let _currentLoad: Promise<any[]> | null = null

export function loadAndRenderArgs(exampleId: string): Promise<any[]> {
  if (_currentLoad) return _currentLoad
  _currentLoad = (async () => {
    try {
      const result = await api.parseArgs(exampleId)
      // await 期间用户可能已切换示例：过期响应不得写入 state.currentArgs，
      // 否则新详情页会挂着上一个示例的参数表单（重跑即"用 A 的参数跑 B"）
      if (state.selectedId !== exampleId) return []
      state.currentArgs = result.args || []
    } catch (err) {
      if (state.selectedId !== exampleId) return []
      console.error('解析参数失败:', err)
      state.currentArgs = []
    }
    renderArgsForm(state.currentArgs)
    return state.currentArgs
  })()
  return _currentLoad
}

/** 切换示例时丢弃上一次的解析缓存 */
export function invalidateArgsCache(): void {
  _currentLoad = null
}

/** 是否存在「必填且无默认值」的参数（卡片直接运行时改为指导用户填参） */
export function requiredArgsMissing(args: any[]): boolean {
  return (args || []).some(
    (a) => a.required && a.default === undefined && !(a.action === 'store_true' || a.action === 'store_false')
  )
}

// ---------------------------------------------------------------------------
// 渲染
// ---------------------------------------------------------------------------
// 参数字段 Tailwind 类名（原 style.css .arg-field-* 规则的工具类化）
const ARG_FIELD_CLS = 'arg-field flex flex-col gap-1 min-w-[160px] flex-1'
const ARG_FIELD_CHECKBOX_CLS = 'arg-field checkbox-field flex flex-row items-center gap-2 flex-1'
const ARG_LABEL_CLS =
  'text-[11px] font-[590] text-ink-mute font-mono flex items-center gap-2 lowercase tracking-[0.01em]'
const ARG_INPUT_CLS =
  'px-2 py-1 bg-page border border-line rounded-md text-ink text-[12px] font-mono outline-none transition-[border-color,box-shadow] duration-[120ms] hover:border-line-strong focus:border-accent focus:shadow-elev-focus placeholder:text-ink-faint'
const ARG_CHECKBOX_CLS = 'w-4 h-4 accent-accent cursor-pointer rounded'
const ARG_REQUIRED_CLS = 'text-danger'
const ARG_HELP_CLS = 'text-[10px] text-ink-faint font-sans normal-case tracking-normal'

export function renderArgsForm(args) {
  if (!args || args.length === 0) {
    hideArgsPanel()
    return
  }

  if (els.argsPanel) els.argsPanel.style.display = ''
  if (els.argsPanel) els.argsPanel.classList.remove('collapsed')
  if (els.argsCount) els.argsCount.textContent = `(${args.length})`
  if (els.argsForm) els.argsForm.innerHTML = ''

  args.forEach((arg, idx) => {
    const field = document.createElement('div')
    const isBool = arg.type === 'bool' || arg.action === 'store_true' || arg.action === 'store_false'

    if (isBool) {
      field.className = ARG_FIELD_CHECKBOX_CLS
      const checkbox = document.createElement('input')
      checkbox.type = 'checkbox'
      checkbox.className = ARG_CHECKBOX_CLS
      checkbox.id = `arg-${idx}`
      checkbox.dataset.dest = arg.dest
      checkbox.dataset.argIndex = idx
      checkbox.checked = arg.default === true
      if (arg.action === 'store_false') {
        checkbox.checked = arg.default !== false
      }

      const label = document.createElement('label')
      label.className = `${ARG_LABEL_CLS} cursor-pointer`
      label.htmlFor = `arg-${idx}`
      label.innerHTML = `${escapeHtml(arg.name)} ${arg.required ? `<span class="${ARG_REQUIRED_CLS}">*</span>` : ''}`
      if (arg.help) {
        label.innerHTML += ` <span class="${ARG_HELP_CLS}">${escapeHtml(arg.help)}</span>`
      }

      field.appendChild(checkbox)
      field.appendChild(label)
    } else {
      field.className = ARG_FIELD_CLS

      const label = document.createElement('label')
      label.className = ARG_LABEL_CLS
      label.innerHTML = `${escapeHtml(arg.name)} ${arg.required ? `<span class="${ARG_REQUIRED_CLS}">*</span>` : ''}`
      if (arg.help) {
        label.innerHTML += ` <span class="${ARG_HELP_CLS}">${escapeHtml(arg.help)}</span>`
      }
      field.appendChild(label)

      let input
      if (arg.choices && arg.choices.length > 0) {
        input = document.createElement('select')
        input.className = ARG_INPUT_CLS
        arg.choices.forEach((choice) => {
          const opt = document.createElement('option')
          opt.value = String(choice)
          opt.textContent = String(choice)
          if (String(arg.default) === String(choice)) opt.selected = true
          input.appendChild(opt)
        })
      } else {
        input = document.createElement('input')
        input.type = arg.type === 'int' || arg.type === 'float' ? 'number' : 'text'
        input.className = ARG_INPUT_CLS
        if (arg.type === 'int') input.step = '1'
        if (arg.type === 'float') input.step = 'any'
        if (arg.default !== undefined && arg.default !== null) {
          input.value = String(arg.default)
        }
        input.placeholder = arg.metavar || arg.dest
      }

      input.id = `arg-${idx}`
      input.dataset.dest = arg.dest
      input.dataset.argIndex = idx
      field.appendChild(input)
    }

    els.argsForm.appendChild(field)
  })
}

// ---------------------------------------------------------------------------
// 隐藏参数面板
// ---------------------------------------------------------------------------
export function hideArgsPanel() {
  if (els.argsPanel) els.argsPanel.style.display = 'none'
  state.currentArgs = []
}

// ---------------------------------------------------------------------------
// 把历史记录的参数回填到表单（重跑前调用，保证表单与实际运行一致）
// 规则：-开头的 token 匹配 spec.flags（选项）或勾选布尔开关；其余按顺序填位置参数。
// 简化处理：不解析「值本身以 - 开头」的参数（如负数需引号的历史记录场景极罕见）。
// ---------------------------------------------------------------------------
export function applyArgsToForm(args: string[]): void {
  if (!els.argsForm || !Array.isArray(args)) return
  const specs = state.currentArgs || []
  const fields = Array.from(els.argsForm.querySelectorAll('[data-arg-index]')) as Array<HTMLInputElement | HTMLSelectElement>
  const positional = fields.filter((f) => {
    const spec = specs[Number(f.dataset.argIndex)]
    return spec && spec.is_positional
  })
  let posIdx = 0

  for (let i = 0; i < args.length; i++) {
    const token = String(args[i] ?? '')
    if (!token) continue

    if (token.startsWith('-')) {
      const idx = fields.findIndex((f) => {
        const spec = specs[Number(f.dataset.argIndex)]
        return spec && Array.isArray(spec.flags) && spec.flags.includes(token)
      })
      if (idx < 0) continue
      const field = fields[idx]
      const spec = specs[Number(field.dataset.argIndex)]
      const isStoreTrue = spec.action === 'store_true'
      const isStoreFalse = spec.action === 'store_false'
      if (isStoreTrue || isStoreFalse) {
        // 历史里出现该 flag 即代表开关生效：store_true 勾选、store_false 取消勾选
        ;(field as HTMLInputElement).checked = isStoreTrue
      } else {
        const next = args[i + 1]
        if (next !== undefined && !String(next).startsWith('-')) {
          field.value = String(next)
          i++
        }
      }
    } else {
      const field = positional[posIdx++]
      if (field) field.value = token
    }
  }
}

// ---------------------------------------------------------------------------
// 从表单收集参数值并转为命令行参数数组
// ---------------------------------------------------------------------------
export function collectArgsFromForm(): string[] {
  const args: any[] = []
  if (!els.argsForm) return args
  const fields = els.argsForm.querySelectorAll('[data-arg-index]')

  fields.forEach((input) => {
    const idx = parseInt((input as HTMLElement).dataset.argIndex as string)
    const spec = state.currentArgs[idx]
    if (!spec) return

    const isBool = spec.type === 'bool' || spec.action === 'store_true' || spec.action === 'store_false'

    if (isBool) {
      const checked = (input as HTMLInputElement).checked
      const isStoreTrue = spec.action === 'store_true'
      const isStoreFalse = spec.action === 'store_false'
      if (isStoreTrue && checked) {
        args.push(spec.flags[0] || `--${spec.dest}`)
      }
      if (isStoreFalse && !checked) {
        args.push(spec.flags[0] || `--${spec.dest}`)
      }
    } else {
      const value = (input as HTMLInputElement).value.trim()
      if (value === '') return

      if (spec.is_positional) {
        args.push(value)
      } else {
        const flag = spec.flags[0] || `--${spec.dest.replace(/_/g, '-')}`
        args.push(flag, value)
      }
    }
  })

  return args
}
