// 多维筛选引擎纯函数测试（零依赖，node tests/test_filter_engine.mjs）
// 重点：各维度必须 AND 组合，禁止「搜索命中就短路返回」类回归。
// 源码：electron-prototype/electron/src/renderer/src/filter-engine.ts（经 renderer-loader 转译加载）
import assert from 'node:assert/strict'
import { createRendererLoader } from './renderer-loader.mjs'

const FE = createRendererLoader().load('filter-engine')

let passed = 0
function test(name, fn) {
  fn()
  passed += 1
  console.log(`  ✓ ${name}`)
}

// ---------------------------------------------------------------------------
test('extractImportTags: 抽取第三方库、过滤标准库与相对导入、去重', () => {
  const code = [
    'import os',
    'import sys',
    'import numpy as np',
    'from pandas import DataFrame',
    'from .helpers import x',
    'import numpy', // 重复
    'from PIL import Image'
  ].join('\n')
  assert.deepEqual(FE.extractImportTags(code), ['numpy', 'pandas', 'pil'])
  assert.deepEqual(FE.extractImportTags(''), [])
  assert.deepEqual(FE.extractImportTags(null), [])
})

test('allTagsOf: 元数据标签与 import 标签合并去重、统一小写', () => {
  const ex = { tags: ['NumPy', 'demo'], code: 'import numpy\nimport requests' }
  assert.deepEqual(FE.allTagsOf(ex).sort(), ['demo', 'numpy', 'requests'])
})

test('buildRunStatusIndex: 倒序历史（最新在前）中同一示例只取最新一条', () => {
  const idx = FE.buildRunStatusIndex([
    { id: 'b', ok: false, ts: '2026-09-09T12:00:00' },
    { id: 'a', ok: true, ts: '2026-09-09T11:00:00' }, // 最新
    { id: 'a', ok: false, ts: '2026-09-09T10:00:00' }
  ])
  assert.equal(idx.get('a'), 'ok')
  assert.equal(idx.get('b'), 'failed')
  assert.equal(FE.buildRunStatusIndex(null).size, 0)
})

test('normalizeQuery: 缺省补齐与非法运行状态回退 all', () => {
  assert.deepEqual(FE.normalizeQuery(undefined), {
    category: 'all',
    favOnly: false,
    runStatus: 'all',
    runnable: 'all',
    tags: [],
    tagsAny: [],
    q: '',
    theme: 'all',
    minQuality: 0
  })
  assert.equal(FE.normalizeQuery({ runStatus: 'weird' }).runStatus, 'all')
  assert.equal(FE.normalizeQuery({ runnable: 'weird' }).runnable, 'all')
  assert.equal(FE.normalizeQuery({ q: '  ABC ' }).q, 'abc')
  assert.equal(FE.normalizeQuery({ minQuality: -5 }).minQuality, 0)
  assert.equal(FE.normalizeQuery({ theme: '' }).theme, 'all')
})

// ---------------------------------------------------------------------------
// 组合逻辑回归：任何一维不满足都必须 false，不能被其他维度命中短路
// ---------------------------------------------------------------------------
const SAMPLE = [
  { id: 'a', name: 'hello.py', category: 'topics', tags: ['demo'], code: "import numpy\nprint('hi')" },
  { id: 'b', name: 'net.py', category: 'tools', tags: ['web'], code: 'import requests\n# crawl' },
  { id: 'c', name: 'chart.py', category: 'topics', tags: ['viz'], code: 'import matplotlib\nimport numpy' }
]
const fav = new Set(['a'])
const runStatus = new Map([
  ['a', 'ok'],
  ['b', 'failed']
  // c 从未运行
])

test('分类维度：category 不匹配即使全文命中也排除', () => {
  const got = FE.filterExamples(SAMPLE, { category: 'tools', q: 'numpy' }, { favorites: fav, runStatus })
  // a/c 含 numpy 但分类不是 tools → 全部排除（防搜索短路）
  assert.deepEqual(
    got.map((e) => e.id),
    []
  )
})

