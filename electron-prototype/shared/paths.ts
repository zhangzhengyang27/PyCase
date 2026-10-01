// 数据根目录契约（跨进程单一来源，与 sidecar server.py 的 DATA_DIR 口径对齐）：
//   打包态 → userData（主进程 spawn 时注入 DESKTOP_APP_DATA_DIR，Resources 只读）；
//   开发态 → 仓库根（.venv / 缓存 / logs 都在仓库根，README 约定的共享环境）。
// 主进程里凡是「sidecar 会把数据写在哪」的判断（openLog 等）必须经此函数——
// 不要自行读 process.env.DESKTOP_APP_DATA_DIR：它只注入给 sidecar 子进程，
// 主进程自身的环境里永远没有它（曾因此让「查看准备日志」按钮两种模式都开错路径）。
export function resolveDataDir(opts: { isPackaged: boolean; userDataPath: string; repoRoot: string }): string {
  return opts.isPackaged ? opts.userDataPath : opts.repoRoot
}
