// interactive-mapping.ts：目录条目 ↔ 交互页面的映射（画廊路由终局形态）。
// 两张表：
//   1) TITLE_TO_INTERACTIVE——CLI/目录条目，title 精确匹配（W3-W14 各批）；
//   2) VIZ_FAMILY_TO_INTERACTIVE——bulk_viz 图族变体，id 形如 topics_viz-<图族>-d<N>，
//      由 vizVariantOf 解析出图族后查表（30 图族中 29 个已路由，quiver 暂无页面走详情兜底）。
// store/detail.ts 的 openDetail 统一收口：凡命中映射的条目，打开动作一律直达交互页面
// （画廊/清单/收藏/历史/命令面板全生效）；原示例源码从交互页头部的「查看原示例源码」
// 回链进入（双向可达）。生成器改名时本表与内置库 JSON 需同步。
import { computed } from 'vue'
import { examples } from './store/catalog'
import { selectedId } from './store/detail'
import { getToolSchema } from './interactive-tools'
import type { VExample } from './store/catalog'

export const TITLE_TO_INTERACTIVE: Record<string, string> = {
  // ---- W3 devtools ----
  正则测试器: 'interactive:regex-tester',
  'JSON 格式化校验': 'interactive:json-format',
  'JSON → dataclass': 'interactive:json-dataclass',
  'CSV ↔ JSON 互转': 'interactive:csv-json',
  时间戳转换器: 'interactive:timestamp',
  'UUID/短 ID 生成器': 'interactive:uuid',
  颜色转换器: 'interactive:color',
  科学单位换算: 'interactive:unit-convert',
  密码强度检查: 'interactive:pwd-strength',
  // ---- W4 轻量 ----
  'JWT 解码器': 'interactive:jwt',
  '.env 校验器': 'interactive:env-check',
  'Markdown 目录生成': 'interactive:md-toc',
  'gitignore 生成器': 'interactive:gitignore',
  换行符规范化: 'interactive:normalize',
  缩进规范化: 'interactive:normalize', // 与换行符规范化归并为同一页面
  批量查找替换: 'interactive:find-replace',
  密码生成器: 'interactive:pwd-gen',
  // ---- W5/W6 文件管道 ----
  批量缩放: 'interactive:batch-resize',
  批量格式转换: 'interactive:batch-convert',
  批量裁剪比例: 'interactive:batch-crop',
  批量水印: 'interactive:batch-watermark',
  图片批量水印: 'interactive:batch-watermark', // office 同名能力
  主色调提取: 'interactive:palette',
  'GIF 帧提取': 'interactive:gif-extract',
  '图片合成 GIF': 'interactive:gif-compose',
  '批量亮度/对比度': 'interactive:batch-enhance',
  图片信息报告: 'interactive:image-info',
  圆角与边框: 'interactive:rounded-frame',
  图片批量压缩: 'interactive:batch-convert', // showcase 同名能力
  'CSV ↔ Excel 互转': 'interactive:csv-excel',
  'PDF 文本提取': 'interactive:pdf-extract',
  '图片转 PDF': 'interactive:img-to-pdf',
  // ---- W8 速查 ----
  'IP 查询': 'interactive:ip-lookup',
  'DNS 解析查询': 'interactive:dns-lookup',
  端口连通检查: 'interactive:port-check',
  'HTTP 头检查器': 'interactive:http-headers',
  网速测试: 'interactive:speed-test',
  电池状态监控: 'interactive:battery',
  磁盘使用仪表: 'interactive:disk-usage',
  系统信息报告: 'interactive:system-info',
  '进程资源 Top 榜': 'interactive:process-top',
  媒体信息探测: 'interactive:media-info',
  // ---- W9 结果浏览 ----
  '大文件 TopN 查找器': 'interactive:bigfile-topn',
  重复文件清理器: 'interactive:dup-finder',
  重复文件查找: 'interactive:dup-finder', // office 同名能力
  空目录清扫器: 'interactive:empty-dir',
  目录体积报告: 'interactive:dir-size',
  快速文件查找: 'interactive:quick-find',
  目录树打印: 'interactive:tree-print',
  'TODO/FIXME 扫描': 'interactive:todo-scan',
  敏感信息扫描器: 'interactive:secret-scan',
  代码行数统计: 'interactive:loc-stats',
  'CSV 列统计工具': 'interactive:csv-column-stats',
  日志等级统计: 'interactive:log-level-stats',
  'Git 分支报告': 'interactive:git-branches',
  'Git 提交统计': 'interactive:git-commits',
  文本对比工具: 'interactive:text-diff',
  // ---- W10 向导 ----
  两表对比: 'interactive:table-diff',
  '多 Sheet 拆分': 'interactive:sheet-split',
  'Excel 去重合并': 'interactive:dedup-merge',
  批量重命名: 'interactive:batch-rename',
  批量重命名工具: 'interactive:batch-rename', // showcase 同名能力
  文件自动分类: 'interactive:file-classify',
  'SQLite ↔ Excel': 'interactive:sqlite-export',
  // ---- W11 ffmpeg 构建器 ----
  视频压缩: 'interactive:video-compress',
  视频格式转换: 'interactive:video-convert',
  视频合并: 'interactive:video-merge',
  '视频转 GIF': 'interactive:video-to-gif',
  视频截图: 'interactive:video-shot',
  去除音轨: 'interactive:remove-audio',
  音视频裁剪: 'interactive:av-trim',
  音量调整: 'interactive:volume-adjust',
  提取音频: 'interactive:extract-audio',
  音频压缩转码: 'interactive:audio-compress',
  批量转码: 'interactive:batch-transcode',
  // ---- W12 Office 改造 ----
  'Excel 建表入门': 'interactive:excel-build',
  'Excel 读取与遍历': 'interactive:excel-build', // 教学演示 → 建表页覆盖其能力
  'Excel 样式': 'interactive:excel-style',
  'Excel 公式与汇总': 'interactive:excel-formula',
  'Excel 内嵌图表': 'interactive:excel-chart',
  冻结表头: 'interactive:excel-freeze',
  条件格式: 'interactive:excel-condfmt',
  'Excel 数据排序': 'interactive:excel-sort',
  工作表保护: 'interactive:excel-protect',
  单元格批注: 'interactive:excel-comment',
  合并单元格表头: 'interactive:excel-merge-header',
  'Word 文档生成': 'interactive:word-doc',
  'Word 表格': 'interactive:word-table',
  'Word 批量函件': 'interactive:word-letters',
  'PPT 幻灯片生成': 'interactive:ppt-slides',
  文本日报生成: 'interactive:daily-report',
  'Markdown 待办清单': 'interactive:md-todo',
  邮件构造与落盘: 'interactive:mail-draft',
  库存盘点脚本: 'interactive:stock-inventory',
  // ---- W13 增补 ----
  编码修复器: 'interactive:encoding-fix',
  二维码生成器: 'interactive:qrcode-gen',
  // ---- W12/W13 漏映射补全 ----
  文件变更监听: 'interactive:file-watch',
  站点可用性监控: 'interactive:site-monitor',
  'URL 批量体检': 'interactive:site-monitor',
  'YAML ↔ JSON 互转': 'interactive:yaml-json',
  'Excel 透视汇总': 'interactive:pivot',
  跨表关联: 'interactive:cross-join',
  数据校验: 'interactive:data-validate',
  // ---- W14 终局补齐 ----
  哈希校验器: 'interactive:hash-checker',
  网页正文提取: 'interactive:web-article',
  统一压缩解压器: 'interactive:archive-tool',
  临时文件清理器: 'interactive:temp-cleaner',
  目录打包备份: 'interactive:dir-backup',
  日志轮转: 'interactive:log-rotate',
  目录同步器: 'interactive:dir-sync',
  敏感文件粉碎器: 'interactive:file-shredder',
  'Word 插入图片': 'interactive:word-image',
  'PPT 数据表': 'interactive:ppt-data-table',
  花销记账本: 'interactive:expense-summary',
  // ---- 日期计算器（专属页）----
  日期计算: 'interactive:date-calculator'
}

