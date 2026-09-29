// category-meta.ts：分类（topics/tools/projects/user）的语义图标（卡片与详情页共用）
// v2：分类不再驱动色相/底色，只贡献一个 Lucide 图标；未收录分类由消费方回退 categoryIcon。
import { FileCode2, FolderUp, Package, Wrench, type LucideIcon } from 'lucide-vue-next'

export const CATEGORY_ICONS: Record<string, LucideIcon> = {
  topics: FileCode2,
  tools: Wrench,
  projects: Package,
  // 用户导入的示例（导入向导产物）
  user: FolderUp
}
