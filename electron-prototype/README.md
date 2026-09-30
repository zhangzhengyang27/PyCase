# electron 工程：开发与打包指南

> 应用本体（Electron 壳 + Vue 渲染层 + Python sidecar）。产品说明见仓库根 [README](../README.md)，
> 重设计进度见 [docs/redesign-plan.md](../docs/redesign-plan.md)。

## 组成

```
electron-prototype/
├── electron/            # Electron 工程（electron-vite 三段构建）
│   ├── src/main/        # 主进程：窗口、sidecar 生命周期、IPC、走查/性能探针
│   ├── src/preload/     # 桥（contextBridge）：类型化 SidecarAPI
│   ├── src/renderer/    # Vue 3 渲染层（store 分 10 域 + 组件层；token 见 src/theme.css）
│   ├── build-pyinstaller/sidecar.spec   # sidecar 冻结配置（hiddenimports 扫描 app/*.py）
│   └── package.json     # 脚本 / electron-builder 配置（mac + win 目标）
├── sidecar/             # Python 后端（server.py + ai_service.py，纯标准库）
└── shared/              # 跨语言单一来源：protocol.json（RPC 方法表）+ protocol.ts（客户端类型）
```

## 常用命令（在 `electron-prototype/electron` 下）

```bash
npm install                  # 依赖（国内可直接加 --registry=https://registry.npmmirror.com）
npm run dev                  # 开发（electron-vite dev；sidecar 由主进程 spawn）
npm run typecheck            # tsc + vue-tsc（noImplicitAny）
npm run lint                 # ESLint + stylelint
npm run format:check         # Prettier 校验
npm test                     # Vitest 组件测试
npm run smoke                # 真实窗口走查（壳/画廊/详情/全局层/首启/资源/A6/性能）
npm run sidecar              # 冻结 sidecar（PyInstaller）并冒烟：真启动 + list_examples == 1496
npm run dist:mac / dist:win  # 出包（先自动冻结 sidecar）
```

## 打包与数据

- 打包产物在 `dist/`、sidecar 冻结产物在 `sidecar-dist/`（均已 gitignore）。
- 随包资源（`electron-builder.extraResources`）：`json_examples`（清单 + 真实源码 + 烘焙事实）、
  `topics/tools/projects`（原位示例）、`examples_assets`（目录型示例素材）、`requirements.txt`、
  `sidecar/sidecar(.exe)`；**清单里 `file` 指到的每一棵目录树都必须随包**，静态不变量见
  `tests/test_packaging_invariants.py`。
- 打包冒烟：CI 的 `packaging` 矩阵（mac + win）会「冻结 → 出包 → 产物断言 → mac 打包产物自测」；
  Windows 侧另有 NSIS 静默安装 + 启动冒烟。

## 约定

- 渲染层不直接摸 `window.sidecar`：一律经 `src/renderer/src/sidecar-client.ts` 的类型化 API；
  协议增删方法要同时改 `shared/protocol.json`（Python 金标与 TS 契约测试双端校验）。
- 组件不猜平台：mac/win 差异走 `html[data-platform]`（CSS 层）与 `src/renderer/src/platform.ts`。
- 写盘型走查探针必须先断言目标身份（历史事故：目录未刷新导致误改内置示例源码）。
