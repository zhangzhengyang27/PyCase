// overview.ts 纯函数单元测试：主题互斥分区 + 标签分区 + others 兜底桶 + 质量降序预览
//
// v2 口径：主题判定认服务端下发的 theme_key（列表不含 code，判据在服务端，
// 见 src/themes.ts 与 app/contract_store.py::theme_key）。夹具因此给 theme_key，
// 而不是像 v1 那样塞 code 让前端跑正则。
// 13 分区口径（e59d523）：5 主题 + 7 标签组 + 其他；「综合项目」分区已退役，
// 未命中主题/标签组的条目（含 projects 分类）一律落 others。
import { createRendererLoader } from './renderer-loader.mjs'

const { assignSections, TAG_SECTIONS, tagSectionLabel, SECTION_CATALOG, sectionLabelOf } =
  createRendererLoader().load('overview')

function ex(id, { theme = null, name = id, tags = [], quality } = {}) {
  return { id, name, category: 'topics', path: `x/${id}`, theme_key: theme, tags, quality_score: quality }
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

console.log('assignSections')

// 1. 结构分区（空库时 others 为空则省略：5 主题 + 2 标签组）
{
  const sections = assignSections([])
  check('空库返回 5 主题 + 2 标签组（others 省略）', sections.length === 5 + TAG_SECTIONS.length)
  check(
    "标签组全部带 tags 与 kind='tags'",
    sections.filter((s) => s.kind === 'tags').every((s) => Array.isArray(s.tags) && s.tags.length > 0)
  )
  check(
    "主题分区 kind='theme'",
    sections.slice(0, 5).every((s) => s.kind === 'theme')
  )
  check('others 为空时省略', !sections.some((s) => s.key === 'others'))
}

// 2. 互斥分配：一张卡只出现在一个分区（THEMES 顺序 first-match）
{
  const examples = [
    ex('t1', { theme: 'turtle' }),
    ex('g1', { theme: 'games' }),
    ex('cv1', { theme: 'opencv' }),
    ex('pil1', { theme: 'images' }),
    ex('viz1', { theme: 'viz' }),
    ex('plain1', {})
  ]
  const sections = assignSections(examples)
  const all = sections.flatMap((s) => s.items.map((e) => e.id))
  check('每张卡恰好出现一次', all.length === examples.length && new Set(all).size === examples.length)
  const byKey = Object.fromEntries(sections.map((s) => [s.key, s.items.map((e) => e.id)]))
  check('turtle 卡进 turtle 分区', byKey.turtle.join() === 't1')
  check('pygame 卡进 games 分区', byKey.games.join() === 'g1')
  check('cv2 卡进 opencv 分区', byKey.opencv.join() === 'cv1')
  check('PIL 卡进 images 分区', byKey.images.join() === 'pil1')
  check('matplotlib 卡进 viz 分区', byKey.viz.join() === 'viz1')
  check('无命中卡进 others', byKey.others.join() === 'plain1')
}

// 3. 一张卡只会出现在一个分区（theme_key 由服务端 first-match 定死，客户端按 key 归位）
{
  const sections = assignSections([ex('multi', { theme: 'turtle' }), ex('g2', { theme: 'games' })])
  const inGames = sections.find((s) => s.key === 'games').items.map((e) => e.id)
  const inTurtle = sections.find((s) => s.key === 'turtle').items.map((e) => e.id)
  check('按 theme_key 归位且互斥', inTurtle.join() === 'multi' && inGames.join() === 'g2')
  const unknownKey = assignSections([ex('weird', { theme: 'not-a-theme' })])
  check(
    '未知 theme_key 落 others（不静默吞掉）',
    unknownKey
      .find((s) => s.key === 'others')
      .items.map((e) => e.id)
      .join() === 'weird'
  )
}

// 4. 预览按质量分降序，同分按 id 稳定
{
  const examples = [
    ex('b-low', { theme: 'turtle', quality: 50 }),
    ex('a-high', { theme: 'turtle', quality: 90 }),
    ex('c-high', { theme: 'turtle', quality: 90 })
  ]
  const items = assignSections(examples).find((s) => s.key === 'turtle').items
  check('质量降序 + 同分按 id', items.map((e) => e.id).join() === 'a-high,c-high,b-low')
}

// 5. projects / tools 分类同样参与主题命中（games 谓词排除 projects）；
//    未命中主题/标签组的条目（含 projects 分类）一律落 others（「综合项目」分区已退役）
{
  const examples = [
    { ...ex('proj1', {}), category: 'projects' },
    { ...ex('tool1', { theme: 'games' }), category: 'tools' },
    { ...ex('proj2', { tags: ['flask'] }), category: 'projects' }
  ]
  const sections = assignSections(examples)
  const games = sections.find((s) => s.key === 'games')
  const others = sections.find((s) => s.key === 'others')
  check('projects 未命中主题不再进 games', !games.items.some((e) => e.id === 'proj1'))
  check(
    'tools 命中主题照常进主题区',
    games.items.some((e) => e.id === 'tool1')
  )
  check(
    '未命中主题/标签组的 projects 落 others',
    others.items.map((e) => e.id).join() === 'proj1,proj2'
  )
}

// 6. 标签分区：命中组内任一标签即入区；声明顺序即优先级（多组同时命中取先声明者）
{
  const sections = assignSections([
    ex('a1', { tags: ['python-basics'] }),
    ex('a2', { tags: ['基础'] }),
    ex('both1', { tags: ['python-basics', 'algorithms'] }),
    ex('s1', { tags: ['排序'] }),
    ex('plain1', {})
  ])
  const byKey = Object.fromEntries(sections.map((s) => [s.key, s.items.map((e) => e.id)]))
  check('python-basics 进语言基础区', byKey['tag:basics'].includes('a1'))
  check('中文标签 基础 同样进语言基础区', byKey['tag:basics'].includes('a2'))
  check(
    '双组命中取声明序靠前者（语言基础 > 算法与数据结构）',
    byKey['tag:basics'].includes('both1') && !byKey['tag:algo'].includes('both1')
  )
  check('排序 进算法与数据结构区', byKey['tag:algo'].includes('s1'))
  check('爬虫标签进网络爬虫区', (() => {
    const secs = assignSections([ex('c1', { tags: ['爬虫'] })])
    const bucket = secs.find((s) => s.key === 'tag:crawler')
    return !!bucket && bucket.items.map((e) => e.id).includes('c1')
  })())
  check('无标签且未命中主题进 others', byKey.others.includes('plain1'))
  check('空库时 others 分节不出现', !assignSections([]).some((s) => s.key === 'others'))
}

// 7. tagSectionLabel：结果条范围标题反查
{
  check('组内标签反查分区名', tagSectionLabel(['python-basics']) === '语言基础')
  check('爬虫标签反查网络爬虫分区', tagSectionLabel(['爬虫']) === '网络爬虫')
  check('大小写不敏感', tagSectionLabel(['Python-Basics']) === '语言基础')
  check('未知标签返回 undefined', tagSectionLabel(['no-such-tag']) === undefined)
}

// 8. SECTION_CATALOG：侧栏二级分区菜单的完整元数据（全部 13 项，others 恒在）
{
  check('13 项 = 5 主题 + 7 标签组 + 其他', SECTION_CATALOG.length === 13)
  // 与 assignSections 同序；assignSections 空库省略 others，这里补回正好对齐 13 项
  check(
    '键序与 assignSections 一致（others 恒在末尾）',
    SECTION_CATALOG.map((s) => s.key).join() === [...assignSections([]).map((s) => s.key), 'others'].join()
  )
  check(
    "kind 分布：5 theme + 7 tags + 1 others",
    SECTION_CATALOG.filter((s) => s.kind === 'theme').length === 5 &&
      SECTION_CATALOG.filter((s) => s.kind === 'tags').length === TAG_SECTIONS.length &&
      SECTION_CATALOG.filter((s) => s.kind === 'others').length === 1
  )
  check(
    "标签组项带 tags（下钻/图标解析用）",
    SECTION_CATALOG.filter((s) => s.kind === 'tags').every((s) => Array.isArray(s.tags) && s.tags.length > 0)
  )
  check('others 收尾', SECTION_CATALOG[12].key === 'others')
  check(
    '新域分区四件套齐全且键序稳定',
    sectionLabelOf('tag:crawler') === '网络爬虫' &&
      sectionLabelOf('tag:data') === '数据分析' &&
      sectionLabelOf('tag:db') === '数据库' &&
      sectionLabelOf('tag:web') === 'Web 开发' &&
      sectionLabelOf('tag:async') === '并发与异步' &&
      SECTION_CATALOG.map((s) => s.key).slice(7, 12).join() ===
        'tag:crawler,tag:data,tag:db,tag:web,tag:async'
  )
  check(
    'sectionLabelOf 反查（分区 key → 展示名）',
    sectionLabelOf('tag:basics') === '语言基础' &&
      sectionLabelOf('others') === '其他示例' &&
      sectionLabelOf(null) === undefined &&
      sectionLabelOf('no-such-key') === undefined
  )
}

if (failed) {
  console.error(`\n${failed} 项断言失败`)
  process.exit(1)
}
console.log('\n全部通过')
