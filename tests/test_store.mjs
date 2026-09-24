// store.ts 单元测试：Vue 渲染层的状态编排（示例加载 / 派生筛选 / 收藏 / 偏好 / 高危门）
//
// 通过 renderer-loader 加载真实 store.ts —— 'vue' 从工程 node_modules 真实加载
// （ref/computed/watch 都是真响应式，不是桩），仅以替身替换两个副作用依赖：
//   './toast'              → pushToast 空实现（DOM 提示）
//   './src/sidecar-client' → 受控的 api 桩（IPC 边界）
// store.ts 是模块级单例，各用例之间靠 resetState() 归零状态。
import { createRendererLoader } from "./renderer-loader.mjs";

globalThis.window = { confirm: () => true };

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ---------------------------------------------------------------------------
// IPC 桩：记录调用、按 storeData / fixtures 返回数据
// ---------------------------------------------------------------------------
const calls = [];
let fixtures = [];
let storeData = {};

const api = {
  storeGet: async (key) => (Object.prototype.hasOwnProperty.call(storeData, key) ? storeData[key] : null),
  storeSet: async (key, value) => {
    calls.push(["storeSet", key, value]);
  },
  listExamples: async () => {
    if (!fixtures) throw new Error("sidecar 连接失败");
    return { examples: fixtures };
  },
  runExample: async (params) => {
    calls.push(["runExample", params]);
    return { run_id: "run-1" };
  },
  parseArgs: async () => ({ args: [] }),
  listAssets: async () => ({ assets: [] })
};

const S = createRendererLoader(
  { "./toast": { pushToast: () => {} }, "./src/sidecar-client": { api } },
  { packages: ["vue"] }
).load("store");

// ---------------------------------------------------------------------------
// 夹具
// ---------------------------------------------------------------------------
function mkExamples() {
  return [
    { id: "t1", name: "alpha.py", category: "topics", code: "import numpy as np\n", tags: ["基础"], quality_score: 90, run_status: "runnable" },
    { id: "t2", name: "beta.py", category: "topics", code: "import pygame\n", tags: ["游戏"], quality_score: 60, run_status: "missing_deps" },
    { id: "t3", name: "gamma.py", category: "topics", code: "import turtle\n", tags: [], quality_score: 30, run_status: "empty" },
    { id: "tool1", name: "tool_a.py", category: "tools", code: "import requests\n", tags: ["工具"], quality_score: 70, run_status: "runnable" },
    { id: "proj1", name: "delta.py", category: "projects", code: "print(1)\n", tags: [], quality_score: 80, run_status: "runnable" },
    { id: "risk", name: "risky.py", category: "topics", code: "import shutil\n", tags: [], quality_score: 50, run_status: "risky", risk_high: true }
  ];
}

async function resetState() {
  fixtures = mkExamples();
  storeData = {};
  calls.length = 0;
  S.examples.value = [];
  S.loadError.value = "";
  S.searchQuery.value = "";
  S.toolSearchQuery.value = "";
  S.activeView.value = "gallery";
  S.galleryMode.value = "overview";
  S.activeTheme.value = "all";
  S.minQuality.value = 0;
  S.sortBy.value = "quality_desc";
  S.galleryLimit.value = 120;
  S.activeSectionTags.value = [];
  S.activeCategory.value = "all";
  S.viewMode.value = "grid";
  S.favorites.value = new Set();
  S.favOnly.value = false;
  S.activeRunStatus.value = "all";
  S.activeRunnable.value = "all";
  S.activeTags.value = new Set();
  S.runHistory.value = [];
  S.runTimeout.value = 30;
  S.skipHighRiskConfirm.value = false;
  S.pendingHighRiskRun.value = null;
  S.selectedId.value = null;
  S.isDirty.value = false;
  // 两个搜索框都有 120ms 防抖，等它们落定，避免跨用例串味
  await sleep(140);
}

/** 归零状态 + 灌入夹具 + 走一次真实 loadAll */
async function boot() {
  await resetState();
  await S.loadAll();
}

// ---------------------------------------------------------------------------
// 断言工具
// ---------------------------------------------------------------------------
let failed = 0;
let total = 0;
function check(desc, cond) {
  total++;
  if (!cond) {
    failed++;
    console.error(`  ✗ ${desc}`);
  } else {
    console.log(`  ✓ ${desc}`);
  }
}
function ids(list) {
  return list.map((e) => e.id).join(",");
}
function setCalls(key) {
  return calls.filter((c) => c[0] === "storeSet" && c[1] === key);
}

