# v0.5.0 发布说明（macOS arm64，ad-hoc 签名）

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
