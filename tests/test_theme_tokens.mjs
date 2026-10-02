// theme.css 令牌 ↔ 组件类名一致性测试（审计 P1 回归网）
//
// 背景：组件里 40+ 处 border-line-hairline / bg-fill-subtle，而 @theme 里没有
// 对应的 --color-line-hairline / --color-fill-subtle——Tailwind v4 对未映射类名
// 不生成任何 CSS，border-color 回落 currentColor（发丝线变文字色）、bg 完全透明
// （进度条轨道不可见）。这条护栏保证：组件用到的每个语义色类名，都必须能在
// theme.css 的 @theme 块里找到 --color-* 映射，类名与令牌的脱节当场变红。
//
// 算法：语义色家族清单是显式契约（不只是从已有 --color-* 推导）——某个家族可能
// 整体缺失映射（fill 就是这样漏网的），从「已定义颜色」反推永远发现不了它。
import { readFileSync, readdirSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const REPO = join(dirname(fileURLToPath(import.meta.url)), '..')
const RENDERER = join(REPO, 'electron-prototype/electron/src/renderer')
const THEME_CSS = join(RENDERER, 'src/theme.css')

// 1. 从 @theme 块收集已定义的语义色名（--color-* 只在 @theme 出现，全文件扫描即可）
const themeText = readFileSync(THEME_CSS, 'utf8')
const definedColors = new Set([...themeText.matchAll(/--color-([a-z0-9-]+)\s*:/g)].map((m) => m[1]))

// 2. 语义色家族契约：前 17 个来自 @theme 现有命名空间的族首，
//    'fill' 是防「整族缺失」的显式成员——它目前除 bg-fill-subtle 外零映射。
const FAMILIES = new Set([
  'page', 'panel', 'card', 'surface', 'hover', 'pressed', 'subtle', 'inset',
  'sidebar', 'console', 'chip', 'ink', 'accent', 'on', 'ok', 'danger', 'warn',
  'line', 'fill'
])

// 3. 扫描组件与纯函数模块里的色值类用法（.css 走 stylelint 侧、测试桩不在口径内）
function walk(dir) {
  const out = []
  for (const name of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, name.name)
    if (name.isDirectory()) {
      if (name.name === '__tests__') continue
      out.push(...walk(p))
    } else if (/\.(vue|ts)$/.test(name.name)) {
      out.push(p)
    }
  }
  return out
}

// 色值承载工具类：名字捕获到 / 前或引号前为止；允许 border-b-line-* 这类方向前缀
const UTIL_RE = /\b(border|bg|text|divide|ring|fill|stroke|outline|decoration|from|via|to|accent|caret)-([a-z][a-z0-9-]*)/g

const violations = []
for (const file of walk(RENDERER)) {
  const lines = readFileSync(file, 'utf8').split('\n')
  lines.forEach((line, i) => {
    for (const m of line.matchAll(UTIL_RE)) {
      let name = m[2]
      // 方向前缀（border-b-line-*）：剥掉一层再看语义家族
      if (/^[xytrbl]-(?=[a-z])/.test(name)) name = name.slice(2)
      const family = name.split('-')[0]
      if (!FAMILIES.has(family)) continue
      if (!definedColors.has(name)) {
        violations.push({ cls: `${m[1]}-${name}`, loc: `${file.replace(RENDERER + '/', '')}:${i + 1}` })
      }
    }
  })
}

let failed = 0
function check(desc, cond) {
  if (!cond) {
    failed++
    console.error(`  ✗ ${desc}`)
  } else {
    console.log(`  ✓ ${desc}`)
  }
}

console.log('theme.css @theme 映射 ↔ 组件语义色类名')

// 按类名聚合便于读：border-line-hairline ×39（components/ExampleCard.vue:62 …）
const byClass = new Map()
for (const v of violations) {
  if (!byClass.has(v.cls)) byClass.set(v.cls, [])
  byClass.get(v.cls).push(v.loc)
}
for (const [cls, locs] of byClass) {
  console.error(`    漂移 ${cls} ×${locs.length}（如 ${locs[0]}）→ @theme 缺 --color-${cls.replace(/^[a-z]+-/, '')}`)
}

check('语义色家族契约里有 fill / line 等显式成员', FAMILIES.has('fill') && FAMILIES.has('line'))
check(
  violations.length === 0 ? '组件语义色类名全部有 @theme 映射' : `发现 ${violations.length} 处类名无 @theme 映射`,
  violations.length === 0
)

if (failed) {
  console.error(`\n${failed} 项断言失败`)
  process.exit(1)
}
console.log('\n全部通过')

// ---------------------------------------------------------------------------
// 隐形墨水禁令（2026-10-02 事故）：--color-console 映射的是终端**背景**色
// （--bg-console），把 text-console 当文字类用 = 输出与背景同色、肉眼不可见——
// 示例 print 输出在 theme.css v3 后整体隐形（smoke 只断言 textContent 故未拦截）。
// 终端正文请用 text-ink-console（→ --text-console，跟随主题的可读色）。
check('禁令：text-console（背景色当文字色，隐形墨水）不得再出现', (() => {
  const banned = /(^|[^a-z-])text-console(?![a-z-])/
  let used = []
  for (const file of walk(RENDERER)) {
    const src = readFileSync(file, 'utf8')
    if (banned.test(src)) used.push(file.replace(RENDERER + '/', ''))
  }
  if (used.length) console.error('    text-console 出现在: ' + used.join(', '))
  return used.length === 0
})())
check('终端正文类 text-ink-console 已有 @theme 映射', definedColors.has('ink-console'))
check('系统行 text-gutter 已有 @theme 映射（曾漏映射继承容器色）', definedColors.has('gutter'))