// ===========================================================================
console.log("画廊池与工具箱互补");
await boot();
check("galleryExamples 排除 tools（6 → 5）", S.galleryExamples.value.length === 5);
check("galleryExamples 不含 tool1", !S.galleryExamples.value.some((e) => e.id === "tool1"));
check("toolsTotal 只数 tools（=1）", S.toolsTotal.value === 1);
check("toolboxItems 只含 tools", ids(S.toolboxItems.value) === "tool1");
check("filtered 默认等于画廊池", ids(S.filtered.value) === "t1,t2,t3,proj1,risk");

console.log("排序");
check("默认 quality_desc 降序", ids(S.sortedGallery.value) === "t1,proj1,t2,risk,t3");
S.sortBy.value = "name";
check("按文件名升序", ids(S.sortedGallery.value) === "t1,t2,proj1,t3,risk");
S.sortBy.value = "last_run";
check("无运行历史时 last_run 稳定回退", S.sortedGallery.value.length === 5);
S.sortBy.value = "quality_desc";
S.galleryLimit.value = 2;
check("shownGallery 受 galleryLimit 截断", S.shownGallery.value.length === 2);
S.galleryLimit.value = 120;

console.log("收藏");
calls.length = 0;
check("toggleFavorite 首次返回 true", S.toggleFavorite("t1") === true);
check("isFavorite 生效", S.isFavorite("t1") === true);
check("收藏落盘 storeSet('favorites')", setCalls("favorites").length === 1);
check("落盘内容是 id 数组", JSON.stringify(setCalls("favorites")[0][2]) === '["t1"]');
check("再次 toggle 返回 false", S.toggleFavorite("t1") === false);
check("toggle 后不再收藏", S.isFavorite("t1") === false);
check("undefined id 不崩且返回 false", S.toggleFavorite(undefined) === false);
check("isFavorite(undefined) 为 false", S.isFavorite(undefined) === false);
S.favorites.value = new Set(["t2"]);
S.favOnly.value = true;
check("favOnly 只留收藏项", ids(S.filtered.value) === "t2");
S.favOnly.value = false;

console.log("筛选重置");
S.activeTheme.value = "turtle";
S.minQuality.value = 80;
S.activeTags.value = new Set(["基础"]);
S.activeSectionTags.value = ["x"];
S.activeCategory.value = "projects";
S.activeRunStatus.value = "ok";
S.activeRunnable.value = "risky";
S.favOnly.value = true;
calls.length = 0;
S.clearFilters();
check(
  "clearFilters 归零全部维度",
  S.activeTheme.value === "all" &&
    S.minQuality.value === 0 &&
    S.activeTags.value.size === 0 &&
    S.activeSectionTags.value.length === 0 &&
    S.activeCategory.value === "all" &&
    S.activeRunStatus.value === "all" &&
    S.activeRunnable.value === "all"
);
check("clearFilters 不动 favOnly", S.favOnly.value === true);
check("clearFilters 持久化偏好", setCalls("viewPrefs").length === 1);
S.clearAllFilters();
check("clearAllFilters 连 favOnly 一起清", S.favOnly.value === false);

console.log("芯片反向应用（removeChip）");
S.favOnly.value = true;
S.removeChip({ key: "fav" });
check("fav 芯片 → favOnly=false", S.favOnly.value === false);
S.activeRunStatus.value = "failed";
S.removeChip({ key: "runStatus" });
check("runStatus 芯片 → all", S.activeRunStatus.value === "all");
S.activeRunnable.value = "broken";
S.removeChip({ key: "runnable" });
check("runnable 芯片 → all", S.activeRunnable.value === "all");
S.activeTheme.value = "turtle";
calls.length = 0;
S.removeChip({ key: "theme" });
check("theme 芯片 → all 且持久化", S.activeTheme.value === "all" && setCalls("viewPrefs").length === 1);
S.activeSectionTags.value = ["a", "b"];
S.removeChip({ key: "tagsAny" });
check("tagsAny 芯片 → 清空", S.activeSectionTags.value.length === 0);
S.activeCategory.value = "projects";
S.removeChip({ key: "category" });
check("category 芯片 → all", S.activeCategory.value === "all");
S.minQuality.value = 90;
calls.length = 0;
S.removeChip({ key: "quality" });
check("quality 芯片 → 0 且持久化", S.minQuality.value === 0 && setCalls("viewPrefs").length === 1);
S.activeTags.value = new Set(["基础", "游戏"]);
S.removeChip({ key: "tag", value: "基础" });
check("tag 芯片只删该标签", JSON.stringify([...S.activeTags.value]) === '["游戏"]');
S.searchQuery.value = "plot";
S.removeChip({ key: "q" });
check("q 芯片 → 清空搜索框", S.searchQuery.value === "");

