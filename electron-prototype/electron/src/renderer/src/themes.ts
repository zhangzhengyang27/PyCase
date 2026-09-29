// themes.ts：画廊筛选条的主题维度配置（纯函数，无 DOM 依赖）
// v2：主题判定改认服务端下发的 theme_key（契约 §3.2/§5）——列表不再带 code，
// 而主题谓词既要读 import 又要读正文子串，判据只能留在能读源码的一侧。
// 服务端实现见 app/contract_store.py::theme_key，两侧谓词逐条对齐。

export interface ThemeConfig {
  key: string
  label: string
  placeholder: string
  /** 判定依据 = 服务端下发的 theme_key（列表不含 code，判据不在前端） */
  filter: (e: { theme_key?: string | null }) => boolean
}

export const THEMES: ThemeConfig[] = [
  {
    key: 'turtle',
    label: 'Turtle 绘图',
    placeholder: '搜索 Turtle 示例…',
    filter: (e) => e.theme_key === 'turtle'
  },
  {
    key: 'games',
    label: 'Pygame 游戏',
    placeholder: '搜索 Pygame 游戏示例…',
    filter: (e) => e.theme_key === 'games'
  },
  {
    key: 'opencv',
    label: 'OpenCV 视觉',
    placeholder: '搜索 OpenCV 示例…',
    filter: (e) => e.theme_key === 'opencv'
  },
  {
    key: 'images',
    label: 'PIL 图像处理',
    placeholder: '搜索 PIL 图像示例…',
    filter: (e) => e.theme_key === 'images'
  },
  {
    key: 'viz',
    label: '数据可视化',
    placeholder: '搜索可视化示例…',
    filter: (e) => e.theme_key === 'viz'
  }
]
