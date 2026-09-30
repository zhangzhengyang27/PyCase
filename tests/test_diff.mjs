// diff.ts 纯函数单元测试：行级差异（编辑历史对比用）
import { createRendererLoader } from "./renderer-loader.mjs";

const { diffLines, diffStats } = createRendererLoader().load("src/diff");

let failed = 0;
function check(desc, cond) {
  if (!cond) {
    failed++;
    console.error(`  ✗ ${desc}`);
  } else {
    console.log(`  ✓ ${desc}`);
  }
}

console.log("diffLines");

{
  const same = diffLines("a\nb", "a\nb");
  check("完全一致 → 全 same", same.length === 2 && same.every((l) => l.kind === "same"));
}

{
  const d = diffLines("a\nb\nc", "a\nx\nc");
  check("单行替换 → 一 del 一 add", d.map((l) => l.kind).join() === "same,del,add,same");
  check("行号正确（del 无右号、add 无左号）", d[1].left === 2 && d[1].right === null && d[2].left === null && d[2].right === 2);
}

{
  const d = diffLines("a\nb\nc", "a\nb\nc\nd");
  check("尾部追加 → 只有 add", d.filter((l) => l.kind === "add").length === 1 && d.at(-1).text === "d");
  check("插入一行不会让后续行全变（LCS 对齐）", d.filter((l) => l.kind === "del").length === 0);
}

{
  const d = diffLines("a\nb\nc", "a\nc");
  check("中间删除一行 → 只有 del", d.map((l) => l.kind).join() === "same,del,same");
}

{
  const d = diffLines("", "x");
  check("空 → 单行：一 add（空串与单行语义分明）", d.length === 1 && d[0].kind === "add" && d[0].text === "x");
}

{
  const stats = diffStats(diffLines("a\nb\nc", "a\nx\nc\nd"));
  check("统计：1 增 1 删 + 1 增", stats.added === 2 && stats.removed === 1);
}

{
  const big = Array.from({ length: 300 }, (_, i) => `line${i}`).join("\n");
  const d = diffLines(big, big + "\nextra");
  check("300 行规模仍只有 1 处新增", d.filter((l) => l.kind !== "same").length === 1);
}

if (failed) {
  console.error(`\n${failed} 项断言失败`);
  process.exit(1);
}
console.log("\n全部通过");
