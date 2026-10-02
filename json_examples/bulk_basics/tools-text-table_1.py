"""文本表格：4 行对齐输出。"""
headers = ["名称", "数量", "单价"]
data = [['苹果', 12, 5.5], ['香蕉', 30, 3.2], ['橙子', 8, 6.0], ['葡萄', 15, 9.9]]
widths = [max(len(str(headers[i])), max(len(str(r[i])) for r in data)) for i in range(3)]
line = "| " + " | ".join(h.ljust(w) for h, w in zip(headers, widths)) + " |"
print(line)
print("|" + "|".join("-" * (w + 2) for w in widths) + "|")
for r in data:
    print("| " + " | ".join(str(c).ljust(w) for c, w in zip(r, widths)) + " |")
