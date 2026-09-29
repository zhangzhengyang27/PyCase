// base 层组件测试：无 store 依赖的通用控件（按钮 / 输入 / 下拉 / 弹窗 / 空态 / 横幅 / 骨架 / toast）。
// 这一层是 22 个组件里最「纯」的部分——只靠 props/emits/slots 通信，因此也是
// 组件测试基建的第一块试金石：跑通即证明 @vitejs/plugin-vue + jsdom + test-utils 链路可用。
import { describe, expect, it, afterEach, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { markRaw } from 'vue'

import BaseButton from '../base/BaseButton.vue'
import BaseInput from '../base/BaseInput.vue'
import BaseSelect from '../base/BaseSelect.vue'
import AppModal from '../base/AppModal.vue'
import AppEmpty from '../base/AppEmpty.vue'
import AlertBanner from '../base/AlertBanner.vue'
import SkeletonCard from '../base/SkeletonCard.vue'
import AppToast from '../base/AppToast.vue'
import { dismissToast, pushToast, toasts } from '../../toast'

// Teleport 组件（AppModal / AppToast）会把 DOM 挂到 document.body，
// 每个用例后必须清掉，否则上一个用例的弹窗会污染下一个的查询结果。
afterEach(() => {
  document.body.innerHTML = ''
  toasts.value = []
  vi.useRealTimers()
})

// ---------------------------------------------------------------------------
// BaseButton
// ---------------------------------------------------------------------------
describe('BaseButton', () => {
  it('渲染默认插槽内容，默认 variant=ghost / size=md / type=button', () => {
    const w = mount(BaseButton, { slots: { default: '运行' } })
    const btn = w.get('button')
    expect(btn.text()).toBe('运行')
    expect(btn.attributes('type')).toBe('button')
    // ghost 变体特征类
    expect(btn.classes()).toContain('bg-transparent')
    // md 高度
    expect(btn.classes()).toContain('h-[var(--ctrl-md)]')
  })

  it('variant 与 size 映射到对应类名', () => {
    const primary = mount(BaseButton, { props: { variant: 'primary', size: 'lg' } })
    expect(primary.get('button').classes()).toContain('btn-primary-deep')
    expect(primary.get('button').classes()).toContain('h-[var(--ctrl-lg)]')

    const danger = mount(BaseButton, { props: { variant: 'danger', size: 'sm' } })
    // v2：危险 = 红色文字按钮（不填充），尺寸走 --ctrl-sm
    expect(danger.get('button').classes()).toContain('btn-danger-deep')
    expect(danger.get('button').classes()).toContain('h-[var(--ctrl-sm)]')
  })

  it('square 时按 size 给出等宽方形（sm=w-6 / md=w-7 / lg=w-8）且去掉横向内边距', () => {
    expect(mount(BaseButton, { props: { square: true, size: 'sm' } }).get('button').classes()).toContain('w-6')
    expect(mount(BaseButton, { props: { square: true, size: 'md' } }).get('button').classes()).toContain('w-7')
    expect(mount(BaseButton, { props: { square: true, size: 'lg' } }).get('button').classes()).toContain('w-8')

    const sq = mount(BaseButton, { props: { square: true } }).get('button')
    expect(sq.classes()).toContain('px-0')
    expect(sq.classes()).not.toContain('px-2.5')

    // 非 square 才给横向内边距
    expect(mount(BaseButton).get('button').classes()).toContain('px-2.5')
  })

  it('disabled 或 loading 时按钮进入原生 disabled 态', () => {
    expect(mount(BaseButton, { props: { disabled: true } }).get('button').attributes('disabled')).toBeDefined()
    expect(mount(BaseButton, { props: { loading: true } }).get('button').attributes('disabled')).toBeDefined()
    // 两者都未设置时不带 disabled
    expect(mount(BaseButton).get('button').attributes('disabled')).toBeUndefined()
  })

  it('loading 时额外渲染内联 spinner（不吞掉插槽文案）', () => {
    const w = mount(BaseButton, { props: { loading: true }, slots: { default: '保存中' } })
    expect(w.find('span.animate-spin').exists()).toBe(true)
    expect(w.get('button').text()).toContain('保存中')
    // 非 loading 不渲染 spinner
    expect(mount(BaseButton).find('span.animate-spin').exists()).toBe(false)
  })

  it('点击冒泡出 click 事件并携带原生事件对象', async () => {
    const w = mount(BaseButton, { slots: { default: 'go' } })
    await w.get('button').trigger('click')
    expect(w.emitted('click')).toHaveLength(1)
    expect(w.emitted('click')![0][0]).toBeInstanceOf(Event)
  })

  it('title 透传到原生 title 属性', () => {
    expect(mount(BaseButton, { props: { title: '运行示例' } }).get('button').attributes('title')).toBe('运行示例')
  })
})

// ---------------------------------------------------------------------------
// BaseInput
// ---------------------------------------------------------------------------
describe('BaseInput', () => {
  it('受控渲染 modelValue，输入时 emit update:modelValue', async () => {
    const w = mount(BaseInput, { props: { modelValue: 'abc' } })
    const input = w.get('input')
    expect((input.element as HTMLInputElement).value).toBe('abc')

    await input.setValue('abcd')
    expect(w.emitted('update:modelValue')).toEqual([['abcd']])
  })

  it('默认 md（h-7）/ lg（h-8）尺寸类', () => {
    expect(mount(BaseInput, { props: { modelValue: '' } }).get('input').classes()).toContain('h-7')
    expect(mount(BaseInput, { props: { modelValue: '', size: 'lg' } }).get('input').classes()).toContain('h-8')
  })

  it('error 态：红框 + aria-invalid + 下方错误文案；无 error 时不渲染文案', () => {
    const w = mount(BaseInput, { props: { modelValue: '', error: '不能为空' } })
    expect(w.get('input').attributes('aria-invalid')).toBe('true')
    expect(w.get('input').classes()).toContain('border-danger')
    expect(w.get('p').text()).toBe('不能为空')

    const ok = mount(BaseInput, { props: { modelValue: '' } })
    expect(ok.get('input').attributes('aria-invalid')).toBeUndefined()
    expect(ok.find('p').exists()).toBe(false)
    expect(ok.get('input').classes()).toContain('border-line')
  })

  it('type=password 且 showPassword 时提供可见性切换按钮', async () => {
    const w = mount(BaseInput, { props: { modelValue: 's3cret', type: 'password', showPassword: true } })
    const input = w.get('input')
    expect(input.attributes('type')).toBe('password')

    const toggle = w.get('button')
    await toggle.trigger('click')
    expect(w.get('input').attributes('type')).toBe('text')
    // 按钮 title 随状态切换，便于无障碍识别
    expect(w.get('button').attributes('title')).toBe('隐藏密码')

    await toggle.trigger('click')
    expect(w.get('input').attributes('type')).toBe('password')
  })

  it('未开启 showPassword 时不出现切换按钮（即便 type=password）', () => {
    const w = mount(BaseInput, { props: { modelValue: '', type: 'password' } })
    expect(w.find('button').exists()).toBe(false)
    expect(w.get('input').attributes('type')).toBe('password')
  })

  it('透传 placeholder / autocomplete / spellcheck / aria-label', () => {
    const w = mount(BaseInput, {
      props: { modelValue: '', placeholder: '搜索', autocomplete: 'email', spellcheck: false, ariaLabel: '搜索框' }
    })
    const attrs = w.get('input').attributes()
    expect(attrs.placeholder).toBe('搜索')
    expect(attrs.autocomplete).toBe('email')
    expect(attrs['aria-label']).toBe('搜索框')
    // jsdom 未实现 spellcheck 属性（'spellcheck' in input === false），
    // 因此 Vue 走 setAttribute 分支——断言属性而非 property。
    expect(attrs.spellcheck).toBe('false')
    // 未传时不应写入该属性
    expect(mount(BaseInput, { props: { modelValue: '' } }).get('input').attributes('spellcheck')).toBeUndefined()
  })
})

// ---------------------------------------------------------------------------
// BaseSelect
// ---------------------------------------------------------------------------
describe('BaseSelect', () => {
  it('经插槽渲染 option，change 时 emit update:modelValue', async () => {
    const w = mount(BaseSelect, {
      props: { modelValue: 'b' },
      slots: { default: '<option value="a">甲</option><option value="b">乙</option>' }
    })
    const select = w.get('select')
    expect(select.findAll('option')).toHaveLength(2)
    expect((select.element as HTMLSelectElement).value).toBe('b')

    await select.setValue('a')
    expect(w.emitted('update:modelValue')).toEqual([['a']])
  })

  it('title 透传', () => {
    expect(mount(BaseSelect, { props: { modelValue: 'a', title: '排序' } }).get('select').attributes('title')).toBe('排序')
  })
})

// ---------------------------------------------------------------------------
// AppModal
// ---------------------------------------------------------------------------
describe('AppModal', () => {
  function mountModal(props: Record<string, unknown> = {}, slots: Record<string, string> = {}) {
    return mount(AppModal, {
      props: { title: '标题', ...props },
      slots,
      attachTo: document.body
    })
  }

  it('Teleport 到 body，渲染标题、role=dialog、aria-modal、aria-label', () => {
    mountModal({}, { default: '内容' })
    const dialog = document.body.querySelector('[role="dialog"]')!
    expect(dialog).toBeTruthy()
    expect(dialog.getAttribute('aria-modal')).toBe('true')
    expect(dialog.getAttribute('aria-label')).toBe('标题')
    expect(dialog.textContent).toContain('标题')
    expect(dialog.textContent).toContain('内容')
  })

  it('width 默认 440px 并可通过 prop 覆盖（写成 inline style）', () => {
    mountModal()
    expect(document.body.querySelector('[role="dialog"]')!.getAttribute('style')).toContain('width: 440px')

    document.body.innerHTML = ''
    mountModal({ width: '720px' })
    expect(document.body.querySelector('[role="dialog"]')!.getAttribute('style')).toContain('width: 720px')
  })

  it('点击关闭按钮 emit close', async () => {
    const w = mountModal()
    const closeBtn = document.body.querySelector('button[aria-label="关闭"]') as HTMLElement
    closeBtn.click()
    await w.vm.$nextTick()
    expect(w.emitted('close')).toHaveLength(1)
  })

  it('Esc 关闭', async () => {
    const w = mountModal()
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await w.vm.$nextTick()
    expect(w.emitted('close')).toHaveLength(1)
  })

  it('点击遮罩自身（@click.self）关闭', async () => {
    const w = mountModal()
    const backdrop = document.body.querySelector('.fixed.inset-0') as HTMLElement
    backdrop.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    await w.vm.$nextTick()
    expect(w.emitted('close')).toHaveLength(1)
  })

  it('仅当提供 footer 插槽时才渲染底栏', () => {
    mountModal()
    expect(document.body.querySelector('.border-t')).toBeNull()

    document.body.innerHTML = ''
    mountModal({}, { footer: '<button>确定</button>' })
    expect(document.body.querySelector('.border-t')).toBeTruthy()
  })

  it('draggable=false 时头部不带拖拽光标类', () => {
    mountModal({ draggable: false })
    const header = document.body.querySelector('[role="dialog"] > div')!
    expect(header.className).not.toContain('cursor-grab')
  })

  it('头部拖拽（pointerdown + pointermove）写入 translate 位移', async () => {
    const w = mountModal({ draggable: true })
    const dialog = document.body.querySelector('[role="dialog"]') as HTMLElement
    const header = dialog.firstElementChild as HTMLElement

    header.dispatchEvent(new PointerEvent('pointerdown', { clientX: 100, clientY: 100, bubbles: true }))
    window.dispatchEvent(new PointerEvent('pointermove', { clientX: 140, clientY: 130, bubbles: true }))
    await w.vm.$nextTick()

    const style = dialog.getAttribute('style')!
    expect(style).toContain('translate(40px, 30px)')

    window.dispatchEvent(new PointerEvent('pointerup', { bubbles: true }))
  })

  it('点击头部内的按钮不触发拖拽（closest("button") 守卫）', async () => {
    const w = mountModal({ draggable: true })
    const dialog = document.body.querySelector('[role="dialog"]') as HTMLElement
    const closeBtn = dialog.querySelector('button') as HTMLElement

    closeBtn.dispatchEvent(new PointerEvent('pointerdown', { clientX: 100, clientY: 100, bubbles: true }))
    window.dispatchEvent(new PointerEvent('pointermove', { clientX: 200, clientY: 200, bubbles: true }))
    await w.vm.$nextTick()

    expect(dialog.getAttribute('style')).toContain('translate(0px, 0px)')
  })

  it('拖拽被钳制在视口内（不会把面板整个拖出屏幕）', async () => {
    const w = mountModal({ draggable: true })
    const dialog = document.body.querySelector('[role="dialog"]') as HTMLElement
    const header = dialog.firstElementChild as HTMLElement

    header.dispatchEvent(new PointerEvent('pointerdown', { clientX: 0, clientY: 0, bubbles: true }))
    // 向左上拖一个夸张的量：jsdom 里 getBoundingClientRect 全为 0，
    // 钳制下限 minX = 16 - 0 - 0 = 16，minY = 16 - 0 = 16
    window.dispatchEvent(new PointerEvent('pointermove', { clientX: -5000, clientY: -5000, bubbles: true }))
    await w.vm.$nextTick()

    expect(dialog.getAttribute('style')).toContain('translate(16px, 16px)')
    window.dispatchEvent(new PointerEvent('pointerup', { bubbles: true }))
  })
})

// ---------------------------------------------------------------------------
// AppEmpty
// ---------------------------------------------------------------------------
describe('AppEmpty', () => {
  it('渲染 title，description 可选', () => {
    const withDesc = mount(AppEmpty, { props: { title: '没有结果', description: '换个关键词试试' } })
    expect(withDesc.text()).toContain('没有结果')
    expect(withDesc.text()).toContain('换个关键词试试')

    const without = mount(AppEmpty, { props: { title: '没有结果' } })
    // 无 description 时正文只剩标题（图标容器本身无文本）
    expect(without.text()).toBe('没有结果')
  })

  it('icon 传入组件时才渲染图标容器内的图标', () => {
    // markRaw：VTU 会把 props 变成响应式，组件对象被 reactive 包住会触发 Vue 警告。
    const icon = markRaw({ template: '<svg data-testid="fake-icon" />' })
    const withIcon = mount(AppEmpty, { props: { title: '空', icon } })
    expect(withIcon.find('[data-testid="fake-icon"]').exists()).toBe(true)

    const without = mount(AppEmpty, { props: { title: '空' } })
    expect(without.find('[data-testid="fake-icon"]').exists()).toBe(false)
  })

  it('默认插槽用于放置动作按钮', () => {
    const w = mount(AppEmpty, { props: { title: '空' }, slots: { default: '<button>重试</button>' } })
    expect(w.get('button').text()).toBe('重试')
  })
})

// ---------------------------------------------------------------------------
// AlertBanner
// ---------------------------------------------------------------------------
describe('AlertBanner', () => {
  it('role=alert 并渲染标题', () => {
    const w = mount(AlertBanner, { props: { title: '加载失败' } })
    expect(w.get('[role="alert"]').text()).toContain('加载失败')
  })

  it('type 默认 error，warning 切换配色类', () => {
    const err = mount(AlertBanner, { props: { title: 'x' } })
    expect(err.get('[role="alert"]').classes()).toContain('bg-danger-bg')
    expect(err.find('svg').classes()).toContain('text-danger')

    const warn = mount(AlertBanner, { props: { title: 'x', type: 'warning' } })
    expect(warn.get('[role="alert"]').classes()).toContain('bg-warn-bg')
    expect(warn.find('svg').classes()).toContain('text-warn')
  })

  it('默认插槽渲染右侧动作', () => {
    const w = mount(AlertBanner, { props: { title: 'x' }, slots: { default: '<button>重试</button>' } })
    expect(w.get('button').text()).toBe('重试')
  })
})

// ---------------------------------------------------------------------------
// SkeletonCard
// ---------------------------------------------------------------------------
describe('SkeletonCard', () => {
  it('渲染占位骨架（含 pulse 动画）且无文本内容', () => {
    const w = mount(SkeletonCard)
    expect(w.get('div').classes()).toContain('animate-pulse')
    expect(w.text()).toBe('')
    // 与 ExampleCard 同构：1 个图标占位块 + 头部 2 行 + 正文 3 行 = 5 条占位条
    expect(w.findAll('.bg-card')).toHaveLength(5)
    expect(w.findAll('.bg-hover')).toHaveLength(1)
  })
})

// ---------------------------------------------------------------------------
// AppToast
// ---------------------------------------------------------------------------
describe('AppToast', () => {
  // @vue/test-utils 默认把 <TransitionGroup> 替换成 <transition-group-stub>，
  // 因此条目并不是 [role="status"] 的直接子元素，中间隔着一层 stub 元素。
  // 这里刻意写出 stub 标签名而不是用宽松的 `[role="status"] div`：
  // 若将来取消 transition stub，测试会立即失败并提醒改选择器，而不是静默变宽松。
  function toastItems(): HTMLElement[] {
    return Array.from(
      document.body.querySelectorAll<HTMLElement>('[role="status"] > transition-group-stub > div')
    )
  }

  beforeEach(() => {
    vi.useFakeTimers()
  })

  it('无 toast 时容器存在但不渲染条目', () => {
    mount(AppToast)
    const region = document.body.querySelector('[role="status"]')!
    expect(region).toBeTruthy()
    expect(region.getAttribute('aria-live')).toBe('polite')
    expect(toastItems()).toHaveLength(0)
  })

  it('toast.ts 状态变化驱动条目渲染（真实响应式，非 mock）', async () => {
    mount(AppToast)
    pushToast('success', '保存成功')
    await Promise.resolve()
    await Promise.resolve()

    const items = toastItems()
    expect(items).toHaveLength(1)
    expect(items[0].textContent).toContain('保存成功')
  })

  it('关闭按钮调用 dismissToast 移除对应条目', async () => {
    mount(AppToast)
    pushToast('info', '提示一')
    await Promise.resolve()
    await Promise.resolve()

    const btn = document.body.querySelector('button[aria-label="关闭通知"]') as HTMLElement
    btn.click()
    await Promise.resolve()
    await Promise.resolve()

    expect(toasts.value).toHaveLength(0)
  })

  it('超过同屏上限 4 条时最旧的被顶掉', () => {
    pushToast('info', 'a')
    pushToast('info', 'b')
    pushToast('info', 'c')
    pushToast('info', 'd')
    pushToast('info', 'e')
    expect(toasts.value).toHaveLength(4)
    expect(toasts.value.map((t) => t.text)).toEqual(['b', 'c', 'd', 'e'])
  })

  it('到达超时时间后自动退场（success 3s）', async () => {
    pushToast('success', '稍后消失')
    expect(toasts.value).toHaveLength(1)
    vi.advanceTimersByTime(3000)
    expect(toasts.value).toHaveLength(0)
  })

  it('悬停暂停、移出恢复倒计时', async () => {
    mount(AppToast)
    pushToast('success', '悬停测试')
    await Promise.resolve()
    await Promise.resolve()

    const item = toastItems()[0]
    item.dispatchEvent(new MouseEvent('mouseenter'))
    vi.advanceTimersByTime(5000)
    // 暂停期间不消失
    expect(toasts.value).toHaveLength(1)

    item.dispatchEvent(new MouseEvent('mouseleave'))
    vi.advanceTimersByTime(3000)
    expect(toasts.value).toHaveLength(0)
  })

  it('dismissToast 清理定时器，不会在之后重复触发', () => {
    pushToast('error', '错误')
    dismissToast(toasts.value[0].id)
    expect(toasts.value).toHaveLength(0)
    vi.advanceTimersByTime(8000)
    expect(toasts.value).toHaveLength(0)
  })
})
