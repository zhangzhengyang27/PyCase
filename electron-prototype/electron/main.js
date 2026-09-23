// Electron 主进程：管理窗口、spawn Python sidecar、桥接 IPC。

const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");
const { fileURLToPath } = require("url");

// ---------------------------------------------------------------------------
// 路径解析
// ---------------------------------------------------------------------------
const IS_PACKAGED = app.isPackaged;

let APP_DIR;
if (IS_PACKAGED) {
  // 打包模式：数据文件（json_examples）在 resources 目录下
  APP_DIR = process.resourcesPath;
} else {
  // 开发模式：从 electron/ 目录向上推导
  const ELECTRON_DIR = __dirname;
  const PROTOTYPE_DIR = path.dirname(ELECTRON_DIR);
  APP_DIR = path.dirname(PROTOTYPE_DIR);
}

const SIDECAR_SCRIPT = IS_PACKAGED
  ? null // 打包模式下不使用源码脚本
  : path.join(path.dirname(path.dirname(__dirname)), "electron-prototype", "sidecar", "server.py");

// 解析 sidecar 启动命令：
//   开发模式 → python3 server.py
//   打包模式 → 直接运行 PyInstaller 产物（sidecar 可执行文件）
function resolveSidecarCommand() {
  // 环境变量覆盖（调试用）
  if (process.env.SIDECAR_PATH && fs.existsSync(process.env.SIDECAR_PATH)) {
    return { command: process.env.SIDECAR_PATH, args: [] };
  }

  if (IS_PACKAGED) {
    // 打包后 sidecar 可执行文件在 resources 目录下
    const ext = process.platform === "win32" ? ".exe" : "";
    const bundled = path.join(process.resourcesPath, "sidecar", `sidecar${ext}`);
    if (fs.existsSync(bundled)) {
      return { command: bundled, args: [] };
    }
    // 兜底：尝试在 resourcesPath 根目录
    const rootSidecar = path.join(process.resourcesPath, `sidecar${ext}`);
    if (fs.existsSync(rootSidecar)) {
      return { command: rootSidecar, args: [] };
    }
    console.warn("[sidecar] 未找到打包后的 sidecar，回退到 python3 源码模式");
  }

  // 开发模式：优先用项目共享 venv 的 Python 启动 sidecar（与示例运行环境一致），
  // venv 尚未创建时回退 python3（sidecar 首次运行示例时会自动创建 .venv）
  const venvPython = path.join(
    APP_DIR,
    ".venv",
    process.platform === "win32" ? path.join("Scripts", "python.exe") : path.join("bin", "python")
  );
  const pythonExe =
    process.env.PYTHON_EXECUTABLE ||
    (fs.existsSync(venvPython) ? venvPython : "python3");
  return { command: pythonExe, args: [SIDECAR_SCRIPT] };
}

// ---------------------------------------------------------------------------
// Sidecar 管理
// ---------------------------------------------------------------------------
let sidecarProcess = null;
let requestId = 0;
const pendingRequests = new Map(); // id -> {resolve, reject}
let mainWindow = null;
let sidecarReady = false;
const readyQueue = []; // sidecar 就绪前缓存的消息

function spawnSidecar() {
  const { command, args } = resolveSidecarCommand();
  console.log(`[sidecar] launching: ${command} ${args.join(" ")}`);
  console.log(`[sidecar] mode: ${IS_PACKAGED ? "packaged" : "development"}`);

  sidecarProcess = spawn(command, args, {
    cwd: APP_DIR,
    stdio: ["pipe", "pipe", "pipe"],
    env: { ...process.env, PYTHONUNBUFFERED: "1" },
  });

  let stdoutBuffer = "";
  sidecarProcess.stdout.on("data", (data) => {
    stdoutBuffer += data.toString("utf-8");
    const lines = stdoutBuffer.split("\n");
    stdoutBuffer = lines.pop(); // 保留不完整的行
    for (const line of lines) {
      if (line.trim()) {
        handleSidecarMessage(line);
      }
    }
  });

  sidecarProcess.stderr.on("data", (data) => {
    console.error("[sidecar stderr]", data.toString());
  });

  sidecarProcess.on("close", (code) => {
    console.log(`[sidecar] exited with code ${code}`);
    sidecarProcess = null;
    sidecarReady = false;
    // 拒绝所有挂起的请求
    for (const [id, req] of pendingRequests) {
      req.reject(new Error("sidecar 进程已退出"));
      pendingRequests.delete(id);
    }
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send("sidecar:status", { ready: false, code });
    }
  });

  sidecarProcess.on("error", (err) => {
    console.error("[sidecar] spawn error:", err);
  });
}

