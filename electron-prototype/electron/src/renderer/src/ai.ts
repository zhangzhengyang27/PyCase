// ai.ts：AI 代码解释（DeepSeek）前端
// 职责：设置弹窗（key 存 userData，前端不接触明文）、解释侧栏、流式事件订阅、首次外发告知。
// 依赖：state（state.ts）、api（sidecar-client.ts）、escapeHtml（utils.ts）、state.editor（Monaco）。

import { state } from './state'
import { api } from './sidecar-client'
import { escapeHtml, BTN_GHOST_CLS, BTN_PRIMARY_CLS } from './utils'

const AI_PANEL_ID = 'ai-explain-panel'
const AI_SETTINGS_ID = 'ai-settings-modal'

// ---------------------------------------------------------------------------
// 设置弹窗
// ---------------------------------------------------------------------------
export function openAISettings() {
  closeAISettings();
  const s = state.aiSettings;
  const overlay = document.createElement("div");
  overlay.className = "fixed inset-0 bg-black/45 flex items-center justify-center z-[1000]";
  overlay.id = AI_SETTINGS_ID;
  overlay.innerHTML = `
    <div class="relative bg-panel rounded-[10px] w-[440px] max-w-[90vw] max-h-[85vh] overflow-auto shadow-[0_12px_40px_rgba(0,0,0,0.25)]" role="dialog" aria-label="AI 设置">
      <div class="flex items-center justify-between px-4 py-3 border-b border-line-subtle font-[590] text-[13px]">
        <span>AI 代码解释设置（DeepSeek）</span>
        <button class="border-0 bg-transparent text-[18px] cursor-pointer text-ink-mute leading-none" data-action="close">×</button>
      </div>
      <div class="p-4">
        <p class="text-[11.5px] text-ink-mute mb-3 leading-[1.5]">API Key 仅保存在本机 userData，不会写入代码、日志或上传。请求会发送到 DeepSeek 服务器。</p>
        <label class="flex flex-col gap-1 mb-2.5 text-[12px]">
          <span class="text-ink-dim">API Key${s.hasKey ? "（已配置，留空保持不变）" : ""}</span>
          <input type="password" id="ai-key" class="px-2 py-1.5 border border-line-subtle rounded-md bg-page text-ink font-mono text-[12px]" placeholder="sk-..." autocomplete="off" />
        </label>
        <label class="flex flex-col gap-1 mb-2.5 text-[12px]">
          <span class="text-ink-dim">模型</span>
          <input type="text" id="ai-model" class="px-2 py-1.5 border border-line-subtle rounded-md bg-page text-ink font-mono text-[12px]" value="${escapeHtml(s.model)}" />
        </label>
        <label class="flex flex-col gap-1 mb-2.5 text-[12px]">
          <span class="text-ink-dim">Base URL</span>
          <input type="text" id="ai-baseurl" class="px-2 py-1.5 border border-line-subtle rounded-md bg-page text-ink font-mono text-[12px]" value="${escapeHtml(s.baseUrl)}" />
        </label>
        <div class="flex gap-2 justify-end mt-3">
          <button class="${BTN_PRIMARY_CLS}" data-action="save">保存</button>
          <button class="${BTN_GHOST_CLS}" data-action="close">取消</button>
        </div>
      </div>
    </div>`;
  document.body.appendChild(overlay);

  overlay.addEventListener("click", (e) => {
    const action = (e.target as HTMLElement).dataset.action;
    if (action === "close" || e.target === overlay) closeAISettings();
    if (action === "save") saveAISettings();
  });
}

export function closeAISettings() {
  const el = document.getElementById(AI_SETTINGS_ID);
  if (el) el.remove();
}

export async function saveAISettings() {
  const key = (document.getElementById("ai-key") as HTMLInputElement).value.trim();
  const model = (document.getElementById("ai-model") as HTMLInputElement).value.trim() || "deepseek-chat";
  const baseUrl = (document.getElementById("ai-baseurl") as HTMLInputElement).value.trim() || "https://api.deepseek.com";
  const patch: any = { model, baseUrl };
  if (key) patch.apiKey = key; // 空字符串不覆盖（主进程会清除 ""，这里只在有值时传）
  try {
    const res = await api.aiSetSettings(patch);
    state.aiSettings.hasKey = !!res.hasKey;
    state.aiSettings.model = model;
    state.aiSettings.baseUrl = baseUrl;
    closeAISettings();
  } catch (err) {
    alert("保存 AI 设置失败：" + (err as any).message);
  }
}