console.log("浏览态下钻：三种范围互斥");
await boot();
S.activeTheme.value = "turtle";
S.openGalleryBrowse({ tags: ["爬虫", "办公"] });
check(
  "tags 下钻清空 theme/category",
  S.activeSectionTags.value.join(",") === "爬虫,办公" && S.activeTheme.value === "all" && S.activeCategory.value === "all"
);
S.openGalleryBrowse({ category: "projects" });
check(
  "category 下钻清空 tags/theme",
  S.activeCategory.value === "projects" && S.activeSectionTags.value.length === 0 && S.activeTheme.value === "all"
);
calls.length = 0;
S.openGalleryBrowse({ theme: "viz" });
check(
  "theme 下钻清空 tags/category 且持久化",
  S.activeTheme.value === "viz" && S.activeSectionTags.value.length === 0 && S.activeCategory.value === "all" && setCalls("viewPrefs").length === 1
);
check("下钻即进入浏览态", S.galleryMode.value === "browse");
S.openGalleryBrowse({ favOnly: true });
check("favOnly 下钻置位", S.favOnly.value === true);

console.log("loadAll：成功路径");
await resetState();
storeData = {
  history: [{ id: "t1", ok: true, ts: "2026-09-01T00:00:00Z" }],
  favorites: ["t2", "proj1"],
  viewPrefs: { sortBy: "name", activeTheme: "turtle", minQuality: 80, viewMode: "list" },
  safetyPrefs: { skipHighRiskConfirm: true },
  runPrefs: { timeout: 120 }
};
await S.loadAll();
check("示例装载完整", S.examples.value.length === 6);
check("loading 归位", S.loading.value === false && S.loadError.value === "");
check("恢复收藏", S.isFavorite("t2") && S.isFavorite("proj1"));
check("恢复运行历史", S.runHistory.value.length === 1);
check("恢复排序偏好", S.sortBy.value === "name");
check("恢复主题偏好", S.activeTheme.value === "turtle");
check("恢复质量分偏好", S.minQuality.value === 80);
check("恢复密度偏好", S.viewMode.value === "list");
check("恢复高危确认开关", S.skipHighRiskConfirm.value === true);
check("恢复运行超时", S.runTimeout.value === 120);
const t1 = S.examples.value.find((e) => e.id === "t1");
check("构建 _codeLower 预处理缓存", t1._codeLower === "import numpy as np\n");
check("构建 _tagsAll（元数据 + import 标签）", t1._tagsAll.includes("基础") && t1._tagsAll.includes("numpy"));

console.log("loadAll：脏偏好被拒（不写入非法状态）");
await resetState();
storeData = { viewPrefs: { sortBy: "bogus", activeTheme: "不存在的主题", minQuality: -5, viewMode: "weird" } };
await S.loadAll();
check("非法 sortBy 被拒", S.sortBy.value === "quality_desc");
check("非法 activeTheme 被拒（否则引擎会静默放行全部）", S.activeTheme.value === "all");
check("负 minQuality 被拒", S.minQuality.value === 0);
check("非法 viewMode 被拒", S.viewMode.value === "grid");

console.log("loadAll：失败路径");
await resetState();
fixtures = null;
await S.loadAll();
check("错误信息落到 loadError", S.loadError.value === "sidecar 连接失败");
check("失败时示例清空", S.examples.value.length === 0);
check("失败后 loading 归位", S.loading.value === false);

