// tool-schemas-crawlers.ts：V4 爬虫精选 ×4——把 63 个爬虫教学示例中最实用的 4 个改造为页面工具。
// 形态：URL/文本输入 → requests 真实请求 → 结构化结果（表格/文本）。
// 需联网；requests 已在共享 venv。
import type { InteractiveToolSchema } from './interactive-tools'

const str = (v: unknown): string => String(v ?? '')

// ---------------------------------------------------------------------------
// 1. HTTP 请求器（方法/URL/headers/body → 发送 → 响应结构化展示）
// ---------------------------------------------------------------------------
export const httpRequesterSchema: InteractiveToolSchema = {
  id: 'interactive:http-requester',
  title: 'HTTP 请求器',
  description: '发请求看响应：方法/URL/自定义 headers → 状态码/耗时/响应头/正文预览（需联网）。',
  tags: ['网络', '爬虫'],
  fields: [
    {
      key: 'method',
      label: '方法',
      type: 'select',
      default: 'GET',
      width: 'half',
      options: ['GET', 'POST', 'PUT', 'DELETE'].map((m) => ({ value: m, label: m }))
    },
    { key: 'url', label: 'URL', type: 'text', required: true, placeholder: 'https://httpbin.org/get', width: 'half' },
    {
      key: 'headers',
      label: 'Headers（每行 Key: Value）',
      type: 'textarea',
      required: false,
      placeholder: 'User-Agent: myapp/1.0'
    },
    { key: 'body', label: 'Body（POST/PUT）', type: 'textarea', required: false, placeholder: '{"key": "value"}' }
  ],
  computeVia: 'sidecar',
  steps: [
    { title: '请求参数', keys: ['method', 'url', 'headers', 'body'] },
    { title: '发送', keys: [] }
  ],
  compute: (v) => {
    if (!str(v.url)) return { error: '请输入 URL' }
    const m = str(v.method ?? 'GET')
    if (!['GET', 'POST', 'PUT', 'DELETE'].includes(m)) return { error: '未知请求方法' }
    return { rows: [{ label: '请求', value: `${m} ${str(v.url).slice(0, 80)}`, copy: true }] }
  },
  pyCode: (v) => {
    const url = str(v.url).trim()
    const method = str(v.method ?? 'GET')
    if (!url) return '# 输入 URL 后自动生成代码'
    const headers = str(v.headers)
    const body = str(v.body)
    const hLines = headers
      .split('\n')
      .filter((l) => l.includes(':'))
      .map((l) => {
        const idx = l.indexOf(':')
        return `        ${JSON.stringify(l.slice(0, idx).trim())}: ${JSON.stringify(l.slice(idx + 1).trim())},`
      })
      .join('\n')
    return `"""HTTP 请求器。"""
import json
import time

import requests

headers = {
${hLines}
}
t0 = time.monotonic()
resp = requests.request("${method}", ${JSON.stringify(url)}, headers=headers or None,${method !== 'GET' && body ? ` data=${JSON.stringify(body)},` : ''} timeout=15)
elapsed = (time.monotonic() - t0) * 1000
rows = [
    {"label": "状态码", "value": str(resp.status_code)},
    {"label": "耗时", "value": f"{elapsed:.0f} ms"},
    {"label": "Content-Type", "value": resp.headers.get("content-type", "—")},
    {"label": "响应大小", "value": f"{len(resp.content)} bytes"},
]
print("<<<JSON>>>")
print(json.dumps({"primary": {"value": str(resp.status_code)},
                  "rows": rows,
                  "text": resp.text[:3000]}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 2. 网页标题与链接提取器
// ---------------------------------------------------------------------------
export const linkExtractorSchema: InteractiveToolSchema = {
  id: 'interactive:link-extractor',
  title: '网页链接提取',
  description: '提取网页全部 <a> 链接与标题（表格化展示；需联网）。',
  tags: ['网络', '爬虫'],
  fields: [{ key: 'url', label: 'URL', type: 'text', required: true, placeholder: 'https://example.com' }],
  computeVia: 'sidecar',
  compute: (v) => (str(v.url) ? { rows: [{ label: 'URL', value: str(v.url), copy: true }] } : { error: '请输入 URL' }),
  pyCode: (v) => {
    const url = str(v.url).trim()
    if (!url) return '# 输入 URL 后自动生成代码'
    return `"""网页链接提取（正则解析，无 bs4 依赖）。"""
import json
import re

import requests

html = requests.get(${JSON.stringify(url)}, timeout=15).text
links = re.findall(r'<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>', html, re.I | re.S)
rows = []
seen = set()
for href, text in links:
    text = re.sub(r"<[^>]+>", "", text).strip()[:60]
    if href in seen:
        continue
    seen.add(href)
    rows.append([text or "（无文本）", href])
print("<<<JSON>>>")
print(json.dumps({"primary": {"value": str(len(rows)), "unit": "个外链"},
                  "table": {"columns": ["文本", "URL"], "rows": rows[:100]}}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 3. 开放天气查询
// ---------------------------------------------------------------------------
export const weatherSchema: InteractiveToolSchema = {
  id: 'interactive:weather',
  title: '天气查询',
  description: 'OpenWeatherMap API 城市天气（wttr.in 免费接口，无需 API Key，需联网）。',
  tags: ['网络', '查询'],
  fields: [
    { key: 'city', label: '城市', type: 'text', required: true, placeholder: 'Shanghai 或 北京', width: 'half' }
  ],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.city) ? { rows: [{ label: '城市', value: str(v.city), copy: true }] } : { error: '请输入城市名' },
  pyCode: (v) => {
    const city = str(v.city).trim()
    if (!city) return '# 输入城市后自动生成代码'
    return `"""天气查询（wttr.in 免费接口）。"""
import json

import requests

resp = requests.get("https://wttr.in/${city}?format=j1", timeout=15, headers={"User-Agent": "curl/8.0"})
data = resp.json()
cur = data["current_condition"][0]
rows = [
    {"label": "温度", "value": f"{cur['temp_C']}°C（体感 {cur['FeelsLikeC']}°C）"},
    {"label": "天气", "value": cur["weatherDesc"][0]["value"]},
    {"label": "湿度", "value": f"{cur['humidity']}%"},
    {"label": "风速", "value": f"{cur['windspeedKmph']} km/h"},
]
print("<<<JSON>>>")
print(json.dumps({"rows": rows}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

// ---------------------------------------------------------------------------
// 4. 汇率换算查询
// ---------------------------------------------------------------------------
export const exchangeRateSchema: InteractiveToolSchema = {
  id: 'interactive:exchange-rate',
  title: '汇率换算',
  description: '实时汇率换算（exchangerate-api 免费端点，需联网）。',
  tags: ['网络', '查询'],
  fields: [
    { key: 'from', label: '源货币', type: 'text', required: true, default: 'USD', width: 'half', placeholder: 'USD' },
    { key: 'to', label: '目标货币', type: 'text', required: true, default: 'CNY', width: 'half', placeholder: 'CNY' },
    { key: 'amount', label: '金额', type: 'number', default: 100, width: 'half' }
  ],
  computeVia: 'sidecar',
  compute: (v) => {
    if (!str(v.from) || !str(v.to)) return { error: '请输入货币代码' }
    const amt = Number(v.amount ?? 100)
    if (!Number.isFinite(amt) || amt <= 0) return { error: '金额需为正数' }
    return { rows: [{ label: '换算', value: `${amt} ${str(v.from)} → ${str(v.to)}` }] }
  },
  pyCode: (v) => {
    const from = str(v.from).trim().toUpperCase()
    const to = str(v.to).trim().toUpperCase()
    const amt = Number(v.amount ?? 100)
    if (!from || !to || !Number.isFinite(amt)) return '# 补全货币代码与金额后自动生成代码'
    return `"""汇率换算（exchangerate-api 免费端点）。"""
import json

import requests

rate = requests.get(f"https://open.er-api.com/v6/latest/${from}", timeout=15).json()["rates"][${JSON.stringify(to)}]
result = ${amt} * rate
print("<<<JSON>>>")
print(json.dumps({"primary": {"value": f"{result:.2f}", "unit": ${JSON.stringify(to)}},
                  "rows": [{"label": "汇率", "value": f"1 ${from} = {rate:.4f} ${to}", "copy": True}]},
                 ensure_ascii=False))
print("<<<END>>>")
`
  }
}

export const CRAWLER_SCHEMAS: InteractiveToolSchema[] = [
  httpRequesterSchema,
  linkExtractorSchema,
  weatherSchema,
  exchangeRateSchema
]
