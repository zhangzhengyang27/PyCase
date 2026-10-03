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

/** 图族代码（id 中段）→ 路由目标：图表实验室页 + 类型预选。30 图族全量归并进单页。 */
export const VIZ_FAMILY_TO_INTERACTIVE: Record<string, { page: string; type: string }> = {
  bar: { page: 'interactive:viz-lab', type: 'bar' },
  scatter: { page: 'interactive:viz-lab', type: 'scatter' },
  step: { page: 'interactive:viz-lab', type: 'step' },
  area: { page: 'interactive:viz-lab', type: 'area' },
  stackplot: { page: 'interactive:viz-lab', type: 'area' }, // 堆叠面积与面积图同族归并
  errorbar: { page: 'interactive:viz-lab', type: 'errbar' },
  stem: { page: 'interactive:viz-lab', type: 'stem' },
  'dual-axis': { page: 'interactive:viz-lab', type: 'dualaxis' },
  'twin-styles': { page: 'interactive:viz-lab', type: 'dualaxis' }, // 双轴样式与双轴对比同族归并
  'smooth-multiline': { page: 'interactive:viz-lab', type: 'multiseries' },
  polar: { page: 'interactive:viz-lab', type: 'polar-rose' },
  radar: { page: 'interactive:viz-lab', type: 'radar' },
  box: { page: 'interactive:viz-lab', type: 'box' },
  violin: { page: 'interactive:viz-lab', type: 'violin' },
  hexbin: { page: 'interactive:viz-lab', type: 'hexbin' },
  barh: { page: 'interactive:viz-lab', type: 'hbar' },
  'log-scale': { page: 'interactive:viz-lab', type: 'log' },
  annotation: { page: 'interactive:viz-lab', type: 'annotate' },
  inset: { page: 'interactive:viz-lab', type: 'inset' },
  'style-grid': { page: 'interactive:viz-lab', type: 'grid' },
  heatmap: { page: 'interactive:viz-lab', type: 'heatmap' },
  contour: { page: 'interactive:viz-lab', type: 'contour-filled' },
  surface3d: { page: 'interactive:viz-lab', type: 'surface-3d' },
  scatter3d: { page: 'interactive:viz-lab', type: 'scatter-3d' },
  wireframe3d: { page: 'interactive:viz-lab', type: 'wireframe-3d' },
  bar3d: { page: 'interactive:viz-lab', type: 'bar-3d' },
  // W17 未覆盖的图族 → 实验室补齐类型
  line: { page: 'interactive:viz-lab', type: 'line' },
  pie: { page: 'interactive:viz-lab', type: 'pie' },
  hist: { page: 'interactive:viz-lab', type: 'hist' }
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

// ---------------------------------------------------------------------------
// 通用 topics 家族路由（全库示例交互化：「能改的就改」批次）。
// id 形如 topics_<家族><变体尾缀>，尾缀为 -v12 / -s8 / -x1 / -1（家族各异）或无尾缀（单例）。
// 家族键 = 剥掉 topics_ 前缀与变体尾缀后的中段（如 algo-quick-sort / pil-gaussian / turtle-spiral）。
// 变体尾缀只标识同族参数差异，不带数据模式语义（模式预选仅 viz 的 d1~d12 有）。
// ---------------------------------------------------------------------------

const TOPICS_ID_RE = /^topics_(.+?)(?:-[vsx]?\d+)?$/

export interface TopicsFamily {
  /** 家族中段（如 algo-quick-sort / pil-gaussian / turtle-spiral / basics-fizzbuzz） */
  family: string
  /** 变体尾缀里的数字（无尾缀单例为 null） */
  variant: number | null
}

/** 解析 topics 家族（非 viz 变体；viz 走 vizVariantOf）。.py 结尾的 id 先归一化；
 * 解析不出或非 topics id 返回 null */
export function topicsFamilyOf(ex: VExample | null | undefined): TopicsFamily | null {
  if (!ex) return null
  const norm = ex.id.replace(/\.py$/i, '')
  const m = TOPICS_ID_RE.exec(norm)
  if (!m) return null
  const v = /-(?:[vsx])?(\d+)$/.exec(norm)
  return { family: m[1], variant: v ? Number(v[1]) : null }
}

/** 家族中段 → 交互页面 id。仅收录交互页能力确实覆盖该家族的条目（宁缺毋歪曲）。 */
export const TOPICS_FAMILY_TO_INTERACTIVE: Record<string, { page: string; type?: string }> = {
  // ---- 算法可视化（V4/V5 既有页；algo-* 32 变体 + 单例）----
  'algo-binary-search': { page: 'interactive:binary-search' },
  'algo-quick-sort': { page: 'interactive:quick-sort' },
  'algo-lcs': { page: 'interactive:lcs' },
  'algo-dijkstra': { page: 'interactive:dijkstra' },
  'algo-knapsack': { page: 'interactive:knapsack' },
  'algo-union-find': { page: 'interactive:union-find' },
  'algo-collatz': { page: 'interactive:collatz' },
  'algo-gcd-lcm': { page: 'interactive:gcd-lcm' },
  'algo-matrix-rotate': { page: 'interactive:matrix-rotate' },
  // ---- bulk_basics 教学家族（既有页覆盖）----
  'basics-fizzbuzz': { page: 'interactive:fizzbuzz' },
  'basics-prime': { page: 'interactive:prime-sieve' },
  'basics-fibonacci': { page: 'interactive:fibonacci' },
  'basics-wordcount': { page: 'interactive:word-freq' },
  'basics-matrix-mul': { page: 'interactive:matrix-multiply' },
  'basics-regex': { page: 'interactive:regex-tester' },
  // ---- dataviz 明确等价（其余家族待建页后补映射）----
  'data-analysis_dataviz-error-bar': { page: 'interactive:viz-lab', type: 'errbar' },
  'data-analysis_dataviz-log-scale': { page: 'interactive:viz-lab', type: 'log' },
  'data-analysis_dataviz-polar-rose': { page: 'interactive:viz-lab', type: 'polar-rose' },
  'data-analysis_dataviz-scatter-3d': { page: 'interactive:viz-lab', type: 'scatter-3d' },
  'data-analysis_dataviz-surface-3d': { page: 'interactive:viz-lab', type: 'surface-3d' },
  'data-analysis_dataviz-scatter-density': { page: 'interactive:散点密度图' },
  'data-analysis_dataviz-radar-chart': { page: 'interactive:viz-lab', type: 'radar' },
  'data-analysis_dataviz-heatmap-annotated': { page: 'interactive:viz-lab', type: 'heatmap' },
  'data-analysis_dataviz-dual-axis-combo': { page: 'interactive:viz-lab', type: 'dualaxis' },
  'data-analysis_dataviz-line-multi-series': { page: 'interactive:viz-lab', type: 'multiseries' },
  'data-analysis_dataviz-boxplot-multi': { page: 'interactive:viz-lab', type: 'box' },
  'data-analysis_dataviz-histogram-kde': { page: 'interactive:直方图' },
  // ---- sciviz 明确等价 ----
  'data-analysis_sciviz-sciviz-venn-diagram': { page: 'interactive:venn' },
  'data-analysis_sciviz-sciviz-dendrogram': { page: 'interactive:dendrogram' },
  'data-analysis_sciviz-sciviz-wordcloud': { page: 'interactive:wordcloud-chart' },
  'data-analysis_sciviz-sciviz-3d-surface': { page: 'interactive:viz-lab', type: 'surface-3d' },
  'data-analysis_sciviz-sciviz-polar-rose': { page: 'interactive:viz-lab', type: 'polar-rose' },
  'data-analysis_sciviz-sciviz-contour-fields': { page: 'interactive:viz-lab', type: 'contour-filled' },
  // ---- 爬虫中交互页能力确实覆盖的条目（请求/头检查/批量下载/汇率/天气）----
  'crawler-http-get-basic': { page: 'interactive:http-requester' },
  'crawler-http-headers-ua': { page: 'interactive:http-headers' },
  'crawler-http-timeout-retry': { page: 'interactive:http-requester' },
  'crawler-parse-json-api': { page: 'interactive:http-requester' },
  'crawler3-image-batch-download': { page: 'interactive:image-downloader' },
  'crawler3-exchange-rate-api': { page: 'interactive:exchange-rate' },
  'crawler3-open-meteo-weather': { page: 'interactive:weather' },
  // ---- dataviz 高级图表（viz-lab 新类型 + gap 甘特页）----
  'data-analysis_dataviz-grouped-bar': { page: 'interactive:viz-lab', type: 'grouped-bar' },
  'data-analysis_dataviz-stacked-bar': { page: 'interactive:viz-lab', type: 'stacked-bar' },
  'data-analysis_dataviz-bubble-chart': { page: 'interactive:viz-lab', type: 'bubble' },
  'data-analysis_dataviz-correlation-matrix': { page: 'interactive:viz-lab', type: 'correlation' },
  'data-analysis_dataviz-line-confidence-band': { page: 'interactive:viz-lab', type: 'confidence-band' },
  'data-analysis_dataviz-pie-donut': { page: 'interactive:viz-lab', type: 'donut' },
  'data-analysis_dataviz-horizontal-bar-rank': { page: 'interactive:viz-lab', type: 'hbar' },
  'data-analysis_dataviz-gantt-chart': { page: 'interactive:甘特图' },
  // ---- sciviz 出版级（科研绘图实验室 / viz-lab 共享类型）----
  'data-analysis_sciviz-sciviz-ternary': { page: 'interactive:sciviz-lab', type: 'ternary' },
  'data-analysis_sciviz-sciviz-streamplot': { page: 'interactive:sciviz-lab', type: 'streamplot' },
  'data-analysis_sciviz-sciviz-pcolor-fields': { page: 'interactive:sciviz-lab', type: 'pcolor' },
  'data-analysis_sciviz-sciviz-unstructured-mesh': { page: 'interactive:sciviz-lab', type: 'unstructured-mesh' },
  'data-analysis_sciviz-sciviz-slope-graph': { page: 'interactive:sciviz-lab', type: 'slope' },
  'data-analysis_sciviz-sciviz-line-styles': { page: 'interactive:sciviz-lab', type: 'line-styles' },
  'data-analysis_sciviz-sciviz-canvas-axes': { page: 'interactive:sciviz-lab', type: 'canvas-axes' },
  'data-analysis_sciviz-sciviz-complex-axes': { page: 'interactive:sciviz-lab', type: 'complex-axes' },
  'data-analysis_sciviz-sciviz-data-formats': { page: 'interactive:sciviz-lab', type: 'data-formats' },
  'data-analysis_sciviz-sciviz-pandas-plot': { page: 'interactive:sciviz-lab', type: 'pandas-plot' },
  'data-analysis_sciviz-sciviz-3d-profile': { page: 'interactive:sciviz-lab', type: '3d-profile' },
  'data-analysis_sciviz-sciviz-3d-bars': { page: 'interactive:sciviz-lab', type: '3d-bars' },
  'data-analysis_sciviz-sciviz-seaborn-stats': { page: 'interactive:sciviz-lab', type: 'stats-style' },
  'data-analysis_sciviz-sciviz-box-violin': { page: 'interactive:sciviz-lab', type: 'box-violin' },
  'data-analysis_sciviz-sciviz-chord-diagram': { page: 'interactive:sciviz-lab', type: 'chord' },
  'data-analysis_sciviz-sciviz-bar-basics': { page: 'interactive:viz-lab', type: 'bar' },
  'data-analysis_sciviz-sciviz-grouped-bars': { page: 'interactive:viz-lab', type: 'grouped-bar' },
  'data-analysis_sciviz-sciviz-pie-donut': { page: 'interactive:viz-lab', type: 'donut' },
  // ---- bulk_pil 滤镜家族（tool-schemas-pil.ts，画廊专用页）----
  'pil-gaussian': { page: 'interactive:pil-lab', type: 'gaussian' },
  'pil-grayscale': { page: 'interactive:pil-lab', type: 'grayscale' },
  'pil-invert': { page: 'interactive:pil-lab', type: 'invert' },
  'pil-emboss': { page: 'interactive:pil-lab', type: 'emboss' },
  'pil-contour': { page: 'interactive:pil-lab', type: 'contour' },
  'pil-solarize': { page: 'interactive:pil-lab', type: 'solarize' },
  'pil-posterize': { page: 'interactive:pil-lab', type: 'posterize' },
  'pil-mirror': { page: 'interactive:pil-lab', type: 'mirror' },
  'pil-rotate-crop': { page: 'interactive:pil-lab', type: 'rotate-crop' },
  'pil-enhance-quad': { page: 'interactive:pil-lab', type: 'enhance-quad' },
  'pil-gradient-mask': { page: 'interactive:pil-lab', type: 'gradient-mask' },
  'pil-pixelate': { page: 'interactive:pil-lab', type: 'pixelate' },
  // ---- bulk_opencv 处理家族（tool-schemas-opencv.ts）----
  'opencv-canny': { page: 'interactive:cv-lab', type: 'canny' },
  'opencv-threshold': { page: 'interactive:cv-lab', type: 'threshold' },
  'opencv-adaptive': { page: 'interactive:cv-lab', type: 'adaptive' },
  'opencv-morph-open': { page: 'interactive:cv-lab', type: 'morph-open' },
  'opencv-morph-close': { page: 'interactive:cv-lab', type: 'morph-close' },
  'opencv-gradient': { page: 'interactive:cv-lab', type: 'gradient' },
  'opencv-sobel': { page: 'interactive:cv-lab', type: 'sobel' },
  'opencv-laplacian': { page: 'interactive:cv-lab', type: 'laplacian' },
  'opencv-blur-stack': { page: 'interactive:cv-lab', type: 'blur-stack' },
  'opencv-sharpen': { page: 'interactive:cv-lab', type: 'sharpen' },
  'opencv-equalize': { page: 'interactive:cv-lab', type: 'equalize' },
  'opencv-gamma': { page: 'interactive:cv-lab', type: 'gamma' },
  'opencv-rotate': { page: 'interactive:cv-lab', type: 'rotate' },
  'opencv-perspective': { page: 'interactive:cv-lab', type: 'perspective' },
  'opencv-resize-pyramid': { page: 'interactive:cv-lab', type: 'resize-pyramid' },
  'opencv-contours-area': { page: 'interactive:cv-lab', type: 'contours-area' },
  'opencv-hough-lines': { page: 'interactive:cv-lab', type: 'hough-lines' },
  'opencv-distance-transform': { page: 'interactive:cv-lab', type: 'distance-transform' },
  'opencv-bitwise-mix': { page: 'interactive:cv-lab', type: 'bitwise-mix' },
  'opencv-colormap': { page: 'interactive:cv-lab', type: 'colormap' },
  'opencv-edge': { page: 'interactive:cv-lab', type: 'edge' },
  'opencv-colorspace': { page: 'interactive:cv-lab', type: 'colorspace' },
  'opencv-geometric': { page: 'interactive:cv-lab', type: 'geometric' },
  'opencv-histogram': { page: 'interactive:cv-lab', type: 'histogram' },
  'opencv-contours': { page: 'interactive:cv-lab', type: 'edge' }, // 单例轮廓演示 → 边缘组合类型
  // ---- bulk_turtle 图形家族（tool-schemas-turtle.ts）----
  'turtle-spiral': { page: 'interactive:turtle-lab', type: 'spiral' },
  'turtle-spiral-square': { page: 'interactive:turtle-lab', type: 'spiral-square' },
  'turtle-rose': { page: 'interactive:turtle-lab', type: 'rose' },
  'turtle-fractal-tree': { page: 'interactive:turtle-lab', type: 'fractal-tree' },
  'turtle-koch': { page: 'interactive:turtle-lab', type: 'koch' },
  'turtle-sierpinski': { page: 'interactive:turtle-lab', type: 'sierpinski' },
  'turtle-mandala': { page: 'interactive:turtle-lab', type: 'mandala' },
  'turtle-lissajous': { page: 'interactive:turtle-lab', type: 'lissajous' },
  'turtle-phyllotaxis': { page: 'interactive:turtle-lab', type: 'phyllotaxis' },
  'turtle-polygon-ring': { page: 'interactive:turtle-lab', type: 'polygon-ring' },
  'turtle-hex-flower': { page: 'interactive:turtle-lab', type: 'hex-flower' },
  'turtle-butterfly': { page: 'interactive:turtle-lab', type: 'butterfly' },
  'turtle-galaxy': { page: 'interactive:turtle-lab', type: 'galaxy' },
  'turtle-heart': { page: 'interactive:turtle-lab', type: 'heart' },
  'turtle-waves': { page: 'interactive:turtle-lab', type: 'waves' },
  'turtle-rings': { page: 'interactive:turtle-lab', type: 'rings' },
  'turtle-rays': { page: 'interactive:turtle-lab', type: 'rays' },
  'turtle-burst': { page: 'interactive:turtle-lab', type: 'burst' },
  'turtle-dot-field': { page: 'interactive:turtle-lab', type: 'dot-field' },
  'turtle-dragon': { page: 'interactive:turtle-lab', type: 'dragon' },
  'turtle-square-stairs': { page: 'interactive:turtle-lab', type: 'square-stairs' },
  'turtle-staircase-wave': { page: 'interactive:turtle-lab', type: 'staircase-wave' },
  'turtle-honeycomb': { page: 'interactive:turtle-lab', type: 'honeycomb' },
  'turtle-city-skyline': { page: 'interactive:turtle-lab', type: 'city-skyline' },
  'turtle-starfield': { page: 'interactive:turtle-lab', type: 'starfield' },
  'turtle-kaleidoscope': { page: 'interactive:turtle-lab', type: 'kaleidoscope' },
  'turtle-maze-walk': { page: 'interactive:turtle-lab', type: 'maze-walk' },
  'turtle-rainbow-circles': { page: 'interactive:turtle-lab', type: 'rainbow-circles' },
  'turtle-sunflower': { page: 'interactive:turtle-lab', type: 'sunflower' }
}

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

export interface InteractiveRoute {
  /** 交互页面 id */
  page: string
  /** 类型预选（实验室页的类型选择器值）；非实验室页无 */
  type?: string
}

/** 目录条目 → 路由目标（标题表 → viz 图族表 → 通用 topics 家族表三级解析；无映射返回 null） */
export function interactiveRouteForExample(ex: VExample | null | undefined): InteractiveRoute | null {
  if (!ex) return null
  const title = (ex.title || ex.name || '').replace(/\.py$/i, '').trim()
  const byTitle = TITLE_TO_INTERACTIVE[title]
  if (byTitle) return { page: byTitle }
  const variant = vizVariantOf(ex)
  if (variant) return VIZ_FAMILY_TO_INTERACTIVE[variant.family] ?? null
  const fam = topicsFamilyOf(ex)
  return fam ? (TOPICS_FAMILY_TO_INTERACTIVE[fam.family] ?? null) : null
}

/** 目录条目 → 交互页面 id（仅页面，无类型预选；详情页「交互页面」按钮等兼容场景用） */
export function interactiveIdForExample(ex: VExample | null | undefined): string | null {
  return interactiveRouteForExample(ex)?.page ?? null
}

/** 当前交互页面（schema 驱动）对应的同能力目录条目；无则 null */
export const cliExampleOfCurrentPage = computed<VExample | null>(() => {
  const id = selectedId.value
  if (!id) return null
  const schemaTitle = getToolSchema(id)?.title
  if (!schemaTitle) return null
  return examples.value.find((e) => TITLE_TO_INTERACTIVE[e.title || ''] === id) ?? null
})