function handleSidecarMessage(line) {
  let msg;
  try {
    msg = JSON.parse(line);
  } catch (e) {
    console.error("[sidecar] JSON parse error:", line.slice(0, 200));
    return;
  }

  // 通知（无 id）
  if (msg.id === undefined || msg.id === null) {
    if (msg.method === "sidecar_ready") {
      sidecarReady = true;
      console.log("[sidecar] ready");
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send("sidecar:status", { ready: true });
      }
      // 发送缓存的消息
      while (readyQueue.length > 0) {
        const m = readyQueue.shift();
        sidecarProcess.stdin.write(m + "\n");
      }
    } else if (msg.method === "run_output" || msg.method === "run_finished" || msg.method === "run_images") {
      // 转发到渲染进程
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send(`sidecar:${msg.method}`, msg.params);
      }
    }
    return;
  }

  // 响应（有 id）
  const req = pendingRequests.get(msg.id);
  if (req) {
    pendingRequests.delete(msg.id);
    if (msg.error) {
      req.reject(new Error(msg.error.message || "sidecar 错误"));
    } else {
      req.resolve(msg.result);
    }
  }
}

function callSidecar(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++requestId;
    const msg = JSON.stringify({ jsonrpc: "2.0", id, method, params });

    if (!sidecarProcess) {
      reject(new Error("sidecar 未启动"));
      return;
    }

    pendingRequests.set(id, { resolve, reject });

    if (sidecarReady) {
      sidecarProcess.stdin.write(msg + "\n");
    } else {
      readyQueue.push(msg);
    }

    // 超时保护
    setTimeout(() => {
      if (pendingRequests.has(id)) {
        pendingRequests.delete(id);
        reject(new Error(`请求超时: ${method}`));
      }
    }, 120000);
  });
}

// ---------------------------------------------------------------------------
// 窗口
// ---------------------------------------------------------------------------
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    title: "Python 示例管理器 (Electron 原型)",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadFile(path.join(__dirname, "renderer", "index.html"));

  // 开发环境自动打开 DevTools
  mainWindow.webContents.openDevTools({ mode: "detach" });
}

// ---------------------------------------------------------------------------
// IPC 处理：渲染进程 -> sidecar
// ---------------------------------------------------------------------------
ipcMain.handle("sidecar:ping", () => callSidecar("ping"));
ipcMain.handle("sidecar:listExamples", () => callSidecar("list_examples"));
ipcMain.handle("sidecar:getExample", (_e, id) => callSidecar("get_example", { id }));
ipcMain.handle("sidecar:parseArgs", (_e, id) => callSidecar("parse_args", { id }));
ipcMain.handle("sidecar:saveExample", (_e, params) => callSidecar("save_example", params));
ipcMain.handle("sidecar:runExample", (_e, params) => callSidecar("run_example", params));
ipcMain.handle("sidecar:stopRun", (_e, runId) => callSidecar("stop_run", { run_id: runId }));
ipcMain.handle("sidecar:uploadAsset", (_e, params) => callSidecar("upload_asset", params));
ipcMain.handle("sidecar:listAssets", (_e, id) => callSidecar("list_assets", { id }));
ipcMain.handle("sidecar:deleteAsset", (_e, params) => callSidecar("delete_asset", params));

// 下载运行结果图片：弹出保存对话框，把处理结果复制到用户选择的位置
ipcMain.handle("file:downloadResultImage", async (event, { url, defaultName }) => {
  try {
    const srcPath = fileURLToPath(url);
    if (!fs.existsSync(srcPath)) {
      return { error: `文件不存在：${srcPath}` };
    }
    const win = BrowserWindow.fromWebContents(event.sender);
    const { canceled, filePath } = await dialog.showSaveDialog(win, {
      title: "保存处理结果",
      defaultPath: defaultName || path.basename(srcPath),
    });
    if (canceled || !filePath) {
      return { canceled: true };
    }
    await fs.promises.copyFile(srcPath, filePath);
    return { canceled: false, savedTo: filePath };
  } catch (err) {
    return { error: err.message };
  }
});

ipcMain.handle("sidecar:restart", () => {
  if (sidecarProcess) {
    sidecarProcess.kill();
  }
  spawnSidecar();
  return { status: "restarting" };
});

// ---------------------------------------------------------------------------
// 应用生命周期
// ---------------------------------------------------------------------------
app.whenReady().then(() => {
  spawnSidecar();
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (sidecarProcess) {
    sidecarProcess.kill();
  }
  if (process.platform !== "darwin") {
    app.quit();
  }
});
