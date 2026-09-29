"""数据清洗：抓取结果的标准化流水线。"""
raw = [
    {"name": " 商品A ", "price": "129.00", "stock": "12"},
    {"name": "", "price": "89.5", "stock": "3"},
    {"name": "商品B", "price": "暂无", "stock": "0"},
    {"name": "商品C", "price": " 259 ", "stock": "7"},
]
clean = []
for r in raw:
    name = (r.get("name") or "").strip()
    try:
        price = float(r["price"])
        stock = int(r["stock"])
    except ValueError:
        continue  # 坏数据丢弃并记录（生产中打日志）
    if not name or price <= 0:
        continue
    clean.append({"name": name, "price": price, "stock": stock})
print(clean)
