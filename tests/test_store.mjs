// store 域单元测试：Vue 渲染层的状态编排（示例加载 / 派生筛选 / 收藏 / 偏好 / 高危门）
//
// 分域后（B3-3）逐个加载真实模块并拍平成一个命名空间，断言一字不改：
//   store/catalog（示例目录/筛选）· store/detail（详情/运行）· store/prefs（持久化）
//   · store/index（启动装载 loadAll）
// 'vue' 从工程 node_modules 真实加载（ref/computed/watch 都是真响应式，不是桩），
// 仅以替身替换两个副作用依赖：
//   '../../toast'        → pushToast 空实现（DOM 提示）
//   '../sidecar-client'  → 受控的 api 桩（IPC 边界）
// 各域都是模块级单例，各用例之间靠 resetState() 归零状态。
import { createRendererLoader } from "./renderer-loader.mjs";

globalThis.window = { confirm: () => true };

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ---------------------------------------------------------------------------
// IPC 桩：记录调用、按 storeData / fixtures 返回数据
// ---------------------------------------------------------------------------
const calls = [];
let fixtures = [];
let storeData = {};
// parseArgs 的返回：按需注入参数规格（必填门禁用例要它）
let argFixtures = [];

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
  parseArgs: async () => ({ args: argFixtures }),
  listAssets: async () => ({ assets: [] }),
  // 服务端检索（契约 §5）：v2 列表不含 code，代码搜索由 sidecar 按需读文件后回命中原因
  searchExamples: async (query) => {
    calls.push(["searchExamples", query]);
    return { query, hits: query === "pygame" ? [{ id: "t2", reason: "code" }] : [] };
  }
};

// mock 键 = 源码里的字面说明符（域文件在 src/store/ 下，故为 '../../toast' / '../sidecar-client'）
const loader = createRendererLoader(
  { "../../toast": { pushToast: () => {} }, "../sidecar-client": { api } },
  { packages: ["vue"] }
);
// 注意用 "src/store/xxx" 形式的键：加载器内部把相对导入解析成同一形式，
// 否则同一个模块会被加载两份（模块级单例各持一份状态，断言会莫名其妙地失败）
const S = Object.assign(
  {},
  loader.load("src/store/catalog"),
  loader.load("src/store/detail"),
  loader.load("src/store/prefs"),
  loader.load("src/store/index")
);

// ---------------------------------------------------------------------------
// 夹具
// ---------------------------------------------------------------------------
function mkExamples() {
  return [
    { id: "t1", name: "alpha.py", category: "topics", code: "import numpy as np\n", tags: ["基础"], quality_score: 90, run_status: "runnable", import_tags: ["numpy"] },
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
  argFixtures = [];
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
  // 必填门禁：参数规格与「表单反向注册的校验器」都是模块级单例，必须归零，
  // 否则上一个用例注册的校验器会替下一个用例作答（典型跨用例串味）
  S.currentArgs.value = [];
  S.registerArgsValidator(null);
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
// v2：列表不含 code（契约 §5），代码侧缓存置空；import 标签用服务端下发的派生事实
check("_codeLower 置空（v2 不再从 code 反推）", t1._codeLower === "");
check("构建 _tagsAll（元数据标签 + 服务端 import_tags）", t1._tagsAll.includes("基础") && t1._tagsAll.includes("numpy"));

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

console.log("搜索防抖（元数据 120ms；代码命中走服务端检索，260ms 防抖）");
await boot();
S.searchQuery.value = "pygame";
check("输入后筛选尚未生效", S.filtered.value.length === 5);
await sleep(150);
check("元数据维度无命中（pygame 只在代码里，先落空再等服务端）", S.filtered.value.length === 0);
await sleep(220);
check("服务端代码命中生效（只剩 beta.py）", ids(S.filtered.value) === "t2");
check("代码命中集只收 reason=code 的条目", S.catalogTestHooks().codeHitIds().includes("t2"));
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

console.log("必填参数门禁（requiredArgsMissing / runFromDetail）");
await boot();
// 必填门禁只看参数规格（spec），不看表单里已填的值——表单值由 ArgsForm 反向注册的
// 校验器提供。这里先测「无校验器」的纯 spec 回退口径。
const runCountReq = () => calls.filter((c) => c[0] === "runExample").length;
const specOf = (over) => ({ name: "--token", flags: ["--token"], dest: "token", type: "str", required: true, ...over });
// 每次「应该起跑」的尝试前复位运行态：beginRun 会同步把 isRunning 置真，
// 而 runFromDetail 开头就挡 isRunning —— 不复位的话第二次调用永远不会起跑（假红）
const settleReq = () => {
  S.isRunning.value = false;
  S.currentRunId.value = null;
  calls.length = 0;
};

// ① 必填 + 无默认值 → 缺失
S.currentArgs.value = [specOf({})];
check("必填无默认值 → requiredArgsMissing", S.requiredArgsMissing.value === true);
settleReq();
S.selectedId.value = "t1";
S.runFromDetail();
check("必填无默认值 → runFromDetail 不起跑", runCountReq() === 0);

// ② 必填 + sidecar 返回 default: null（真实数据形状）→ 仍是缺失
//    回归护栏：曾只判 === undefined，导致整条门禁是死代码
S.currentArgs.value = [specOf({ default: null })];
check("必填 default:null（真实形状）→ 仍视为缺失", S.requiredArgsMissing.value === true);

// ③ 必填 + 有默认值 → 不算缺失（用户裁定：必填可以有默认值）
S.currentArgs.value = [specOf({ default: "fallback" })];
check("必填有默认值 → 不算缺失", S.requiredArgsMissing.value === false);
settleReq();
S.runFromDetail();
check("必填有默认值 → runFromDetail 正常起跑", runCountReq() === 1);

// ④ 布尔开关：store_true / store_false 永远有值，不进门禁
S.currentArgs.value = [specOf({ type: "bool", action: "store_true" }), specOf({ type: "bool", action: "store_false" })];
check("布尔必填项不进门禁", S.requiredArgsMissing.value === false);

// ⑤ 非必填参数不受影响
S.currentArgs.value = [specOf({ required: false })];
check("非必填参数不进门禁", S.requiredArgsMissing.value === false);

// ⑥ 表单反向注册的校验器优先于 spec 回退：用户已填值时不再拦
S.currentArgs.value = [specOf({})];
S.registerArgsValidator(() => false);
check("校验器说「已填」→ 门禁放行（spec 仍看着缺失）", S.requiredArgsMissing.value === false);
settleReq();
S.runFromDetail();
check("放行后 runFromDetail 起跑", runCountReq() === 1);
S.registerArgsValidator(null);
check("校验器注销 → 回退到 spec 判定", S.requiredArgsMissing.value === true);

// ⑦ 卡片入口同样受门禁约束（runFromCard → openDetail 拿到必填参数后拦住）
settleReq();
S.selectedId.value = null;
S.currentArgs.value = [];
argFixtures = [specOf({})];
await S.runFromCard("t1");
await sleep(0);
check("runFromCard：必填缺失不自动起跑", runCountReq() === 0);
check("runFromCard：仍停在详情页引导填参", S.selectedId.value === "t1");

settleReq();
S.selectedId.value = null;
S.currentArgs.value = [];
argFixtures = [specOf({ default: "fallback" })];
await S.runFromCard("t1");
await sleep(0);
check("runFromCard：有默认值则自动起跑", runCountReq() === 1);

// ===========================================================================
if (failed) {
  console.error(`\n${failed} / ${total} 项断言失败`);
  process.exit(1);
}
console.log(`\n全部通过（${total} 项断言）`);
