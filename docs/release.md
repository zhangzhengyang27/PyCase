# v1.0.0 发布说明（macOS arm64 + Windows x64）

> 版本号单一来源 = 仓库根 `VERSION`；本版为 2026-09 大厂级重设计的收口版本
> （双轨计划与逐批记录见 [docs/redesign-plan.md](redesign-plan.md)）。

## 本版内容（相对 v0.10.0）

- **视觉与交互重做**：token 三层绑定（平台 × 主题 × 强调色）、壳与导航、画廊/工具箱、运行器/详情、
  全局层（⌘K 面板 / 高危确认 / 设置 / 导入向导）、帮助面板与全屏首启引导页；
  组件层自研（移除 Element Plus），图标单一 Lucide，字重/对比度有门禁。
- **数据契约 v2**：清单只存元数据 + 真实 `.py` 源码树；启动零写盘（索引就绪 ~45ms）；
  派生事实构建期烘焙 + 启动哈希校验；依赖清单由 `app.facts_cli requirements` 汇总（生成器脚本退役）；
  用户集合导入即 v2、旧集合启动自动迁移（含备份）。
- **产品化补课**：失败恢复（崩溃横幅/参数报错可重试/缺依赖一键装包装跑）、可恢复编辑
  （保存与还原前自动快照、版本页行级差异 + 一键还原）、存储治理（占用可视化、两档清理、旧版缓存回收）、
  AI 外发同意可复核可撤回。
- **工程门禁**：护栏 G1–G9 + 迁移演练 G8、ruff/mypy/覆盖率 ≥70%、ESLint/stylelint/Prettier、
  tsc/vue-tsc（noImplicitAny）、真实窗口走查（`npm run smoke`，含性能段与故障注入）、E2E、
  双平台打包矩阵（含 Windows 安装冒烟）。

## 产物

| 平台 | 产物 | 说明 |
|---|---|---|
| macOS arm64 | `dist/Python示例管理器-1.0.0-arm64-mac.zip` | 免安装压缩包（推荐分发格式） |
| macOS arm64 | `dist/Python示例管理器-1.0.0-arm64.dmg` | 安装镜像 |
| Windows x64 | `dist/Python示例管理器 Setup 1.0.0.exe`（NSIS）与 zip | 由 CI `packaging` 矩阵产出 |

安装形态已验证：mac 侧 zip 解包运行与 dmg 挂载运行各跑一次完整走查（本机实测）；
Windows 侧由 CI 执行 NSIS 静默安装 → 启动安装后的 exe 跑走查 → 卸载。

## 发布链（无证书/账号的姿势，对齐 leaf-library）

```bash
# 1) 定版本：改 VERSION → 同步三处 → 提交
python scripts/sync_version.py
git commit -am "release: vX.Y.Z"
# 2) 打 tag 并推送（tag 是发布的唯一触发器）
git tag -a vX.Y.Z -m "vX.Y.Z：<一句话>"
git push origin main vX.Y.Z
```

`.github/workflows/release.yml` 在 `v*` tag 上触发三平台矩阵（mac arm64 / mac x64 / win x64）：
冻结 sidecar（真启动冒烟）→ 版本一致性校验 → 出包 → **从产物里真跑一次走查** → `gh release` 上传到 GitHub Releases。

> **v1.0.0 勘误 + 门禁收口（2026-10-01）**：v1.0.0 tag 时点上述链路**从未走通**——Release #1
> 在 4 分半内失败（GitHub Releases 上没有任何产物），且 tag 落在三处 Windows 致命缺陷修复
> （`c453de1` 等，见 redesign-plan §7 修正记录）之前。自下个版本起，Release workflow 先整体
> 复用 ci.yml 作为发布前置门禁（`needs: ci`，经 `workflow_call`），全绿才进构建矩阵——
> 「tag 只在验收全绿后创建」由口头纪律变成机器强制。

四条「无证书发布」的规矩（都来自实测教训）：

1. **不配签名**：`CSC_IDENTITY_AUTO_DISCOVERY=false`；不设 notarize——electron-builder 在完全没有
   Apple 凭据时只 warn「skipped notarization」并正常出包。**但凭据只配一半会直接抛
   InvalidConfigurationError**，要配就配全（`APPLE_ID`/`APPLE_APP_SPECIFIC_PASSWORD`/`APPLE_TEAM_ID`
   或 `APPLE_API_KEY`/`APPLE_API_KEY_ID`/`APPLE_API_ISSUER`）。
