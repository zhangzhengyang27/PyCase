// interactive-tools.ts：交互工具注册表——不是可运行 Python 示例，是应用内交互页的
// 工具箱门面。不进内置库 JSON（避免污染可运行率 / 守卫 / sidecar 文件装载），
// 由 catalog 合并进工具池：参与搜索与收藏（客户端匹配），恒置顶展示。
import type { VExample } from './store/catalog'

export const INTERACTIVE_PREFIX = 'interactive:'
export const DATE_CALC_ID = `${INTERACTIVE_PREFIX}date-calculator`

export function isInteractiveId(id: string | undefined | null): boolean {
  return !!id && id.startsWith(INTERACTIVE_PREFIX)
}

export const interactiveToolItems: VExample[] = [
  {
    id: DATE_CALC_ID,
    name: 'date-calculator',
    category: 'tools',
    path: '',
    title: '日期计算器',
    description: '任选起止日期，即时计算间隔、正倒计时、日期加减与日历跨度，附等价 Python 代码。',
    tags: ['日期', '交互工具']
  }
]
