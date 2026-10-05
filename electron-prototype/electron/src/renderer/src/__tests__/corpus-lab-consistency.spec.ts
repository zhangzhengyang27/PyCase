// 语料 ↔ 实验室一致性（2026-10-05 评审 Important 3）：
//   ① 新鲜度——四新域语料母本必须与实验室 pyCode 默认参数输出逐字节一致（改 body 不重烘语料即红）；
//   ② 映射覆盖反查——清单里每个语料 id 必须已路由到对应实验室且类型精确匹配
//      （映射完整性测试只查「映射→已注册」方向，本文件查「语料→必须被映射」反方向）；
//   ③ crawler 家族覆盖——62 条教案中除 5 条语义豁免（2 需浏览器二进制走详情兜底、
//      3 已路由既有真实工具页）外，其余 57 条必须全部路由 crawler-lab。
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import type { FieldValue } from '../interactive-tools'
import { TOPICS_FAMILY_TO_INTERACTIVE } from '../interactive-mapping'
import { CRAWLER_TYPES } from '../tool-schemas-crawler-lab'
import { pandasLabSchema, PANDAS_TYPES } from '../tool-schemas-pandas-lab'
import { sqliteLabSchema, SQLITE_TYPES } from '../tool-schemas-sqlite-lab'
import { webLabSchema, WEB_TYPES } from '../tool-schemas-web-lab'
import { asyncioLabSchema, ASYNC_TYPES } from '../tool-schemas-asyncio-lab'

const ROOT = join(process.cwd(), '../..')
const REPO = 'json_examples'

interface SetSpec {
  manifest: string
  prefix: string
  schema: (typeof pandasLabSchema | typeof sqliteLabSchema | typeof webLabSchema | typeof asyncioLabSchema) & {
    id: string
  }
  types: Array<{ value: string }>
}

const NEW_SETS: SetSpec[] = [
  { manifest: `${REPO}/pandas_examples.json`, prefix: 'pandas', schema: pandasLabSchema, types: PANDAS_TYPES },
  { manifest: `${REPO}/sqlite_examples.json`, prefix: 'sqlite', schema: sqliteLabSchema, types: SQLITE_TYPES },
  { manifest: `${REPO}/web_examples.json`, prefix: 'web', schema: webLabSchema, types: WEB_TYPES },
  { manifest: `${REPO}/asyncio_examples.json`, prefix: 'async', schema: asyncioLabSchema, types: ASYNC_TYPES }
]

function defaultsFor(schema: SetSpec['schema'], type: string): Record<string, FieldValue> {
  const v: Record<string, FieldValue> = { type }
  const fieldList = typeof schema.fields === 'function' ? schema.fields(v) : schema.fields
  for (const f of fieldList) if (v[f.key] === undefined) v[f.key] = f.default
  return v
}

describe('四新域语料 ↔ 实验室一致性', () => {
  for (const set of NEW_SETS) {
    it(`${set.prefix}_examples：母本逐字节同源 + 映射 100% 覆盖且类型精确`, () => {
      const manifest = JSON.parse(readFileSync(join(ROOT, set.manifest), 'utf-8'))
      expect(manifest.examples.length).toBe(set.types.length)
      for (const ex of manifest.examples as Array<{ id: string; file: string }>) {
        // 反查：语料 id → 必须已映射到本实验室且类型精确匹配
        const family = ex.id.replace(/^topics_/, '')
        const route = TOPICS_FAMILY_TO_INTERACTIVE[family]
        expect(route, `语料 ${ex.id} 未被映射路由`).toBeTruthy()
        expect(route!.page).toBe(set.schema.id)
        const type = family.slice(set.prefix.length + 1)
        expect(route!.type).toBe(type)
        expect(
          set.types.some((t) => t.value === type),
          `类型 ${type} 不在实验室注册表`
        ).toBe(true)
        // 新鲜度：母本字节 === pyCode 默认参数输出
        const mother = readFileSync(join(ROOT, REPO, ex.file), 'utf-8')
        expect(mother, `${ex.id} 母本与 pyCode 漂移——重跑语料生成`).toBe(
          set.schema.pyCode(defaultsFor(set.schema, type))
        )
      }
    })
  }
})

describe('crawler 教案家族覆盖', () => {
  const EXEMPT = new Set([
    'crawler3-playwright-browser', // 需浏览器二进制，详情页兜底
    'crawler3-selenium-login-pattern', // 同上
    'crawler3-image-batch-download', // 已路由 image-downloader 真实工具页
    'crawler3-exchange-rate-api', // 已路由 exchange-rate
    'crawler3-open-meteo-weather' // 已路由 weather
  ])

  it('62 条教案中除 5 条豁免外全部路由 crawler-lab 且类型存在', () => {
    const manifest = JSON.parse(readFileSync(join(ROOT, `${REPO}/crawler_examples.json`), 'utf-8'))
    const typeValues = new Set(CRAWLER_TYPES.map((t) => t.value))
    let mapped = 0
    for (const ex of manifest.examples as Array<{ id: string }>) {
      const family = ex.id.replace(/^topics_/, '')
      if (EXEMPT.has(family)) continue
      const route = TOPICS_FAMILY_TO_INTERACTIVE[family]
      expect(route, `爬虫语料 ${ex.id} 未路由`).toBeTruthy()
      expect(route!.page).toBe('interactive:crawler-lab')
      expect(typeValues.has(route!.type ?? ''), `${family} 类型 ${route!.type} 不在注册表`).toBe(true)
      mapped++
    }
    expect(mapped).toBe(57)
  })
})
