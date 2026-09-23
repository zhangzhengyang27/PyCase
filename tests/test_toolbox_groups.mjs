// toolbox-groups.ts 纯函数单元测试：项目分组 + 独立工具兜底 + 稳定排序
import { createRendererLoader } from "./renderer-loader.mjs";

const { buildToolboxGroups, projectKeyOf } = createRendererLoader().load("toolbox-groups");

function tool(id, sourceDir, category = "tools") {
  return { id, name: `${id}.py`, category, path: `x/${id}`, source_dir: sourceDir };
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

console.log("projectKeyOf");

check("tools/<project> → 项目 key", projectKeyOf("tools/utility-crawlers") === "utility-crawlers");
check("嵌套路径取第一段", projectKeyOf("tools/utility-crawlers/spider-collection/boss") === "utility-crawlers");
check("无 source_dir → null", projectKeyOf(undefined) === null && projectKeyOf("") === null);
check("非 tools 前缀 → null", projectKeyOf("projects/foo") === null);
check("单段 tools → null", projectKeyOf("tools") === null);

console.log("buildToolboxGroups");

// 1. 空输入 → 空分组
check("空输入零分组", buildToolboxGroups([]).length === 0);

// 2. 按 source_dir 分组 + 中文标签 + 声明序
{
  const groups = buildToolboxGroups([
    tool("a", "tools/wechat-official-account"),
    tool("b", "tools/db-table-dictionary-generator"),
    tool("c", "tools/db-table-dictionary-generator"),
    tool("d", "tools/utility-crawlers/spider-collection/boss"),
  ]);
  check("分组数正确", groups.length === 3);
  check("内置项目按声明序（db 字典在前）", groups[0].key === "db-table-dictionary-generator");
  check("中文标签生效", groups[0].label === "数据库数据字典生成器" && groups[1].label === "实用爬虫合集");
  check("嵌套路径归入顶层项目", groups[0].items.length === 2 && groups[1].items.map((t) => t.id).join() === "d");
}

// 3. 无 source_dir → 独立工具垫底；用户导入（category=user）同样归入
{
  const groups = buildToolboxGroups([
    tool("s1", undefined),
    tool("u1", undefined, "user"),
    tool("a", "tools/tkinter-work-countdown"),
  ]);
  check("独立工具组存在且垫底", groups.length === 2 && groups[1].key === "standalone");
  check("独立工具收编 user 类目", groups[1].items.map((t) => t.id).join() === "s1,u1");
}

// 4. 全部有分组时不产生独立工具组
check("无散件则无兜底组", buildToolboxGroups([tool("a", "tools/python-black-magic")]).length === 1);

// 5. 未知项目 key 回退原名展示
{
  const groups = buildToolboxGroups([tool("x", "tools/future-project")]);
  check("未知项目回退原 key", groups[0].label === "future-project" && groups[0].icon === "🔧");
}

if (failed) {
  console.error(`\n${failed} 项断言失败`);
  process.exit(1);
}
console.log("\n全部通过");