// ---------------------------------------------------------------------------
// bulk_viz 图族路由（画廊卡片 → 图族交互页）
// 变体 id 形如 topics_viz-bar-d8；d1~d12 与 12 种内置数据模式一一对应
// （生成器与各图族页 MODE_FIELD 同序：d1=正弦加噪 … d12=平方增长），路由时按变体预选。
// ---------------------------------------------------------------------------

/** 图族代码（id 中段）→ 交互页面 id。W17 图族页为主，line/pie/hist 落工具箱既有图表页。 */
export const VIZ_FAMILY_TO_INTERACTIVE: Record<string, string> = {
  bar: 'interactive:viz-bar',
  scatter: 'interactive:viz-scatter',
  step: 'interactive:viz-step',
  area: 'interactive:viz-area',
  stackplot: 'interactive:viz-area', // 堆叠面积与面积图同族归并
  errorbar: 'interactive:viz-errbar',
  stem: 'interactive:viz-stem',
  'dual-axis': 'interactive:viz-dualaxis',
  'twin-styles': 'interactive:viz-dualaxis', // 双轴样式与双轴对比同族归并
  'smooth-multiline': 'interactive:viz-multiseries',
  polar: 'interactive:viz-polar-rose',
  radar: 'interactive:viz-radar',
  box: 'interactive:viz-box',
  violin: 'interactive:viz-violin',
  hexbin: 'interactive:viz-hexbin',
  barh: 'interactive:viz-hbar',
  'log-scale': 'interactive:viz-log',
  annotation: 'interactive:viz-annotate',
  inset: 'interactive:viz-inset',
  'style-grid': 'interactive:viz-grid',
  heatmap: 'interactive:viz-heatmap',
  contour: 'interactive:viz-contour-filled',
  surface3d: 'interactive:viz-surface-3d',
  scatter3d: 'interactive:viz-scatter-3d',
  wireframe3d: 'interactive:viz-wireframe-3d',
  bar3d: 'interactive:viz-bar-3d',
  // W17 未覆盖的图族 → 工具箱既有图表页兜底
  line: 'interactive:chart-line',
  pie: 'interactive:chart-pie',
  hist: 'interactive:直方图'
}