test('收藏维度：favOnly 只保留收藏集合内', () => {
  const got = FE.filterExamples(SAMPLE, { favOnly: true }, { favorites: fav, runStatus })
  assert.deepEqual(
    got.map((e) => e.id),
    ['a']
  )
})

test('运行状态：ok/failed/never 正确分流', () => {
  assert.deepEqual(
    FE.filterExamples(SAMPLE, { runStatus: 'ok' }, { favorites: fav, runStatus }).map((e) => e.id),
    ['a']
  )
  assert.deepEqual(
    FE.filterExamples(SAMPLE, { runStatus: 'failed' }, { favorites: fav, runStatus }).map((e) => e.id),
    ['b']
  )
  assert.deepEqual(
    FE.filterExamples(SAMPLE, { runStatus: 'never' }, { favorites: fav, runStatus }).map((e) => e.id),
    ['c']
  )
})

test('标签维度：多标签 AND；自动 import 标签同样可筛', () => {
  // numpy 标签命中 a、c；matplotlib 只命中 c；AND 后只剩 c
  const got = FE.filterExamples(SAMPLE, { tags: ['numpy', 'matplotlib'] }, { favorites: fav, runStatus })
  assert.deepEqual(
    got.map((e) => e.id),
    ['c']
  )
})

test('tagsAny 维度：任一命中即放行（分区下钻 OR 语义），大小写不敏感', () => {
  // web 只命中 b、viz 只命中 c → OR 并集 b+c；a 两边都不中
  const got = FE.filterExamples(SAMPLE, { tagsAny: ['web', 'viz'] }, { favorites: fav, runStatus })
  assert.deepEqual(
    got.map((e) => e.id),
    ['b', 'c']
  )
  // import 自动标签同样参与命中（b 的代码 import requests）
  assert.equal(FE.matchExample(SAMPLE[1], { tagsAny: ['REQUESTS'] }, { favorites: fav, runStatus }), true)
  // 空数组 = 不筛
  assert.equal(FE.filterExamples(SAMPLE, { tagsAny: [] }, { favorites: fav, runStatus }).length, 3)
  // 与 AND 标签可叠加：tags 收紧到交集
  const both = FE.filterExamples(SAMPLE, { tags: ['numpy'], tagsAny: ['viz', 'web'] }, { favorites: fav, runStatus })
  assert.deepEqual(
    both.map((e) => e.id),
    ['c']
  )
})

test('五维 AND 组合：收藏 + 运行成功 + numpy 标签 + 名称', () => {
  const got = FE.filterExamples(
    SAMPLE,
    { category: 'topics', favOnly: true, runStatus: 'ok', tags: ['numpy'], q: 'hello' },
    { favorites: fav, runStatus }
  )
  assert.deepEqual(
    got.map((e) => e.id),
    ['a']
  )
  // 把全文换成不存在的词 → 即使其他维度全中也必须为空
  assert.equal(
    FE.matchExample(
      SAMPLE[0],
      { favOnly: true, runStatus: 'ok', tags: ['numpy'], q: 'zzz' },
      { favorites: fav, runStatus }
    ),
    false
  )
})

test('全文搜索：名称/标签/代码三通道', () => {
  assert.equal(FE.matchExample(SAMPLE[1], { q: 'requests' }, {}), true) // 代码
  assert.equal(FE.matchExample(SAMPLE[0], { q: 'DEMO' }, {}), true) // 标签（大小写不敏感）
  assert.equal(FE.matchExample(SAMPLE[2], { q: 'chart' }, {}), true) // 名称
})

