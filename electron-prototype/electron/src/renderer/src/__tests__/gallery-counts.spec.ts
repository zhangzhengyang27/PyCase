// 画廊池主题计数派生（smoke 走查期望值来源，electron 无关故在 vitest 侧测）：
// 期望值已从手写 FROZEN_THEMES 冻结基线改为运行时从 facts.json 推导——
// 本 spec 用合成夹具钉推导逻辑，再对真实语料只钉结构不变量（不含具体数字，
// 语料增删不需同步本文件；主题漂移由 unmappedThemes 棘轮与 smoke 走查暴露）。
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import { deriveGalleryThemeCounts, isGalleryItem, THEME_SECTION_LABELS } from '../../../../../shared/gallery-counts'

describe('deriveGalleryThemeCounts 合成夹具', () => {
  const items = {
    topics_a: { theme: 'viz' },
    topics_b: { theme: 'viz' },
    topics_c: { theme: 'turtle' },
    topics_d: { theme: null },
    tools_x: { theme: 'viz' },
    hello_y: { theme: 'games' }
  }

  it('tools_ 前缀剥离出池，null 主题跳过，按主题键计数', () => {
    const { counts, poolTotal } = deriveGalleryThemeCounts(items)
    expect(counts).toEqual({ viz: 2, turtle: 1, games: 1 })
    expect(poolTotal).toBe(5)
  })

  it('未映射主题进 unmappedThemes（棘轮：新主题必须显式接线语义表）', () => {
    const { unmappedThemes } = deriveGalleryThemeCounts({ topics_new: { theme: 'web' } })
    expect(unmappedThemes).toEqual(['web'])
  })

  it('isGalleryItem 只豁免 tools_ 前缀', () => {
    expect(isGalleryItem('tools_rename')).toBe(false)
    expect(isGalleryItem('topics_basics-fizzbuzz-1')).toBe(true)
    expect(isGalleryItem('hello_world')).toBe(true)
  })

  it('当前全量主题键都有分区名映射（防语义表与语料脱节的双向锚）', () => {
    expect(Object.keys(THEME_SECTION_LABELS).sort()).toEqual(['games', 'images', 'opencv', 'turtle', 'viz'])
  })
})

describe('真实 facts.json 结构不变量', () => {
  const facts = JSON.parse(readFileSync(join(process.cwd(), '../../json_examples/facts.json'), 'utf-8'))

  it('池内条目数 = 非 tools_ 前缀条目数，主题成员合计 ≤ 池，且无未映射主题', () => {
    const { counts, poolTotal, unmappedThemes } = deriveGalleryThemeCounts(facts.items)
    const nonTools = Object.keys(facts.items).filter((id) => isGalleryItem(id)).length
    expect(poolTotal).toBe(nonTools)
    expect(unmappedThemes).toEqual([])
    expect(Object.values(counts).reduce((a, b) => a + b, 0)).toBeLessThanOrEqual(poolTotal)
  })
})
