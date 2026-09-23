// icons.ts：Lucide 图标映射（emoji 图标体系的替换，设计规范 v1）
// 独立于 utils.ts：utils 会被 node 单测直接加载，不应引入组件库。
import {
  BarChart3,
  Bug,
  Camera,
  Cpu,
  Database,
  Download,
  FileCode2,
  FolderOpen,
  Gamepad2,
  Globe,
  Image,
  Lock,
  Merge,
  MessageCircle,
  Package,
  Smile,
  Table,
  Timer,
  Turtle,
  Wrench,
  Zap,
  type LucideIcon
} from 'lucide-vue-next'
import type { ExampleItem } from './types'

// 工具箱卡片图标：按工具名称语义匹配（沿旧 getToolIcon 的匹配顺序）
export function toolIconFor(name: string): LucideIcon {
  const n = (name || '').toLowerCase()
  if (n.includes('spider') || n.includes('crawl') || n.includes('爬')) return Bug
  if (n.includes('excel') || n.includes('csv')) return Table
  if (n.includes('file') || n.includes('文件')) return FolderOpen
  if (n.includes('image') || n.includes('图')) return Image
  if (n.includes('download') || n.includes('下载')) return Download
  if (n.includes('count') || n.includes('统计')) return BarChart3
  if (n.includes('login') || n.includes('登录')) return Lock
  if (n.includes('wake') || n.includes('唤醒')) return Zap
  if (n.includes('cpu') || n.includes('监控')) return Cpu
  if (n.includes('countdown') || n.includes('倒计时')) return Timer
  if (n.includes('wechat') || n.includes('微信')) return MessageCircle
  if (n.includes('greeting') || n.includes('问候')) return Smile
  if (n.includes('join') || n.includes('合并')) return Merge
  if (n.includes('data') || n.includes('数据')) return Database
  return Wrench
}

// 分类图标：卡片与详情页共用（topics/tools/projects 之外一律 FileCode2）
export function categoryIcon(category: string): LucideIcon {
  if (category === 'tools') return Wrench
  if (category === 'projects') return Package
  return FileCode2
}

// 示例图标：优先按主题特征（tags/import 标签/名称）细分，让 1349 张卡有辨识度
export function exampleIcon(ex: ExampleItem): LucideIcon {
  if (ex.category === 'tools') return toolIconFor(ex.name || '')
  const hay = `${ex.name || ''} ${(ex.tags || []).join(' ')} ${(ex._importTags || []).join(' ')}`.toLowerCase()
  if (hay.includes('turtle')) return Turtle
  if (hay.includes('pygame')) return Gamepad2
  if (hay.includes('opencv') || hay.includes('cv2')) return Camera
  if (hay.includes('pil') || hay.includes('pillow')) return Image
  if (hay.includes('matplotlib') || hay.includes('pyplot') || hay.includes('pandas') || hay.includes('dataviz'))
    return BarChart3
  if (hay.includes('web') || hay.includes('flask') || hay.includes('requests')) return Globe
  return categoryIcon(ex.category)
}
