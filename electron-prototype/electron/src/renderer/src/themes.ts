// themes.ts：画廊筛选条的主题维度配置（纯函数，无 DOM 依赖）
// 从 state.ts 抽出：state.ts 的 els 采集有模块级 DOM 副作用，Vue 渲染层
// 不应为此付出代价；旧代码经 state.ts 的 re-export 继续使用，行为不变。

import type { ExampleItem } from './types'

export interface ThemeConfig {
  key: string
  label: string
  placeholder: string
  filter: (e: ExampleItem) => boolean
}

export const THEMES: ThemeConfig[] = [
  {
    key: 'turtle',
    label: 'Turtle 绘图',
    placeholder: '搜索 Turtle 示例…',
    filter: (e) => {
      const name = (e.name || '').toLowerCase()
      const desc = (e.description || '').toLowerCase()
      const code = (e.code || '').toLowerCase()
      const tags = (e.tags || []).join(' ').toLowerCase()
      return name.includes('turtle') || desc.includes('turtle') || code.includes('turtle') || tags.includes('turtle')
    }
  },
  {
    key: 'games',
    label: 'Pygame 游戏',
    placeholder: '搜索 Pygame 游戏示例…',
    filter: (e) => {
      if (e.name === '__init__.py' || e.category === 'projects') return false
      return /^\s*(?:import|from)\s+pygame\b/m.test(e.code || '')
    }
  },
  {
    key: 'opencv',
    label: 'OpenCV 视觉',
    placeholder: '搜索 OpenCV 示例…',
    filter: (e) => {
      if (e.name === '__init__.py' || e.category === 'projects') return false
      return /^\s*(?:import|from)\s+cv2\b/m.test(e.code || '')
    }
  },
  {
    key: 'images',
    label: 'PIL 图像处理',
    placeholder: '搜索 PIL 图像示例…',
    filter: (e) => {
      if (e.name === '__init__.py' || e.category === 'projects') return false
      return /^\s*(?:import|from)\s+(?:PIL|Pillow)\b/m.test(e.code || '')
    }
  },
  {
    key: 'viz',
    label: '数据可视化',
    placeholder: '搜索可视化示例…',
    filter: (e) => {
      if (e.name === '__init__.py' || e.category === 'projects') return false
      return /\b(matplotlib|pyplot|pandas)\b/.test(e.code || '')
    }
  }
]