// ---------------------------------------------------------------------------
// 解释侧栏
// ---------------------------------------------------------------------------
export function openAIPanel() {
  closeAIPanel();
  const panel = document.createElement("div");
  panel.className =
    "fixed top-[60px] right-4 w-[420px] max-w-[40vw] h-[calc(100vh-100px)] bg-panel border border-line-subtle rounded-[10px] shadow-[0_8px_30px_rgba(0,0,0,0.2)] flex flex-col z-[900]";
  panel.id = AI_PANEL_ID;
  panel.innerHTML = `
    <div class="flex items-center justify-between px-3.5 py-2.5 border-b border-line-subtle font-[590] text-[12.5px]">
      <span>AI 代码解释（DeepSeek）</span>
      <div class="flex gap-1.5">
        <button class="border border-line-subtle bg-transparent text-ink-dim rounded px-2 py-0.5 text-[11px] cursor-pointer hover:text-ink" data-action="stop" id="ai-stop-btn" title="停止解释" style="display:none">停止</button>
        <button class="border border-line-subtle bg-transparent text-ink-dim rounded px-2 py-0.5 text-[11px] cursor-pointer hover:text-ink" data-action="copy" title="复制解释">复制</button>
        <button class="border border-line-subtle bg-transparent text-ink-dim rounded px-2 py-0.5 text-[11px] cursor-pointer hover:text-ink" data-action="close" title="关闭">×</button>
      </div>
    </div>
    <div class="px-3.5 py-1.5 text-[11px] text-ink-mute border-b border-line-subtle" id="ai-status">正在准备…</div>
    <div class="flex-1 overflow-auto px-3.5 py-3 text-[12.5px] leading-[1.65] text-ink whitespace-pre-wrap break-words font-sans" id="ai-output"></div>`;
  document.body.appendChild(panel);
  panel.addEventListener("click", (e) => {
    const action = (e.target as HTMLElement).dataset.action;
    if (action === "close") closeAIPanel();
    if (action === "copy") copyAIOutput();
    if (action === "stop") stopAI();
  });
}

export function showStopButton(show) {
  const btn = document.getElementById("ai-stop-btn");
  if (btn) btn.style.display = show ? "" : "none";
}

export function stopAI() {
  if (!state.aiRunId) return;
  api.aiStop(state.aiRunId).catch(() => {});
  setAIStatus("已停止");
  showStopButton(false);
}

export function closeAIPanel() {
  const el = document.getElementById(AI_PANEL_ID);
  if (!el) return;
  // 关闭面板即终止解释：否则流式请求继续消耗 token，结果也无处展示
  if (state.aiRunId) {
    api.aiStop(state.aiRunId).catch(() => {});
    state.aiRunId = "";
  }
  el.remove();
}

export function setAIStatus(text: string, isError?: boolean) {
  const el = document.getElementById("ai-status");
  if (!el) return;
  el.textContent = text;
  el.classList.toggle("ai-error", !!isError);
}

export function appendAIOutput(text) {
  const el = document.getElementById("ai-output");
  if (!el) return;
  el.textContent += text;
  el.scrollTop = el.scrollHeight;
}

export function copyAIOutput() {
  const el = document.getElementById("ai-output");
  if (!el || !el.textContent) return;
  navigator.clipboard.writeText(el.textContent).then(
    () => setAIStatus("已复制到剪贴板"),
    () => setAIStatus("复制失败", true)
  );
}

// ---------------------------------------------------------------------------
// 主流程：解释选中代码
// ---------------------------------------------------------------------------
export function getSelectedOrAllCode() {
  if (!state.editor) return "";
  const sel = state.editor.getSelection();
  const model = state.editor.getModel();
  if (sel && !sel.isEmpty()) {
    const text = model.getValueInRange(sel);
    if (text && text.trim()) return text;
  }
  return model.getValue();
}