2. **产物名必须 ASCII 且带 `${arch}`**：GitHub 上传路径不转义，含中文/空格的 asset 名会 400；
   双架构矩阵同名会互相覆盖（`PyCase-<版本>-<arch>-mac.zip` 这套命名即由此而来）。
3. **可执行名按平台不同**：mac 用 productName（中文），Windows 用 `executableName: PyCase`；
   找主可执行文件统一走 `scripts/find_mac_app_binary.sh`（先定位顶层 .app 再按包名取
   `Contents/MacOS/<包名>`）——**别用 `find -path '*/Contents/MacOS/*'`**：Electron 包的
   Frameworks 下还有一组 Helper .app 也匹配该模式，按遍历顺序取第一个会拿到
   "… Helper (GPU)"；也别给 find 设 `-maxdepth`（dist 里 app 包外还有一层 `mac-arm64/`）。
4. **走查在 CI runner 上按环境放宽**：runner 是无 GPU 的软件渲染虚拟机（Intel runner 首屏 11s
   vs 本机 0.6–0.9s），且全新机器的共享 venv 首次引导要装几十个包（分钟级、需网络）——
   性能预算走 `SMOKE_PERF_SCALE=6`、运行解释器走 `SMOKE_RUN_ENV=system`（启动即 `PYCASE_RUN_ENV`
   预置，跳过建环境；这两个变量只由 CI 工作流设置）。**严格预算仍以真实机器上的走查为准**，
   CI 只当数量级回归网。

自动更新（electron-updater）本版**未启用**：mac 侧未签名时 Squirrel.Mac 无法应用更新（需签名），
Windows 侧技术上可用——若将来要开，做法是给 electron-builder 加 `publish` 配置（产物会附带
`latest*.yml`）并在设置页加「检查更新」入口。

## 签名与首次打开

- macOS：ad-hoc 签名（`identity: null`），**未公证**。首次打开需右键「打开」或
  `xattr -dr com.apple.quarantine "/Applications/Python示例管理器.app"`；
  正式分发建议配置 Apple 开发者证书 + 公证（预算/账号待定）。
- Windows：未签名（SmartScreen 会提示）；正式分发建议购买代码签名证书。

## 首次运行

首次启动显示首启引导页并后台创建共享 `.venv`（按 `requirements.txt` 装依赖，数分钟，进度可见、
失败可重试或改用系统 Python）；示例运行在隔离工作区，运行产物与上传资源不会被清理动作误删。

---

# 打包与发布说明（macOS / Windows）

> 历史版本说明（v0.5.0，macOS arm64）保留在本文件末尾的存档段；本条以下为 B3-4 起的
> **可复现打包流程**（审计 C1：此前 dist 依赖手工产物、CI 无打包 job）。

## 可复现打包（一条命令）

```bash
cd electron-prototype/electron
npm run dist:mac     # 冻结 sidecar（含冒烟）→ 前端构建 → electron-builder --mac
npm run dist:win     # 同上，出 Windows 产物（需在 Windows 上执行）
npm run sidecar      # 只冻结并冒烟 Python sidecar
```

产物落在 `electron-prototype/electron/dist/`（已 gitignore）；sidecar 冻结产物在
`electron-prototype/electron/sidecar-dist/`（同样 gitignore）。

## 打包链的三道验证（CI `packaging` job 双平台矩阵）

1. **冻结冒烟**：`scripts/build_sidecar.py --smoke` 真启动冻结产物，断言
   `sidecar_ready` → `ping` → `list_examples == 1496`（能加载 app 包、能读随包数据）；
2. **产物断言**：`resources/` 下必须有 `sidecar/sidecar(.exe)`、`requirements.txt`、
   `json_examples/facts.json`、`topics`、`tools`、`projects`、`examples_assets`；
3. **打包产物自测**（macOS）：直接启动 `.app/Contents/MacOS/...` 跑 `SMOKE_TEST=1` 全套走查探针。

静态不变量（不跑打包也能挡缺料）见 `tests/test_packaging_invariants.py`。

## 随包内容与版本

- 真相源随包分发：`json_examples`（清单 + 真实源码 + 烘焙事实）、`topics/tools/projects`（原位示例）、
  `examples_assets`（31 条目录型示例的源码与数据兄弟）；
- 版本号单一来源 = 仓库根 `VERSION`，由 `scripts/sync_version.py` 同步到
  `package.json` / `pyproject.toml` / `app/_version.py`（CI 有 `--check` 门禁）；
