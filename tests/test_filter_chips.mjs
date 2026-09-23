// filter-chips.ts 纯函数单元测试：芯片生成 + 标签映射
import { createRendererLoader } from "./renderer-loader.mjs";

const { buildFilterChips, RUN_STATUS_LABELS, RUNNABLE_LABELS } = createRendererLoader().load("filter-chips");

let failed = 0;
function check(desc, cond) {
  if (!cond) {
    failed++;
    console.error(`  ✗ ${desc}`);
  } else {
    console.log(`  ✓ ${desc}`);
  }
}
function labels(chips) {
  return chips.map((c) => c.label);
}

console.log("buildFilterChips");

// 1. 空查询 → 无芯片
{
  const chips = buildFilterChips({});
  check("空查询零芯片", chips.length === 0);
  const allDefaults = buildFilterChips({ favOnly: false, runStatus: "all", runnable: "all", theme: "all", minQuality: 0, tags: [], q: "" });
  check("全默认值零芯片", allDefaults.length === 0);
}

// 2. 单维度芯片
{
  const chips = buildFilterChips({ favOnly: true });
  check("favOnly → 我的收藏", labels(chips).join() === "我的收藏");
  const chips2 = buildFilterChips({ runStatus: "failed" });
  check("runStatus → 失败过", labels(chips2).join() === "失败过");
  const chips3 = buildFilterChips({ runnable: "missing_deps" });
  check("runnable → 缺依赖", labels(chips3).join() === "缺依赖");
  const chips4 = buildFilterChips({ theme: "turtle" });
  check("theme → 主题 label", labels(chips4).join() === "Turtle 绘图");
  const chips5 = buildFilterChips({ minQuality: 80 });
  check("minQuality → 质量分 ≥80", labels(chips5).join() === "质量分 ≥80");
  const chips6 = buildFilterChips({ q: "  tic tac  " });
  check("搜索词 trim 后进芯片", labels(chips6).join() === "搜索：tic tac");
}

// 3. 多标签 → 多芯片且保序
{
  const chips = buildFilterChips({ tags: ["pygame", "opencv"] });
  check("标签逐个成芯片", labels(chips).join() === "#pygame,#opencv");
  check("tag 芯片 value = 标签名", chips.every((c) => c.key === "tag" && c.value));
}

// 4. 组合查询 → 顺序稳定（fav → runStatus → runnable → theme → quality → tags → q）
{
  const chips = buildFilterChips({
    favOnly: true,
    runStatus: "ok",
    runnable: "risky",
    theme: "viz",
    minQuality: 90,
    tags: ["numpy"],
    q: "plot"
  });
  check(
    "组合查询芯片齐全且有序",
    labels(chips).join() === "我的收藏,成功过,高危,数据可视化,质量分 ≥90,#numpy,搜索：plot"
  );
  const keys = new Set(chips.map((c) => c.key));
  check("移除芯片可按 key+value 定位", keys.size === chips.length && chips[4].value === "90");
}

// 5. 未知 key 回退原始值（脏数据不崩）
{
  const chips = buildFilterChips({ runStatus: "weird", runnable: "weird", theme: "weird" });
  check("未知状态回退原值", labels(chips).join() === "weird,weird,weird");
}

// 6. 标签映射完整性（与侧栏 facet 一致）
check("RUN_STATUS_LABELS 3 项", Object.keys(RUN_STATUS_LABELS).sort().join() === "failed,never,ok");
check("RUNNABLE_LABELS 5 项", Object.keys(RUNNABLE_LABELS).sort().join() === "broken,empty,missing_deps,risky,runnable");

if (failed) {
  console.error(`\n${failed} 项断言失败`);
  process.exit(1);
}
console.log("\n全部通过");
