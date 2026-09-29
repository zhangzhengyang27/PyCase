"""Markdown 待办：生成与统计。"""
from pathlib import Path

tasks = [("已完成", "恢复示例库"), ("已完成", "修复构建链路"),
         ("进行中", "扩充示例规模"), ("待办", "补拍 README 截图")]
lines = ["# 待办清单", ""]
for status, task in tasks:
    mark = {"已完成": "x", "进行中": " ", "待办": " "}[status]
    lines.append(f"- [{mark}] {task}（{status}）")
Path("TODO.md").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
done = sum(1 for s, _ in tasks if s == "已完成")
print(f"完成度: {done}/{len(tasks)}")
