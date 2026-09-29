"""文本日报：数据 → 模板化报告。"""
data = {
    "date": "2026-09-23",
    "new_users": 128,
    "active_users": 1532,
    "revenue": 9820.5,
    "incidents": ["接口超时 2 次", "缓存抖动 1 次"],
}
lines = [
    f"运营日报 {data['date']}",
    "=" * 30,
    f"新增用户: {data['new_users']}",
    f"活跃用户: {data['active_users']}",
    f"营收: ¥{data['revenue']:,.2f}",
    "",
    "异常事件:",
]
lines += [f"  - {x}" for x in data["incidents"]]
report = "\n".join(lines)
print(report)
with open("日报.txt", "w", encoding="utf-8") as f:
    f.write(report)
