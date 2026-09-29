// overview.ts 纯函数单元测试：主题互斥分区 + 标签分区/综合项目 + others 兜底桶 + 质量降序预览
//
// v2 口径：主题判定认服务端下发的 theme_key（列表不含 code，判据在服务端，
// 见 src/themes.ts 与 app/contract_store.py::theme_key）。夹具因此给 theme_key，
// 而不是像 v1 那样塞 code 让前端跑正则。
import { createRendererLoader } from "./renderer-loader.mjs";

const { assignSections, TAG_SECTIONS, tagSectionLabel, PROJECTS_SECTION_META } = createRendererLoader().load("overview");

function ex(id, { theme = null, name = id, tags = [], quality } = {}) {
  return { id, name, category: "topics", path: `x/${id}`, theme_key: theme, tags, quality_score: quality };
}

let failed = 0;
function check(desc, cond) {
  if (!cond) {
    failed++;
    console.error(`  ✗ ${desc}`);
  } else {
    console.log(`  ✓ ${desc}`);
  }
}

console.log("assignSections");

// 1. 结构分区恒在（空库时也保留：5 主题 + 8 标签组 + 综合项目），others 为空则省略
{
  const sections = assignSections([]);
  check(
    "空库返回 5 主题 + 8 标签组 + 综合项目",
    sections.length === 5 + TAG_SECTIONS.length + 1
  );
  check("标签组全部带 tags 与 kind='tags'", sections.filter((s) => s.kind === "tags").every((s) => Array.isArray(s.tags) && s.tags.length > 0));
  check("主题分区 kind='theme'", sections.slice(0, 5).every((s) => s.kind === "theme"));
  check("项目区 kind='projects'", sections.find((s) => s.key === "projects")?.kind === "projects");
  check("others 为空时省略", !sections.some((s) => s.key === "others"));
}

// 2. 互斥分配：一张卡只出现在一个分区（THEMES 顺序 first-match）
{
  const examples = [
    ex("t1", { theme: "turtle" }),
    ex("g1", { theme: "games" }),
    ex("cv1", { theme: "opencv" }),
    ex("pil1", { theme: "images" }),
    ex("viz1", { theme: "viz" }),
    ex("plain1", {}),
  ];
  const sections = assignSections(examples);
  const all = sections.flatMap((s) => s.items.map((e) => e.id));
  check("每张卡恰好出现一次", all.length === examples.length && new Set(all).size === examples.length);
  const byKey = Object.fromEntries(sections.map((s) => [s.key, s.items.map((e) => e.id)]));
  check("turtle 卡进 turtle 分区", byKey.turtle.join() === "t1");
  check("pygame 卡进 games 分区", byKey.games.join() === "g1");
  check("cv2 卡进 opencv 分区", byKey.opencv.join() === "cv1");
  check("PIL 卡进 images 分区", byKey.images.join() === "pil1");
  check("matplotlib 卡进 viz 分区", byKey.viz.join() === "viz1");
  check("无命中卡进 others", byKey.others.join() === "plain1");
}

// 3. 一张卡只会出现在一个分区（theme_key 由服务端 first-match 定死，客户端按 key 归位）
{
  const sections = assignSections([ex("multi", { theme: "turtle" }), ex("g2", { theme: "games" })]);
  const inGames = sections.find((s) => s.key === "games").items.map((e) => e.id);
  const inTurtle = sections.find((s) => s.key === "turtle").items.map((e) => e.id);
  check("按 theme_key 归位且互斥", inTurtle.join() === "multi" && inGames.join() === "g2");
  const unknownKey = assignSections([ex("weird", { theme: "not-a-theme" })]);
  check("未知 theme_key 落 others（不静默吞掉）", unknownKey.find((s) => s.key === "others").items.map((e) => e.id).join() === "weird");
}

// 4. 预览按质量分降序，同分按 id 稳定
{
  const examples = [
    ex("b-low", { theme: "turtle", quality: 50 }),
    ex("a-high", { theme: "turtle", quality: 90 }),
    ex("c-high", { theme: "turtle", quality: 90 }),
  ];
  const items = assignSections(examples).find((s) => s.key === "turtle").items;
  check("质量降序 + 同分按 id", items.map((e) => e.id).join() === "a-high,c-high,b-low");
}

// 5. projects / tools 分类同样参与主题命中（games 谓词排除 projects）；
//    未命中主题的 projects 进综合项目区（先于标签组），tools 命中谓词照常进主题区
{
  const examples = [
    { ...ex("proj1", {}), category: "projects" },
    { ...ex("tool1", { theme: "games" }), category: "tools" },
    { ...ex("proj2", { tags: ["flask"] }), category: "projects" },
  ];
  const sections = assignSections(examples);
  const games = sections.find((s) => s.key === "games");
  const projects = sections.find((s) => s.key === "projects");
  const webapp = sections.find((s) => s.key === "tag:webapp");
  check("projects 未命中主题即进综合项目区", !games.items.some((e) => e.id === "proj1"));
  check("tools 命中主题照常进主题区", games.items.some((e) => e.id === "tool1"));
  check("projects 落入综合项目区（先于标签组）", projects.items.map((e) => e.id).join() === "proj1,proj2");
  check("flask 项目不进 Web 应用区", !webapp.items.some((e) => e.id === "proj2"));
}

// 6. 标签分区：命中组内任一标签即入区；声明顺序即优先级（多组同时命中取先声明者）
{
  const sections = assignSections([
    ex("crawl1", { tags: ["web-crawling"] }),
    ex("net1", { tags: ["网络"] }),
    ex("both1", { tags: ["web-crawling", "python-basics"] }),
    ex("db1", { tags: ["databases"] }),
    ex("plain1", {}),
  ]);
  const byKey = Object.fromEntries(sections.map((s) => [s.key, s.items.map((e) => e.id)]));
  check("web-crawling 进网络爬虫区", byKey["tag:crawling"].includes("crawl1"));
  check("中文标签 网络 同样进网络爬虫区", byKey["tag:crawling"].includes("net1"));
  check("双组命中取声明序靠前者（语言基础 > 网络爬虫）", byKey["tag:basics"].includes("both1") && !byKey["tag:crawling"].includes("both1"));
  check("databases 进数据库区", byKey["tag:database"].includes("db1"));
  check("无标签且未命中主题进 others", byKey.others.includes("plain1"));
  check("空库时 others 分节不出现", !assignSections([]).some((s) => s.key === "others"));
}

// 7. tagSectionLabel：结果条范围标题反查
{
  check("组内标签反查分区名", tagSectionLabel(["web-crawling"]) === "网络爬虫");
  check("大小写不敏感", tagSectionLabel(["Web-Crawling"]) === "网络爬虫");
  check("未知标签返回 undefined", tagSectionLabel(["no-such-tag"]) === undefined);
  check("项目区元数据可导出", PROJECTS_SECTION_META.label === "综合项目");
}

if (failed) {
  console.error(`\n${failed} 项断言失败`);
  process.exit(1);
}
console.log("\n全部通过");
