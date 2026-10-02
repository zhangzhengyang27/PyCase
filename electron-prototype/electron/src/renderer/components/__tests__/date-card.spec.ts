// ExampleCard 交互形态：隐藏运行与质量分，显示「交互」徽章，open 正常发出。
// 交互工具（interactive: 前缀）不是可运行 Python 示例：卡片不出现运行/质量分，
// 点击仍 emit open（由 ToolboxView 决定路由到交互页还是详情页）。
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ExampleCard from '../ExampleCard.vue'
import type { VExample } from '../../src/store/catalog'

const base: VExample = {
  id: 'interactive:date-calculator',
  name: 'date-calculator',
  category: 'tools',
  path: '',
  title: '日期计算器',
  description: '任选起止日期即时计算。',
  // 有意给个高分：interactive 形态连评分位一起退场，这个分数必须整个消失
  quality_score: 80
}

describe('ExampleCard interactive 形态', () => {
  it('不渲染运行按钮，显示交互徽章，点击发 open', async () => {
    const w = mount(ExampleCard, { props: { ex: base, interactive: true } })
    expect(w.find('[data-testid="card-run"]').exists()).toBe(false)
    expect(w.find('[data-testid="interactive-badge"]').exists()).toBe(true)
    // 质量分与运行同语义退场：交互工具没有可运行的 .py，评分位不成立
    expect(w.text()).not.toContain('80')
    // 打开语义而非详情：交互工具没有详情页
    expect(w.get('[role="button"]').attributes('aria-label')).toBe('日期计算器（打开）')
    await w.trigger('click')
    expect(w.emitted('open')).toHaveLength(1)
  })
  it('普通卡片不受影响（运行按钮仍在）', () => {
    const w = mount(ExampleCard, {
      props: { ex: { ...base, id: 'tools_x', run_status: 'runnable', quality_score: 80 } }
    })
    expect(w.find('[data-testid="card-run"]').exists()).toBe(true)
    expect(w.find('[data-testid="interactive-badge"]').exists()).toBe(false)
    // 普通卡的 aria-label 语义与质量分展示不受 interactive 形态影响
    expect(w.get('[role="button"]').attributes('aria-label')).toBe('日期计算器（详情）')
    expect(w.text()).toContain('80')
  })
})
