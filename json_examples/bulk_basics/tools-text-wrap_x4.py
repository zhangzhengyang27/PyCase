"""文本折行：宽度 44 列。"""
text = "'the quick brown fox jumps over the lazy dog and python makes text processing delightfully simple for everyone'"
width = 44
lines, cur = [], ""
for word in text.split():
    if len(cur) + len(word) + 1 > width and cur:
        lines.append(cur)
        cur = word
    else:
        cur = (cur + " " + word).strip()
if cur:
    lines.append(cur)
for ln in lines:
    print(ln)
print(f"共 {{len(lines)}} 行")
