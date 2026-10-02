"""文本表格：3 行对齐输出。"""
headers = ["名称", "数量", "单价"]
data = [['螺丝', 400, 0.2], ['螺母', 350, 0.3], ['垫片', 500, 0.1]]
widths = [max(len(str(headers[i])), max(len(str(r[i])) for r in data)) for i in range(3)]
line = "| " + " | ".join(h.ljust(w) for h, w in zip(headers, widths)) + " |"
print(line)
print("|" + "|".join("-" * (w + 2) for w in widths) + "|")
for r in data:
    print("| " + " | ".join(str(c).ljust(w) for c, w in zip(r, widths)) + " |")
