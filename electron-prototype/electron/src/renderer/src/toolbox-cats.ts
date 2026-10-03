// toolbox-cats.ts：工具箱分类体系（W16 二级菜单）——
// 把 ~240 个工具条目（目录池 + 交互注册表）按能力域互斥归入 14 个分类，
// 供左侧二级菜单（App.vue，镜像画廊分区菜单）与工具箱过滤共用。
// 纯函数、无依赖；规则按声明序 first-match，具体域在前、兜底在后。
export interface ToolCategoryMeta {
  key: string
  label: string
}

export const TOOL_CATEGORY_CATALOG: readonly ToolCategoryMeta[] = [
  { key: 'files', label: '文件与目录' },
  { key: 'image', label: '图片' },
  { key: 'media', label: '音视频' },
  { key: 'doc', label: '文档办公' },
  { key: 'data', label: '数据与数据库' },
  { key: 'text', label: '文本处理' },
  { key: 'net', label: '网络' },
  { key: 'sysmon', label: '系统与监控' },
  { key: 'sec', label: '安全' },
  { key: 'git', label: 'Git' },
  { key: 'conv', label: '换算与生成' },
  { key: 'effi', label: '效率' },
  { key: 'teach', label: '课程脚本' },
  { key: 'other', label: '其他工具' }
]

/** 规则表：按序 first-match；kw 命中 tags/title/name 即归入该分类 */
const RULES: Array<{ key: string; kws: string[] }> = [
  { key: 'teach', kws: [] }, // 特判：name/title 以 .py 结尾的课程脚本（见函数内）
  { key: 'git', kws: ['git'] },
  { key: 'sec', kws: ['安全', '密码', '敏感', 'jwt', '保险库', '粉碎', 'token', '密钥'] },
  { key: 'net', kws: ['网络', 'ip 查询', 'dns', '端口', 'http', '网速', 'url', '站点', '网页', '域名'] },
  { key: 'sysmon', kws: ['系统', '电池', '磁盘', '进程', '硬件'] },
  { key: 'media', kws: ['视频', '音频', '媒体', '转码', '音轨', '音量', 'ffmpeg'] },
  {
    key: 'doc',
    kws: [
      'excel',
      'word',
      'ppt',
      'pdf',
      'docx',
      'xlsx',
      '邮件',
      '日报',
      '待办',
      '函件',
      '盘点',
      '拆分',
      '去重',
      '透视',
      '关联',
      '校验',
      '表格',
      '工时',
      '纪要'
    ]
  },
  { key: 'image', kws: ['图片', '图像', 'gif', '水印', '缩放', '裁剪', '拼贴', '主色调', '圆角', '截图'] },
  { key: 'data', kws: ['数据库', 'sqlite', 'json', 'yaml', 'dataclass', 'csv', '统计', '记账'] },
  {
    key: 'text',
    kws: [
      '文本',
      'markdown',
      '正则',
      '折行',
      '缩进',
      '换行',
      '词频',
      'todo',
      'fixme',
      '对比',
      '查找替换',
      '回文',
      '编码',
      'base64',
      'url 编解码'
    ]
  },
  {
    key: 'files',
    kws: [
      '文件',
      '目录',
      '文件夹',
      '重复',
      '大文件',
      '同步',
      '备份',
      '清理',
      '查找',
      '压缩',
      '解压',
      '归档',
      '分类',
      '树',
      '监听',
      '路径'
    ]
  },
  { key: 'conv', kws: ['换算', '进制', '单位', '生成器', 'uuid', '二维码', '颜色', '时间', '日期', '转换'] },
  { key: 'effi', kws: ['效率', '番茄钟', '计时'] }
]

/** 工具条目 → 分类 key（互斥、first-match；兜底 other） */
export function toolCategoryKeyOf(item: { title?: string; name?: string; tags?: string[] }): string {
  // 课程脚本判定：title 呈「纯文件名.py」形态（migrated 条目的 title 即文件名，
  // 正常工具的 title 是中文名不会命中）
  const title = (item.title || '').trim()
  if (/^[\w-]+\.py$/i.test(title)) return 'teach'
  const hay = `${(item.tags || []).join(' ')} ${title.toLowerCase()} ${(item.name || '').toLowerCase()}`
  for (const rule of RULES) {
    if (rule.kws.some((kw) => hay.includes(kw))) return rule.key
  }
  return 'other'
}

export function toolCategoryLabelOf(key: string): string {
  return TOOL_CATEGORY_CATALOG.find((c) => c.key === key)?.label ?? '其他工具'
}
