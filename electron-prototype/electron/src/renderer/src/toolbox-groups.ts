// toolbox-groups.ts：工具箱按「工具项目」分组的纯函数（无 DOM / store 依赖）
// 分组依据 = sidecar source_dir（内置库 JSON 的 dir 字段，如 'tools/utility-crawlers'），
// 取 tools/ 下第一段为项目 key；无 source_dir 的条目（examples.json 独立工具、
// 用户导入集合）归入「独立工具」兜底组，为空时省略。
import type { ExampleItem } from './types'

export interface ToolboxGroup {
  key: string
  label: string
  items: ExampleItem[]
}

// 内置工具项目的展示元数据（与 json_examples 内置库对应；未收录项目回退原 key 展示）
const PROJECT_META: Record<string, { label: string }> = {
  'db-table-dictionary-generator': { label: '数据库数据字典生成器' },
  'excel-row-to-in-clause': { label: 'Excel 行转 IN 语句' },
  'python-black-magic': { label: 'Python 黑魔法' },
  'remote-sftp-downloader': { label: 'SFTP 远程下载' },
  'tkinter-work-countdown': { label: '上班倒计时（Tkinter）' },
  'utility-crawlers': { label: '实用爬虫合集' },
  'wechat-official-account': { label: '微信公众号工具' }
}

const UNGROUPED_META = { key: 'standalone', label: '独立工具' } as const

export function projectKeyOf(sourceDir: string | undefined): string | null {
  if (!sourceDir) return null
  const parts = sourceDir.split('/')
  // 'tools/<project>/...' → <project>；非 tools 前缀或不足两段不构成项目分组
  if (parts[0] !== 'tools' || parts.length < 2 || !parts[1]) return null
  return parts[1]
}

export function buildToolboxGroups<T extends ExampleItem>(tools: readonly T[]): ToolboxGroup[] {
  const buckets = new Map<string, T[]>()
  const standalone: T[] = []
  for (const t of tools) {
    const key = projectKeyOf(t.source_dir)
    if (!key) standalone.push(t)
    else {
      if (!buckets.has(key)) buckets.set(key, [])
      buckets.get(key)!.push(t)
    }
  }
  const groups: ToolboxGroup[] = Array.from(buckets.entries()).map(([key, items]) => ({
    key,
    label: PROJECT_META[key]?.label || key,
    items
  }))
  // 组顺序稳定：内置项目按 PROJECT_META 声明序，未知项目按 key 字典序，独立工具垫底
  const order = (g: ToolboxGroup) => {
    const i = Object.keys(PROJECT_META).indexOf(g.key)
    return i === -1 ? Object.keys(PROJECT_META).length : i
  }
  groups.sort((a, b) => order(a) - order(b) || a.key.localeCompare(b.key))
  if (standalone.length > 0) groups.push({ ...UNGROUPED_META, items: standalone })
  return groups
}
