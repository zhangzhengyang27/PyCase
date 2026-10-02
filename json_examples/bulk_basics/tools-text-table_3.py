"""文本表格：5 行对齐输出。"""
headers = ["名称", "数量", "单价"]
data = [['小明', 92, 1], ['小红', 88, 2], ['小刚', 95, 1], ['小丽', 79, 3], ['小军', 85, 2]]
widths = [max(len(str(headers[i])), max(len(str(r[i])) for r in data)) for i in range(3)]
line = "| " + " | ".join(h.ljust(w) for h, w in zip(headers, widths)) + " |"
print(line)
print("|" + "|".join("-" * (w + 2) for w in widths) + "|")
for r in data:
    print("| " + " | ".join(str(c).ljust(w) for c, w in zip(r, widths)) + " |")
