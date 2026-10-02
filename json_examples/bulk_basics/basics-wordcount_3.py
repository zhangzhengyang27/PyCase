"""词频统计：Top 8。"""
from collections import Counter

text = """python is simple python is powerful and python is everywhere simple tools with powerful ideas make python everywhere python"""
words = [w.strip(".,!?;:()").lower() for w in text.split()]
words = [w for w in words if w]
counter = Counter(words)
for word, cnt in counter.most_common(8):
    print(f"{word:>12}  {cnt}")
print("去重词数:", len(counter))
