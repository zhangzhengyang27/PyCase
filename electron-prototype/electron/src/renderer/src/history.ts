// history.ts：运行历史
// 数据由主进程持久化到 userData/history.json（渲染层不直接碰文件系统）；
// 最多保留 HISTORY_CAP 条，支持重跑、清空、导出 .log。
// 依赖：state（state.ts）、api（sidecar-client.ts）、escapeHtml（utils.ts），
//       以及 app.ts 的 selectExample / runExample / switchView（延迟 import 避免循环依赖）。

import { state } from './state'
import { api } from './sidecar-client'
import { escapeHtml, BTN_GHOST_CLS } from './utils'
import * as FilterEngine from './filter-engine'
import { openDetail, refreshDetailHistory, runFromDetail } from './detail'
import { applyArgsToForm } from './args-form'
import { switchView, applyAllFilters } from './app'
const HISTORY_CAP = 500

// ---------------------------------------------------------------------------
// 持久化
// ---------------------------------------------------------------------------
export async function loadHistory() {
  try {
    const data = await api.storeGet("history");
    state.runHistory = Array.isArray(data) ? data : [];
  } catch (err) {
    console.error("加载运行历史失败:", err);
    state.runHistory = [];
  }
  updateHistoryBadge();
  // 重建运行状态 facet 索引（列表可能尚未加载，loadExamples 会再补建一次）
  if (typeof FilterEngine !== "undefined") {
    state.runStatusIndex = FilterEngine.buildRunStatusIndex(state.runHistory);
  }
  if (typeof applyAllFilters === "function") applyAllFilters();
}

export async function persistHistory() {
  try {
    await api.storeSet("history", state.runHistory);
  } catch (err) {
    console.error("保存运行历史失败:", err);
  }
  updateHistoryBadge();
}

/**
 * 一次运行结束时记录历史。
 * @param {{id:string,name:string,args:string[],startedAt:number}|null} meta 运行前记录的元信息
 * @param {number} exitCode 退出码
 */
export function recordHistory(meta, exitCode) {
  if (!meta) return;
  state.runHistory.unshift({
    ts: new Date(meta.startedAt).toISOString(),
    id: meta.id,
    name: meta.name,
    args: meta.args || [],
    duration_ms: Math.max(0, Date.now() - meta.startedAt),
    exit_code: exitCode,
    ok: exitCode === 0,
  });
  if (state.runHistory.length > HISTORY_CAP) state.runHistory.length = HISTORY_CAP;
  persistHistory();
  // 更新运行状态 facet（最近一条决定该示例的状态）
  if (typeof FilterEngine !== "undefined") {
    state.runStatusIndex = FilterEngine.buildRunStatusIndex(state.runHistory);
    if (typeof applyAllFilters === "function") applyAllFilters();
  }
  // 详情页内嵌历史同步刷新
  if (typeof refreshDetailHistory === "function") refreshDetailHistory();
}

export async function clearHistory() {
  state.runHistory = [];
  if (typeof FilterEngine !== "undefined") {
    state.runStatusIndex = FilterEngine.buildRunStatusIndex([]);
  }
  await persistHistory();
  if (typeof applyAllFilters === "function") applyAllFilters();
  renderHistoryPanel();
}