test('buildTagFacets: 按除标签外条件统计并倒序', () => {
  const facets = FE.buildTagFacets(SAMPLE, { category: 'topics' }, { favorites: fav, runStatus })
  const numpy = facets.find((f) => f.tag === 'numpy')
  assert.equal(numpy.count, 2) // a、c
  // tools 的 requests 不计入（category=topics）
  assert.equal(
    facets.find((f) => f.tag === 'requests'),
    undefined
  )
})

// ---------------------------------------------------------------------------
// v0.6 新维度：主题 / 质量分 / 排序
// ---------------------------------------------------------------------------
const THEMED = [
  { id: 't1', name: 'turtle_star.py', category: 'topics', code: 'import turtle', quality_score: 92 },
  { id: 't2', name: 'game.py', category: 'topics', code: 'import pygame', quality_score: 75 },
  { id: 't3', name: 'plot.py', category: 'topics', code: 'import matplotlib', quality_score: 58 }
]
const themeMatchers = {
  turtle: (ex) => /turtle/.test(ex.code || ''),
  games: (ex) => /pygame/.test(ex.code || ''),
  viz: (ex) => /matplotlib/.test(ex.code || '')
}

test('主题维度：themeMatcher 命中才保留，all 不过滤', () => {
  const got = FE.filterExamples(THEMED, { theme: 'turtle' }, { themeMatchers })
  assert.deepEqual(
    got.map((e) => e.id),
    ['t1']
  )
  // 未注册的 matcher key：不过滤（保守行为）
  assert.equal(FE.filterExamples(THEMED, { theme: 'unknown' }, { themeMatchers }).length, 3)
  assert.equal(FE.filterExamples(THEMED, { theme: 'all' }, { themeMatchers }).length, 3)
})

test('质量分维度：minQuality 下限 AND 组合，与主题可叠加', () => {
  assert.deepEqual(
    FE.filterExamples(THEMED, { minQuality: 80 }, { themeMatchers }).map((e) => e.id),
    ['t1']
  )
  assert.deepEqual(
    FE.filterExamples(THEMED, { minQuality: 60, theme: 'games' }, { themeMatchers }).map((e) => e.id),
    ['t2']
  )
  // 无 quality_score 字段按 0 处理
  assert.deepEqual(
    FE.filterExamples([{ id: 'x', name: 'x.py', category: 'topics' }], { minQuality: 1 }, {}).map((e) => e.id),
    []
  )
})

test('sortExamples: 质量分降序（缺省按 0）与名称排序', () => {
  const list = [
    { id: 'a', name: 'b.py', quality_score: 50 },
    { id: 'b', name: 'a.py', quality_score: 90 },
    { id: 'c', name: 'c.py' }
  ]
  assert.deepEqual(
    FE.sortExamples(list, 'quality_desc', {}).map((e) => e.id),
    ['b', 'a', 'c']
  )
  assert.deepEqual(
    FE.sortExamples(list, 'name', {}).map((e) => e.id),
    ['b', 'a', 'c']
  ) // a.py < b.py < c.py
})

test('sortExamples: last_run 依赖 ctx.lastRunAt，未运行排最后', () => {
  const list = [
    { id: 'a', name: 'a.py' },
    { id: 'b', name: 'b.py' },
    { id: 'c', name: 'c.py' }
  ]
  const ctx = {
    lastRunAt: new Map([
      ['b', 200],
      ['a', 100]
    ])
  }
  assert.deepEqual(
    FE.sortExamples(list, 'last_run', ctx).map((e) => e.id),
    ['b', 'a', 'c']
  )
})

test('buildLastRunIndex: 最新在前，同一示例只取第一条，非法 ts 记 0', () => {
  const idx = FE.buildLastRunIndex([
    { id: 'a', ts: '2026-09-09T12:00:00Z' },
    { id: 'a', ts: '2026-09-09T11:00:00Z' },
    { id: 'b', ts: 'not-a-date' }
  ])
  assert.equal(idx.size, 2)
  assert.equal(idx.get('a'), Date.parse('2026-09-09T12:00:00Z'))
  assert.equal(idx.get('b'), 0)
  assert.equal(FE.buildLastRunIndex(null).size, 0)
})

