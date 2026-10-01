// 渲染层 utils.ts 纯函数单元测试（原 history/favorites 模块已随旧渲染层移除，Vue 层等价逻辑由组件承担）
// 通过 renderer-loader 把 TS 转译为 CJS 加载真实源码，
// 并以 mock 替换 './state' / './app' / './sidecar-client'（DOM/IPC 副作用模块）。
import { createRendererLoader } from './renderer-loader.mjs'

// persistHistory/persistFavorites 完成后会触达 DOM（更新徽章/chip），注入最小 mock
globalThis.document = {
  getElementById: () => null,
  querySelectorAll: () => [],
  createElement: () => ({
    className: '',
    textContent: '',
    innerHTML: '',
    title: '',
    classList: { toggle() {}, add() {}, remove() {} },
    addEventListener() {},
    appendChild() {}
  }),
  body: { appendChild() {} },
  addEventListener() {},
  removeEventListener() {}
}

// app.ts 依赖图含 Monaco/IPC，测试中以空实现替身（被测代码只做 typeof 存在性检查或调用）
const APP_STUBS = {
  selectExample() {},
  runExample() {},
  switchView() {},
  loadExamples() {},
  applyAllFilters() {},
  applyFilters() {},
  renderTree() {},
  renderToolGrid() {}
}

/** 每个 harnese 独立的 mock state/api 与加载器（互不串状态） */
function makeHarness() {
  const state = {
    runHistory: [],
    favorites: new Set(),
    favOnly: false,
    selectedId: null,
    runStatusIndex: new Map()
  }
  const els = {} // 真实 state 模块同时导出 els（DOM 引用表）；测试环境置空即可
  const api = {
    storeGet: async () => null,
    storeSet: async () => {}
  }
  const loader = createRendererLoader({
    './state': { state, els, isThemeView: () => false },
    './app': APP_STUBS,
    './sidecar-client': { api }
  })
  return { state, api, loader }
}

// ---------------------------------------------------------------------------
// utils.ts 测试（splitArgs / 质量与状态徽章的 v2 口径）
// ---------------------------------------------------------------------------
const { loader: utilsLoader } = makeHarness()
const utils = utilsLoader.load('utils')

// splitArgs：空格分隔、引号成组、空串参数
console.assert(JSON.stringify(utils.splitArgs('')) === '[]', 'splitArgs 空串')
console.assert(JSON.stringify(utils.splitArgs('  ')) === '[]', 'splitArgs 纯空白')
console.assert(
  JSON.stringify(utils.splitArgs('--width 100 --name demo')) === JSON.stringify(['--width', '100', '--name', 'demo']),
  'splitArgs 普通拆分'
)
console.assert(
  JSON.stringify(utils.splitArgs('--title \'hello world\' --msg "a b"')) ===
    JSON.stringify(['--title', 'hello world', '--msg', 'a b']),
  'splitArgs 单双引号成组'
)
console.assert(
  JSON.stringify(utils.splitArgs("--empty '' tail")) === JSON.stringify(['--empty', '', 'tail']),
  'splitArgs 引号空串保留为参数'
)
console.assert(
  JSON.stringify(utils.splitArgs('a\tb  c')) === JSON.stringify(['a', 'b', 'c']),
  'splitArgs 制表符与多空格'
)

// qualityTextCls：低于 60 分才用琥珀，其余用中性色（v2 收敛为两档）
console.assert(utils.qualityTextCls(92) === 'text-ink-mute', 'qualityTextCls 高分中性')
console.assert(utils.qualityTextCls(70) === 'text-ink-mute', 'qualityTextCls 中分中性')
console.assert(utils.qualityTextCls(30) === 'text-warn', 'qualityTextCls 低分琥珀')
console.assert(utils.qualityTextCls(undefined) === 'text-warn', 'qualityTextCls 缺省按 0（低分）')

// runStatusLabel/runStatusBadgeCls/runStatusHint：可运行性状态徽章
console.assert(utils.runStatusLabel('missing_deps') === '缺依赖', 'runStatusLabel 缺依赖')
console.assert(utils.runStatusLabel('broken') === '语法损坏', 'runStatusLabel 语法损坏')
console.assert(utils.runStatusLabel('unknown_x') === '', 'runStatusLabel 未知状态返回空')
console.assert(utils.runStatusLabel(undefined) === '', 'runStatusLabel undefined 返回空')
// v2 状态语言 = 彩色圆点（runStatusDotCls）+ 中性文字（仅 risky 保留红字）
console.assert(utils.runStatusDotCls('missing_deps') === 'bg-warn', '圆点 缺依赖琥珀')
console.assert(utils.runStatusDotCls('empty') === utils.runStatusDotCls('broken'), '圆点 空壳与损坏同灰档')
console.assert(utils.runStatusDotCls('risky') === 'bg-danger', '圆点 高危红')
console.assert(utils.runStatusDotCls('runnable') === 'bg-ok', '圆点 可运行绿')
console.assert(utils.runStatusTextCls('risky') === 'text-danger', '文字 仅高危红')
console.assert(utils.runStatusTextCls('missing_deps') === 'text-ink-mute', '文字 其余中性')
console.assert(utils.runStatusHint('missing_deps').includes('ImportError'), 'runStatusHint 缺依赖提示')
console.assert(utils.runStatusHint('risky').includes('沙箱'), 'runStatusHint 高危提示非沙箱边界')
console.assert(utils.runStatusHint(undefined) === '', 'runStatusHint undefined 返回空')

// escapeHtml：属性上下文安全——引号必须转义，否则 data-xxx="${...}" 可被突破注入事件处理器
console.assert(utils.escapeHtml('a"b') === 'a&quot;b', 'escapeHtml 双引号')
console.assert(utils.escapeHtml("a'b") === 'a&#39;b', 'escapeHtml 单引号')
console.assert(utils.escapeHtml('a&b') === 'a&amp;b', 'escapeHtml &')
console.assert(
  utils.escapeHtml('<img src=x onerror=alert(1)>') === '&lt;img src=x onerror=alert(1)&gt;',
  'escapeHtml 尖括号'
)
console.assert(utils.escapeHtml('') === '', 'escapeHtml 空串')
console.assert(utils.escapeHtml(null) === '', 'escapeHtml null 兜底')

console.log('renderer-utils: 全部断言通过')

// statusBadgeOf：负面徽章口径收拢（DetailPage/ExampleCard/ExampleListItem 三处同源，审计 P2）
console.assert(utils.statusBadgeOf('missing_deps') === 'missing_deps', 'statusBadgeOf 缺依赖保留')
console.assert(utils.statusBadgeOf('broken') === 'broken', 'statusBadgeOf 语法损坏保留')
console.assert(utils.statusBadgeOf('empty') === 'empty', 'statusBadgeOf 空壳保留')
console.assert(utils.statusBadgeOf('runnable') === '', 'statusBadgeOf runnable 让位正向展示')
console.assert(utils.statusBadgeOf('risky') === '', 'statusBadgeOf risky 让位高危徽章')
console.assert(utils.statusBadgeOf(undefined) === '', 'statusBadgeOf undefined 返回空')