// ---------------------------------------------------------------------------
// 展示辅助
// ---------------------------------------------------------------------------
export function formatHistoryTime(iso) {
  const d = new Date(iso);
  const pad = (n) => String(n).padStart(2, "0");
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(
    d.getSeconds()
  )}`;
}

export function formatDuration(ms) {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export function updateHistoryBadge() {
  const btn = document.getElementById("btn-history");
  if (!btn) return;
  btn.textContent = state.runHistory.length ? `🕘 历史 ${state.runHistory.length}` : "🕘 历史";
}

export function historyAsLog() {
  return state.runHistory
    .map((h) => {
      const status = h.ok ? "成功" : `失败(exit=${h.exit_code})`;
      const args = h.args && h.args.length ? ` ${h.args.join(" ")}` : "";
      return `[${formatHistoryTime(h.ts)}] ${status} ${formatDuration(h.duration_ms)} ${h.name}${args}`;
    })
    .join("\n");
}

export async function exportHistoryLog() {
  if (!state.runHistory.length) {
    window.alert("暂无运行历史可导出");
    return;
  }
  const stamp = new Date().toISOString().slice(0, 10);
  try {
    const res = await api.saveTextFile({
      content: historyAsLog() + "\n",
      defaultName: `run-history-${stamp}.log`,
    });
    if (res && res.error) window.alert(`导出失败：${res.error}`);
  } catch (err) {
    window.alert(`导出失败：${(err as any).message}`);
  }
}

// 从历史记录重跑：打开该示例的详情页，等参数表单装载完成后再回填记录参数并运行。
// openDetail 内的 parseArgs 是异步的：不等它完成就回填/收集，表单与
// state.currentArgs 仍是上一个示例的，会静默填错参或丢参
export async function rerunFromHistory(entry) {
  const ex = state.examples.find((e) => e.id === entry.id);
  if (!ex) {
    window.alert("当前示例列表中找不到该示例，可能已被移除");
    return;
  }
  closeHistoryPanel();
  if (state.activeView === "runner") switchView("gallery");
  await openDetail(entry.id);
  // 等待期间用户可能已切换到别的示例
  if (state.selectedId !== entry.id) return;
  applyArgsToForm(entry.args || []);
  runFromDetail();
}

// ---------------------------------------------------------------------------
// 弹窗面板（自建 DOM，样式复用主题源码弹窗并补充 .history-* 类）
// ---------------------------------------------------------------------------
export function _onHistoryEscape(e) {
  if (e.key === "Escape") closeHistoryPanel();
}

export function initHistoryPanel() {
  const modal = document.createElement("div");
  modal.className = "theme-code-modal history-modal fixed inset-0 z-[1000] flex items-center justify-center";
  modal.id = "history-modal";
  modal.style.display = "none";
  modal.innerHTML = `
    <div class="theme-code-modal-backdrop absolute inset-0 bg-black/45" data-close="1"></div>
    <div class="theme-code-modal-box history-modal-box relative w-[min(680px,90vw)] max-h-[80vh] flex flex-col bg-panel border border-line-subtle rounded-[10px] shadow-[0_12px_40px_rgba(0,0,0,0.25)]">
      <div class="theme-code-modal-header flex items-center justify-between px-4 py-3 border-b border-line-subtle shrink-0">
        <span class="theme-code-modal-title text-[13px] font-[590] text-ink-dim truncate">运行历史</span>
        <div class="history-header-actions flex gap-1.5 items-center">
          <button class="${BTN_GHOST_CLS}" id="history-export">导出 .log</button>
          <button class="${BTN_GHOST_CLS}" id="history-clear">清空</button>
          <button class="${BTN_GHOST_CLS}" id="history-close">✕</button>
        </div>
      </div>
      <div class="history-list overflow-y-auto max-h-[70vh] py-1.5" id="history-list"></div>
    </div>`;
  document.body.appendChild(modal);
  modal.querySelectorAll("[data-close]").forEach((el) => el.addEventListener("click", closeHistoryPanel));
  document.getElementById("history-close")!.addEventListener("click", closeHistoryPanel);
  document.getElementById("history-clear")!.addEventListener("click", () => {
    if (state.runHistory.length && window.confirm("确定清空全部运行历史？")) clearHistory();
  });
  document.getElementById("history-export")!.addEventListener("click", exportHistoryLog);
  // Escape 关闭：幂等（先移除再添加），避免 init 重复调用时叠加监听器
  document.removeEventListener("keydown", _onHistoryEscape);
  document.addEventListener("keydown", _onHistoryEscape);

  const btn = document.getElementById("btn-history");
  if (btn) btn.addEventListener("click", openHistoryPanel);
}

export function openHistoryPanel() {
  renderHistoryPanel();
  const modal = document.getElementById("history-modal");
  if (modal) modal.style.display = "";
}

export function closeHistoryPanel() {
  const modal = document.getElementById("history-modal");
  if (modal) modal.style.display = "none";
}

export function renderHistoryPanel() {
  const list = document.getElementById("history-list");
  if (!list) return;
  if (!state.runHistory.length) {
    list.innerHTML = '<div class="history-empty px-4 py-9 text-center text-[13px] text-ink-dim">还没有运行记录，运行一个示例后会自动记录到这里</div>';
    return;
  }
  const frag = document.createDocumentFragment();
  state.runHistory.forEach((h) => {
    const row = document.createElement("div");
    row.className =
      "history-row flex items-center justify-between gap-3 px-4 py-2 border-b border-line-subtle hover:bg-[rgba(127,127,127,0.06)]" +
      (h.ok ? "" : " failed");
    const left = document.createElement("div");
    left.className = "history-row-main flex items-center gap-2.5 min-w-0 flex-1";
    const status = document.createElement("span");
    status.className = h.ok
      ? "history-badge shrink-0 text-[11px] font-[590] px-2 py-0.5 rounded-full text-[#1a7f37] bg-[rgba(63,185,80,0.14)]"
      : "history-badge shrink-0 text-[11px] font-[590] px-2 py-0.5 rounded-full text-[#cf222e] bg-[rgba(248,81,73,0.14)]";
    status.textContent = h.ok ? "成功" : `失败 ${h.exit_code}`;
    const name = document.createElement("span");
    name.className = "history-name shrink-0 max-w-[240px] text-[12.5px] text-ink truncate";
    name.textContent = h.name;
    name.title = h.id;
    const meta = document.createElement("span");
    meta.className = "history-meta text-[11.5px] text-ink-dim truncate";
    meta.textContent = `${formatHistoryTime(h.ts)} · ${formatDuration(h.duration_ms)}${
      h.args && h.args.length ? " · 参数 " + h.args.join(" ") : ""
    }`;
    left.append(status, name, meta);
    const rerun = document.createElement("button");
    rerun.className = BTN_GHOST_CLS;
    rerun.textContent = "重跑";
    rerun.addEventListener("click", () => rerunFromHistory(h));
    row.append(left, rerun);
    frag.appendChild(row);
  });
  list.innerHTML = "";
  list.appendChild(frag);
}
