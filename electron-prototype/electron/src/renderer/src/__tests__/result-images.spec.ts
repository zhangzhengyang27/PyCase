// 运行产物图协议 URL 助手（main 进程纯逻辑，electron 无关故在 vitest 侧测）：
// sidecar 推来的 file:// URI 在 dev 模式（http:// origin + webSecurity）下不能作为
// <img> src 加载，主进程转发时统一改写为 pycase-img:// 特权协议 URL。
import { describe, expect, it } from 'vitest'
import { fileToImgSchemeUrl, imgSchemeToPath, IMG_SCHEME } from '../../../../../shared/result-images'

describe('result-images 协议 URL 助手', () => {
  it('file:// URI → pycase-img:// URL（路径整体编码，空格/中文安全）', () => {
    const u = fileToImgSchemeUrl('file:///tmp/adhoc%20x/%E5%9B%BE%E7%89%87/chart.png')
    expect(u.startsWith(`${IMG_SCHEME}://`)).toBe(true)
    expect(u).not.toContain(' ')
    expect(u).not.toContain('/adhoc x/'.slice(1)) // 原始空格不得裸露
  })

  it('非 file:// URL 原样返回', () => {
    expect(fileToImgSchemeUrl('https://a/b.png')).toBe('https://a/b.png')
  })

  it('imgSchemeToPath 与 fileToImgSchemeUrl 互逆', () => {
    const p = '/tmp/PyCase/.json_examples_cache/v2/adhoc/abc/chart.png'
    expect(imgSchemeToPath(fileToImgSchemeUrl(`file://${p.split('/').map(encodeURIComponent).join('/')}`))).toBe(p)
  })

  it('imgSchemeToPath 只认本协议', () => {
    expect(imgSchemeToPath('file:///tmp/a.png')).toBeNull()
    expect(imgSchemeToPath('https://a/b.png')).toBeNull()
  })
})
