# Electron + Python sidecar 最小原型

验证「Electron 做桌面端壳 + Python sidecar 做后端」架构是否可行。

## 架构

```
┌─ Electron ────────────────────────────────┐
│  渲染进程: 原生 HTML/CSS/JS (无框架)       │
│       ↕ IPC (contextBridge)                │
│  主进程: Node.js — spawn sidecar, 桥接通信  │
│       ↕ stdio 行分隔 JSON-RPC 2.0          │
│  Python sidecar (server.py)                │
│  └─ 复用现有 app.json_examples.ExampleStore │
│  └─ asyncio 子进程运行示例 (替代 QProcess)  │
│  └─ 输出通过 JSON-RPC notification 实时推送  │
└────────────────────────────────────────────┘
```

## 目录结构

```
electron-prototype/
├── sidecar/
│   └── server.py          # Python sidecar 入口（stdio JSON-RPC）
├── electron/
│   ├── package.json
│   ├── main.js            # Electron 主进程
│   ├── preload.js         # contextBridge 安全 API
│   └── renderer/
│       ├── index.html     # UI 结构
│       ├── style.css      # 深色主题样式
│       └── app.js         # 前端逻辑
└── README.md
```

## 运行

```bash
cd electron-prototype/electron
npm install
npm start
```

要求：系统已安装 `python3`（sidecar 直接用源码运行，无需打包）。

## 已验证的主链路

1. **列出示例** — `list_examples` 调用 ExampleStore.load()，返回全部 1496 个示例（2026-09-24 复核）
2. **搜索/筛选** — 前端按名称、标签、代码内容搜索；按 topics/tools/projects 分类筛选
3. **代码预览** — 选中示例后显示完整代码
4. **运行示例** — `run_example` 用 asyncio 子进程执行，stdout 逐行通过 JSON-RPC notification 推送
5. **实时输出流** — 渲染进程订阅 `run_output` 事件，输出实时追加到面板
6. **停止运行** — `stop_run` 发送 terminate 信号
7. **sidecar 状态监控** — 连接/断开状态实时显示，支持重启

## JSON-RPC 协议

所有消息为单行 JSON，通过 stdin/stdout 传输。

**请求：**
```json
{"jsonrpc":"2.0","id":1,"method":"list_examples","params":{}}
```

**响应：**
```json
{"jsonrpc":"2.0","id":1,"result":{"total":1496,"examples":[...]}}
```

**通知（无 id，服务端主动推送）：**
```json
{"jsonrpc":"2.0","method":"run_output","params":{"run_id":"abc123","text":"Hello\n"}}
{"jsonrpc":"2.0","method":"run_finished","params":{"run_id":"abc123","exit_code":0}}
```

**方法列表：**
| 方法 | 说明 |
|---|---|
| `ping` | 健康检查 |
| `list_examples` | 返回全部示例（扁平列表） |
| `get_example` | 按 id 获取单个示例详情 |
| `run_example` | 运行示例，立即返回 run_id，输出通过通知推送 |
| `stop_run` | 停止指定 run_id 的运行 |

## 关键设计决策

1. **stdio 而非 HTTP/WebSocket** — sidecar 是 Electron 的子进程，stdio 是最直接的通信方式，无需管理端口、无需处理跨域、进程退出自动清理。打包后也最简单。

2. **JSON-RPC 2.0 notification 做流式输出** — `run_example` 立即返回，不阻塞；输出通过无 id 的 notification 推送。这比长轮询或 SSE 更适合 stdio 通道。

3. **asyncio 替代 QProcess** — 原 `PythonRunner` 继承 `QProcess`，sidecar 中用 `asyncio.create_subprocess_exec` + `readline()` 逐行读取，功能等价且无 Qt 依赖。

4. **复用 ExampleStore 零修改** — sidecar 直接 import 现有 `app.json_examples.ExampleStore`，核心逻辑原样保留，证明了分层架构的迁移价值。

## 已知限制（原型阶段）

- 代码预览用 `<pre><code>`，未集成 Monaco Editor
- 不支持运行参数表单（args 硬编码为空）
- 不支持 venv 隔离安装（直接用系统 python3）
- 不支持代码编辑回写
- 未做 PyInstaller 打包（sidecar 用源码运行）
- 无自动更新、签名公证

## 下一步可扩展方向

1. 集成 Monaco Editor 替换 `<pre>` 代码预览
2. 实现参数表单（解析 argparse 生成表单）
3. 接入 venv_manager 做依赖隔离
4. 实现代码编辑 + JSON 回写
5. PyInstaller 打包 sidecar + electron-builder 打包 Electron
6. 逐页迁移工具箱（15 个内置工具改造成 JSON-RPC 端点）