export async function explainSelectedCode() {
  // 上下文守卫：AI 解释依赖详情页 Monaco 中的代码
  if (!state.selectedId) {
    window.alert('请先在画廊或工具箱打开示例详情，再使用 AI 解释')
    return
  }
  // 防重入：流式解释进行中忽略重复点击（避免并发请求双倍 token、面板被重建）
  if (state.aiRunId) return
  // 无 key → 引导设置
  if (!state.aiSettings.hasKey) {
    openAISettings();
    return;
  }
  // 首次使用外发告知
  if (!state.aiSettings.acknowledged) {
    const ok = window.confirm(
      "代码解释功能会将选中的代码发送到 DeepSeek 服务器（" +
        state.aiSettings.baseUrl +
        "）进行处理。是否继续？"
    );
    if (!ok) return;
    state.aiSettings.acknowledged = true;
    api.aiSetSettings({ acknowledged: true }).catch(() => {});
  }

  const code = getSelectedOrAllCode();
  if (!code || !code.trim()) {
    // 先建面板再提示：setAIStatus 依赖 #ai-status 节点，面板不存在时提示会静默丢失
    openAIPanel();
    setAIStatus("没有可解释的代码", true);
    return;
  }
  const ex = state.examples.find((e) => e.id === state.selectedId);
  const fileName = ex?.name || "example.py";

  openAIPanel();
  setAIStatus("正在请求 DeepSeek…");
  const output = document.getElementById("ai-output");
  if (output) output.textContent = "";

  try {
    const res = await api.aiExplain(code, fileName);
    if (res.status === "error" || res.error) {
      const err = res.error || "unknown";
      if (err === "no_api_key") {
        state.aiSettings.hasKey = false;
        setAIStatus("API Key 未配置，请先在设置中填写", true);
      } else {
        setAIStatus("请求失败：" + err, true);
      }
      return;
    }
    state.aiRunId = res.run_id || "";
    setAIStatus("正在生成解释…");
    showStopButton(true);
  } catch (err) {
    setAIStatus("调用失败：" + (err as any).message, true);
    showStopButton(false);
  }
}

// ---------------------------------------------------------------------------
// 初始化：加载设置 + 订阅流式事件 + 绑定按钮
// ---------------------------------------------------------------------------
export async function loadAISettings() {
  try {
    const s = await api.aiGetSettings();
    state.aiSettings.hasKey = !!s.hasKey;
    state.aiSettings.model = s.model || "deepseek-chat";
    state.aiSettings.baseUrl = s.baseUrl || "https://api.deepseek.com";
    state.aiSettings.acknowledged = !!s.acknowledged;
  } catch (err) {
    console.error("[ai] 加载设置失败:", err);
  }
}

export function initAI() {
  // 流式事件订阅（全局，匹配当前 run_id）
  api.on("aiExplainChunk", (data) => {
    if (data.run_id && state.aiRunId && data.run_id !== state.aiRunId) return;
    appendAIOutput(data.text || "");
  });
  api.on("aiExplainDone", (data) => {
    if (data.run_id && state.aiRunId && data.run_id !== state.aiRunId) return;
    const tokens = data.tokens ? `（约 ${data.tokens} tokens）` : "";
    setAIStatus("完成" + tokens);
    state.aiRunId = "";
    showStopButton(false);
  });
  api.on("aiExplainError", (data) => {
    if (data.run_id && state.aiRunId && data.run_id !== state.aiRunId) return;
    setAIStatus("生成失败：" + (data.error || "unknown"), true);
    state.aiRunId = "";
    showStopButton(false);
  });

  // 按钮绑定：工具栏与详情页头部各有一个 AI 解释按钮
  // （此前两个节点共用同一 id，getElementById 只能拿到第一个，详情页按钮从未生效）
  for (const id of ["btn-ai-explain", "btn-ai-explain-toolbar"]) {
    const btnExplain = document.getElementById(id);
    if (btnExplain) btnExplain.addEventListener("click", explainSelectedCode);
  }
  const btnSettings = document.getElementById("btn-ai-settings");
  if (btnSettings) btnSettings.addEventListener("click", openAISettings);
}