console.log(`\nfilter-engine: ${passed} 个测试全部通过`)

// ---------------------------------------------------------------------------
test('matchExample: 可运行性维度按 run_status 精确匹配', () => {
  const missing = { id: 'm', name: 'm.py', category: 'json', run_status: 'missing_deps' }
  const ok = { id: 'r', name: 'r.py', category: 'json', run_status: 'runnable' }
  const unknown = { id: 'u', name: 'u.py', category: 'json' }
  assert.equal(FE.matchExample(missing, { runnable: 'missing_deps' }), true)
  assert.equal(FE.matchExample(missing, { runnable: 'runnable' }), false)
  assert.equal(FE.matchExample(ok, { runnable: 'missing_deps' }), false)
  // run_status 缺失（未知）不匹配任何具体状态；all 恒通过
  assert.equal(FE.matchExample(unknown, { runnable: 'runnable' }), false)
  assert.equal(FE.matchExample(unknown, {}), true)
  // 与其他维度 AND 组合：分类 + 可运行性
  assert.equal(FE.matchExample(missing, { runnable: 'missing_deps', category: 'json' }), true)
  assert.equal(FE.matchExample(missing, { runnable: 'missing_deps', category: 'tools' }), false)
})

test('normalizeQuery: 可运行性维度缺省补 all', () => {
  assert.equal(FE.normalizeQuery({}).runnable, 'all')
  assert.equal(FE.normalizeQuery({ runnable: 'empty' }).runnable, 'empty')
})

// ---------------------------------------------------------------------------
test('allTagsOf: 命中 _tagsAll 缓存时不再解析 code（渲染热路径预处理）', () => {
  const ex = { tags: ['meta'], code: 'import requests', _tagsAll: ['cached'] }
  assert.deepEqual(FE.allTagsOf(ex), ['cached'])
  // 无缓存时回退到实时计算
  assert.deepEqual(FE.allTagsOf({ tags: ['meta'], code: 'import requests' }).sort(), ['meta', 'requests'])
})

test('matchExample: 全文搜索命中 _codeLower 预处理缓存；无缓存时回退实时小写化', () => {
  // 预处理缓存：q 在 _codeLower 中命中
  const ex = { id: 'a', name: 'a.py', category: 'json', code: 'PRINT(1)', _codeLower: 'print(1)' }
  assert.equal(FE.matchExample(ex, { q: 'print' }), true)
  // q 在 normalizeQuery 中已小写化，与 _codeLower（小写）比较语义一致
  assert.equal(FE.matchExample(ex, { q: 'PRINT' }), true)
  // 无缓存：实时 toLowerCase 兜底
  const ex2 = { id: 'b', name: 'b.py', category: 'json', code: 'PRINT(1)' }
  assert.equal(FE.matchExample(ex2, { q: 'print' }), true)
})

test('matchExample: 服务端代码命中集参与全文匹配（v2 列表不含 code）', () => {
  // 列表不再下发 code：客户端匹配不到，命中由 sidecar 检索给出（契约 §5）
  const ex = { id: 'c', name: 'c.py', category: 'json' }
  assert.equal(FE.matchExample(ex, { q: 'randint' }), false)
  assert.equal(FE.matchExample(ex, { q: 'randint' }, { codeHitIds: new Set(['c']) }), true)
  // 命中集只放行命中项，不误伤其它条目
  const other = { id: 'd', name: 'd.py', category: 'json' }
  assert.equal(FE.matchExample(other, { q: 'randint' }, { codeHitIds: new Set(['c']) }), false)
  // 空白查询不因命中集放行（查询为空即不过滤）
  assert.equal(FE.matchExample(other, { q: '' }, { codeHitIds: new Set(['c']) }), true)
})