- 图标：当前使用 Electron 默认图标（品牌图标待 M6）；
- 签名：macOS `identity: null`（ad-hoc，未公证）；Windows 未签名。

---

## 存档：v0.5.0 发布说明（macOS arm64，ad-hoc 签名）

## 产物

- `dist/Python示例管理器-0.5.0-arm64.zip` — 免安装压缩包（**主要分发格式**，276MB）
- `dist/mac-arm64/Python示例管理器.app` — 解包后的 .app（dir target，554MB）
- `dist/Python示例管理器-0.5.0-arm64.dmg` — 安装镜像（构建较慢，若未生成可使用 zip）

> 仅验证 macOS arm64（Apple Silicon）。未构建 x64/Windows/Linux 版本。
> 包体对比：v0.4.0 .app 约 342MB → v0.5.0 .app 554MB（增长主要来自示例数据全量打包与 sidecar PyInstaller 产物）。

## 首次打开（ad-hoc 签名，未公证）

本版本使用 ad-hoc 签名（`identity: null`），**未经过 Apple 公证**。首次打开时 macOS 会提示「无法验证开发者」，请按以下方式之一打开：

1. **右键打开**：在 Finder 中右键 `Python示例管理器.app` → 选择「打开」→ 在弹窗中再次点击「打开」。
2. **系统设置放行**：打开「系统设置 → 隐私与安全性」，滚动到「已阻止使用」区域，点击「仍要打开」。
3. **命令行移除隔离属性**（高级用户）：
   ```bash
   xattr -dr com.apple.quarantine "/Applications/Python示例管理器.app"
   ```

打开后应用会在首次运行示例时自动创建共享 `.venv` 并安装依赖（约 1-3 分钟，取决于网络）。

## 校验

```bash
# 校验 .app 签名状态（ad-hoc 签名显示 "adhoc"）
codesign -dv --verbose=4 "/Applications/Python示例管理器.app" 2>&1 | grep -E "Signature|Authority|TeamIdentifier"

# 校验可执行文件架构（应为 arm64）
file "/Applications/Python示例管理器.app/Contents/MacOS/Python示例管理器"

# 启动后在 DevTools 控制台执行，确认 sidecar 版本为 0.5.0：
#   window.sidecar.ping().then(console.log)
```

## 用户数据位置

应用数据全部存放在本机 userData 目录，**不会**写入应用包（打包后 Resources 只读）：

```
~/Library/Application Support/python-example-manager-electron/
├── history.json      # 运行历史（上限 500 条）
├── favorites.json    # 收藏的示例 id
└── aiSettings.json   # AI 设置（含 DeepSeek API Key，明文存本机）
```

> **AI Key 安全提示**：`aiSettings.json` 中的 API Key 以明文存储在本机用户目录。请勿将此文件分享或提交到 git。卸载应用时需手动删除该目录。

## v0.5.0 新功能

- 🕘 运行历史面板（重跑/清空/导出 .log）
- ⭐ 示例收藏（树/工具/主题卡片星标，只看收藏与搜索叠加）
- 🏷️ 多维标签筛选（import 自动标签 + 运行状态 + 收藏 + 分类 + 全文搜索可组合）
- ✨ AI 代码解释（DeepSeek 流式，选中代码一键解释，Key 仅存本机）

## 已知限制

1. **仅 macOS arm64**：未构建 x64、Windows、Linux 版本。
2. **ad-hoc 签名未公证**：首次打开需右键放行，无法通过 Gatekeeper 自动验证。
3. **AI 代码解释需自备 Key**：应用不内置 API Key，需在「AI 设置」中填写 DeepSeek Key。代码会发送到 `https://api.deepseek.com`。
4. **共享 .venv 首次创建较慢**：首次运行示例时会在仓库根创建 `.venv` 并安装依赖，需网络连接。
5. **示例数据随包分发**：`topics/`、`tools/`、`projects/`、`json_examples/` 作为 extraResources 打包，包体较大（约 300MB+）。
6. **无自动更新**：本版本不内置自动更新机制，升级需手动下载替换。

## 回滚

如需回滚到 v0.4.0：

```bash
cd /path/to/desktop-app
git checkout v0.4.0
# 重新打包（需先重建 sidecar-dist）
cd electron-prototype/electron && npm run dist
```

用户数据（history/favorites/aiSettings）与版本无关，回滚后仍可使用。