/** 变体序号 → 内置数据模式 value（越界返回 null，页面回落默认模式） */
const VIZ_D_TO_MODE: Record<string, string> = {
  '1': 'sine',
  '2': 'linear',
  '3': 'exp',
  '4': 'random',
  '5': 'normal',
  '6': 'pulse',
  '7': 'step',
  '8': 'bimodal',
  '9': 'sawtooth',
  '10': 'spike',
  '11': 'sparse',
  '12': 'square'
}

const VIZ_ID_RE = /^topics_viz-(.+)-d(\d+)$/

export interface VizVariant {
  /** 图族代码（id 中段，如 bar / dual-axis / smooth-multiline） */
  family: string
  /** 变体序号 d1~d12 */
  n: number
  /** 对应内置数据模式 value；d 越界时为 null */
  mode: string | null
}

/** 解析 bulk_viz 图族变体（按 id，与内置库 JSON 的 id 生成规则同源）；非变体返回 null */
export function vizVariantOf(ex: VExample | null | undefined): VizVariant | null {
  if (!ex) return null
  const m = VIZ_ID_RE.exec(ex.id)
  if (!m) return null
  return { family: m[1], n: Number(m[2]), mode: VIZ_D_TO_MODE[m[2]] ?? null }
}

/** 目录条目 → 交互页面 id（标题表 → 图族表两级解析；无映射返回 null） */
export function interactiveIdForExample(ex: VExample | null | undefined): string | null {
  if (!ex) return null
  const title = (ex.title || ex.name || '').replace(/\.py$/i, '').trim()
  const byTitle = TITLE_TO_INTERACTIVE[title]
  if (byTitle) return byTitle
  const variant = vizVariantOf(ex)
  return variant ? (VIZ_FAMILY_TO_INTERACTIVE[variant.family] ?? null) : null
}

/** 当前交互页面（schema 驱动）对应的同能力目录条目；无则 null */
export const cliExampleOfCurrentPage = computed<VExample | null>(() => {
  const id = selectedId.value
  if (!id) return null
  const schemaTitle = getToolSchema(id)?.title
  if (!schemaTitle) return null
  return examples.value.find((e) => TITLE_TO_INTERACTIVE[e.title || ''] === id) ?? null
})