console.log("搜索防抖（输入即时、筛选延迟 120ms）");
await boot();
S.searchQuery.value = "pygame";
check("输入后筛选尚未生效", S.filtered.value.length === 5);
await sleep(150);
check("防抖后筛选生效（只剩 beta.py）", ids(S.filtered.value) === "t2");
S.toolSearchQuery.value = "tool_a";
await sleep(150);
check("工具箱搜索独立生效", ids(S.toolboxItems.value) === "tool1");

console.log("facet 计数口径");
await boot();
const base = S.facetCounts.value;
// 画廊池 5 条：t1(runnable) t2(missing_deps) t3(empty) proj1(runnable) risk(risky)
check("runnable 计数 = 2（t1/proj1）", base.runnableCounts.get("runnable") === 2);
check("missing_deps / empty 各 1", base.runnableCounts.get("missing_deps") === 1 && base.runnableCounts.get("empty") === 1);
check("质量分 ≥90 计 1（t1）", base.qualityCounts.get(90) === 1);
check("质量分 ≥80 计 2（t1/proj1）", base.qualityCounts.get(80) === 2);
check("质量分 ≥60 计 3（t1/t2/proj1）", base.qualityCounts.get(60) === 3);
check("质量分不设 0 档（0 分桶无意义）", !base.qualityCounts.has(0));
const beforeTheme = S.facetCounts.value.runnableCounts.get("runnable");
S.activeTheme.value = "turtle";
check("选中主题后 facet 计数不随自身维度缩放", S.facetCounts.value.runnableCounts.get("runnable") === beforeTheme);
S.activeTheme.value = "all";
check("标签 facet 含已选中但掉出 TopN 的标签（计数 0 仍展示）", (() => {
  S.activeTags.value = new Set(["不存在的标签"]);
  const facets = S.tagFacetsFor("gallery");
  const hit = facets.find((f) => f.tag === "不存在的标签");
  S.activeTags.value = new Set();
  return !!hit && hit.count === 0;
})());

console.log("运行超时持久化");
calls.length = 0;
S.setRunTimeout(45);
check("runTimeout 更新", S.runTimeout.value === 45);
check("runPrefs 落盘", JSON.stringify(setCalls("runPrefs")[0][2]) === '{"timeout":45}');

console.log("高危运行确认门（单点守卫）");
await boot();
// 用例之间复位运行态：真实链路靠 run_finished 事件复位，测试里没有事件源
const settleRun = () => {
  S.isRunning.value = false;
  S.currentRunId.value = null;
  calls.length = 0;
};
const runCount = () => calls.filter((c) => c[0] === "runExample").length;

await S.runFromCard("risk");
check("高危示例不直接运行", runCount() === 0);
check("挂起待确认", S.pendingHighRiskRun.value?.id === "risk");
S.resolveHighRiskRun(true, false);
await sleep(0);
check("确认后真正发起运行", runCount() === 1);
check("确认后挂起态清空", S.pendingHighRiskRun.value === null);
check("未勾选「不再提示」则不持久化", S.skipHighRiskConfirm.value === false && setCalls("safetyPrefs").length === 0);

settleRun();
await S.runFromCard("risk");
S.resolveHighRiskRun(true, true);
await sleep(0);
check("勾选「不再提示」→ 开关置位", S.skipHighRiskConfirm.value === true);
check("开关落盘 safetyPrefs", JSON.stringify(setCalls("safetyPrefs")[0][2]) === '{"skipHighRiskConfirm":true}');
check("本次运行同样发起", runCount() === 1);

settleRun();
await S.runFromCard("risk");
await sleep(0);
check("开关置位后高危示例直接运行（不再挂起）", runCount() === 1 && S.pendingHighRiskRun.value === null);

settleRun();
await S.runFromCard("t1");
await sleep(0);
check("低危示例本就不经确认门", runCount() === 1);

settleRun();
S.skipHighRiskConfirm.value = false; // 复位开关，重新走确认门
await S.runFromCard("risk");
check("拒绝确认则不运行", (() => {
  S.resolveHighRiskRun(false, false);
  return runCount() === 0 && S.pendingHighRiskRun.value === null;
})());

console.log("loadAll 失败后不残留旧数据");
await boot();
fixtures = null;
await S.loadAll();
check("重载失败清空旧示例（不展示过期数据）", S.examples.value.length === 0);

// ===========================================================================
if (failed) {
  console.error(`\n${failed} / ${total} 项断言失败`);
  process.exit(1);
}
console.log(`\n全部通过（${total} 项断言）`);
