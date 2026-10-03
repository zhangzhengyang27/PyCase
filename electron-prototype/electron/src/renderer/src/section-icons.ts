// section-icons.ts：分区与工具箱分组的语义图标（Lucide 单一来源）
// 数据层（themes / overview / toolbox-groups）只保留 key 与 label，图标在此集中映射——
// v2 图标语言：线性 Lucide + 中性 chip 底，emoji 与色相分区徽章退役。
import {
  BarChart3,
  Blocks,
  Boxes,
  Calculator,
  Camera,
  ClipboardList,
  Database,
  Download,
  FileSpreadsheet,
  FileText,
  Film,
  FlaskConical,
  Folder,
  Gamepad2,
  GitBranch,
  Globe,
  GraduationCap,
  Image,
  MessageSquare,
  Network,
  Package,
  Rocket,
  Shield,
  Sparkles,
  Timer,
  Type,
  Turtle,
  Wand2,
  Wrench,
  Zap,
  Activity,
  type LucideIcon
} from 'lucide-vue-next'
import { INTERACTIVE_GROUP_KEY } from './interactive-tools'

/** 画廊分区（五大主题 + 标签分区 + 综合项目 / 其他） */
const SECTION_ICONS: Record<string, LucideIcon> = {
  turtle: Turtle,
  games: Gamepad2,
  opencv: Camera,
  images: Image,
  viz: BarChart3,
  'tag:basics': Blocks,
  'tag:advanced': Zap,
  'tag:crawling': Network,
  'tag:webapp': Globe,
  'tag:office': ClipboardList,
  'tag:database': Database,
  'tag:testing': FlaskConical,
  'tag:algo': Calculator,
  projects: Rocket,
  others: Package
}

export function sectionIcon(key: string | undefined): LucideIcon | undefined {
  return key ? SECTION_ICONS[key] : undefined
}

/** 工具箱分组（内置工具项目 key → 图标；未知项目与独立工具回退 Wrench） */
const TOOLBOX_ICONS: Record<string, LucideIcon> = {
  'db-table-dictionary-generator': Database,
  'excel-row-to-in-clause': FileSpreadsheet,
  [INTERACTIVE_GROUP_KEY]: Sparkles, // 「交互工具」分组：键与 ToolboxView 分组对象同源，漂移会静默退化成 Wrench
  'python-black-magic': Wand2,
  'remote-sftp-downloader': Download,
  'tkinter-work-countdown': Timer,
  'utility-crawlers': Globe,
  'wechat-official-account': MessageSquare,
  standalone: Wrench
}

export function toolboxIcon(key: string): LucideIcon {
  return TOOLBOX_ICONS[key] || Wrench
}

// 工具箱二级分类图标（W16）：key = toolbox-cats.ts 分类 key
export const TOOL_CATEGORY_ICONS: Record<string, LucideIcon> = {
  files: Folder,
  image: Image,
  media: Film,
  doc: FileText,
  data: Database,
  text: Type,
  net: Globe,
  sysmon: Activity,
  sec: Shield,
  git: GitBranch,
  conv: Calculator,
  effi: Timer,
  teach: GraduationCap,
  other: Boxes
}

export function toolCategoryIcon(key: string): LucideIcon {
  return TOOL_CATEGORY_ICONS[key] || Boxes
}
