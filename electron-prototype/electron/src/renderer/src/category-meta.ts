// category-meta.ts：分类（topics/tools/projects/user）的展示元数据（卡片与详情页共用）
// 色相驱动：.hue-chip 类 + 内联 --hue 变量（specs §3.2）；accent-violet 留给 Monaco 语法色。
import { FileCode2, FolderUp, Package, Wrench, type LucideIcon } from 'lucide-vue-next'

export const CATEGORY_META: Record<string, { hue: string; cls: string; icon: LucideIcon }> = {
  topics: { hue: '#5e6ad2', cls: 'bg-accent/12 text-accent-violet', icon: FileCode2 },
  tools: { hue: '#2fa866', cls: 'bg-ok-bg text-ok', icon: Wrench },
  projects: { hue: '#d9a03d', cls: 'bg-warn-bg text-warn', icon: Package },
  // 用户导入的示例（导入向导产物）
  user: { hue: '#2fb8a6', cls: 'bg-accent/12 text-accent-violet', icon: FolderUp }
}
