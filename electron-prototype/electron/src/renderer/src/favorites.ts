// favorites.ts：示例收藏
// 数据由主进程持久化到 userData/favorites.json（复用 store IPC）。
// 收藏入口：画廊/工具箱卡片星标、详情页「收藏」按钮；
// 「⭐ 只看收藏」芯片与搜索、主题、质量分等维度可任意叠加。
// 依赖：state（state.ts）、api（sidecar-client.ts）；运行时调用 app.ts 的渲染函数（延迟 import）。

import { state } from './state'
import { api } from './sidecar-client'
import { applyFilters, applyAllFilters } from './app'

// ---------------------------------------------------------------------------
// 持久化
// ---------------------------------------------------------------------------
export async function loadFavorites() {
  try {
    const data = await api.storeGet("favorites");
    state.favorites = new Set(Array.isArray(data) ? data : []);
  } catch (err) {
    console.error("加载收藏失败:", err);
    state.favorites = new Set();
  }
  updateFavChip();
  updateActionBarFav();
  // 收藏可能晚于示例列表/首次渲染返回：与 loadHistory 对称地重筛一次，
  // 否则卡片星标与「只看收藏」结果是加载期的过期快照（examples 为空时是廉价空转）
  applyAllFilters();
}

export async function persistFavorites() {
  try {
    await api.storeSet("favorites", Array.from(state.favorites));
  } catch (err) {
    console.error("保存收藏失败:", err);
  }
  updateFavChip();
  updateActionBarFav();
}

export function isFavorite(id) {
  return !!id && state.favorites.has(id);
}

/** 切换收藏，返回切换后的状态（true=已收藏） */
export function toggleFavorite(id) {
  if (!id) return false;
  const faved = !state.favorites.has(id);
  if (faved) state.favorites.add(id);
  else state.favorites.delete(id);
  persistFavorites();
  refreshFavoritesViews();
  return faved;
}

// 收藏状态变化后刷新当前可见视图（不重置展开状态）
export function refreshFavoritesViews() {
  if (typeof applyAllFilters === "function") {
    applyAllFilters();
  } else if (typeof applyFilters === "function") {
    applyFilters();
  }
  updateActionBarFav();
}

// ---------------------------------------------------------------------------
// UI
// ---------------------------------------------------------------------------
export function updateFavChip() {
  document.querySelectorAll(".fav-chip").forEach((chip) => {
    const el = chip as HTMLElement;
    el.classList.toggle("active", state.favOnly);
    el.textContent = state.favorites.size ? `⭐ 收藏 ${state.favorites.size}` : "⭐ 收藏";
  });
}

export function updateActionBarFav() {
  const btn = document.getElementById("btn-fav-toggle");
  if (!btn) return;
  const faved = isFavorite(state.selectedId);
  btn.textContent = faved ? "★ 已收藏" : "☆ 收藏";
  btn.classList.toggle("is-faved", faved);
}

export function initFavorites() {
  // 「只看收藏」快捷筛选（画廊/工具箱芯片，与其他维度可叠加）
  document.querySelectorAll(".fav-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      state.favOnly = !state.favOnly;
      updateFavChip();
      if (typeof applyAllFilters === "function") applyAllFilters();
    });
  });
  // 详情页收藏按钮
  const btn = document.getElementById("btn-fav-toggle");
  if (btn) {
    btn.addEventListener("click", () => {
      if (state.selectedId) toggleFavorite(state.selectedId);
    });
  }
}
