// interactive-mapping.ts：目录工具条目 ↔ 交互页面的映射（W14 终局批）。
// 凡交互页面已覆盖其能力的 CLI/目录条目，卡片点击直接路由到交互页面
// （CLI 详情仍可从交互页头部的「CLI 源码」按钮进入——双向可达）。
// 映射键 = 目录条目标题（与内置库 JSON 的 title 一致，生成器/手改标题需同步本表）。
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
  'gitignore 生成器': 'interactive:interactive:gitignore',
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

/** 目录条目 → 交互页面 id（无映射返回 null） */
export function interactiveIdForExample(ex: VExample | null | undefined): string | null {
  if (!ex) return null
  const title = (ex.title || ex.name || '').replace(/\.py$/i, '').trim()
  return TITLE_TO_INTERACTIVE[title] ?? null
}

/** 当前交互页面（schema 驱动）对应的同能力目录条目；无则 null */
export const cliExampleOfCurrentPage = computed<VExample | null>(() => {
  const id = selectedId.value
  if (!id) return null
  const schemaTitle = getToolSchema(id)?.title
  if (!schemaTitle) return null
  return examples.value.find((e) => TITLE_TO_INTERACTIVE[e.title || ''] === id) ?? null
})
