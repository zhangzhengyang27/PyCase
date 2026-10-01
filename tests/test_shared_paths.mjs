// shared/paths.ts 纯函数测试：DATA_DIR 契约。
//
// 背景（审计 C1）：app:openLog 曾写 `process.env.DESKTOP_APP_DATA_DIR || app.getAppPath()`
// ——但该环境变量只注入给 sidecar 子进程，主进程自身永远读不到，于是两种模式下
// 「查看准备日志」按钮都指向不存在的路径。修复后 openLog 经此纯函数取数据根，
// 与 spawn 时注入给 sidecar 的口径逐字一致（server.py: DATA_DIR = env || 仓库根）。
import { createRendererLoader } from './renderer-loader.mjs'

const { resolveDataDir } = createRendererLoader().load('../../../shared/paths')

let failed = 0
function check(desc, cond) {
  if (!cond) {
    failed++
    console.error(`  ✗ ${desc}`)
  } else {
    console.log(`  ✓ ${desc}`)
  }
}

console.log('resolveDataDir')

check(
  '打包态 → userData（与 spawn 注入的 DESKTOP_APP_DATA_DIR 一致）',
  resolveDataDir({ isPackaged: true, userDataPath: '/U', repoRoot: '/R' }) === '/U'
)
check(
  '开发态 → 仓库根（sidecar 默认 DATA_DIR = APP_DIR，日志写 <repo>/logs）',
  resolveDataDir({ isPackaged: false, userDataPath: '/U', repoRoot: '/R' }) === '/R'
)
check(
  '打包态不回落仓库根（repoRoot 缺失也取 userData）',
  resolveDataDir({ isPackaged: true, userDataPath: '/U', repoRoot: '' }) === '/U'
)

if (failed) {
  console.error(`\n${failed} 项断言失败`)
  process.exit(1)
}
console.log('\n全部通过')
