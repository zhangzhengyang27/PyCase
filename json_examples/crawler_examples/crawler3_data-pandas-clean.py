"""pandas 清洗：抓取数据标准化。"""
import pandas as pd

raw = pd.DataFrame([
    {"name": " 商品A ", "price": "129.00", "stock": 12},
    {"name": None, "price": "89.5", "stock": 3},
    {"name": "商品B", "price": None, "stock": 0},
    {"name": "商品A ", "price": "129.00", "stock": 12},
])
df = raw.assign(name=raw["name"].str.strip(), price=pd.to_numeric(raw["price"], errors="coerce"))
df = df.dropna(subset=["name", "price"]).drop_duplicates(subset=["name"])
df["stock"] = df["stock"].astype(int)
print(df)
print("清洗后:", len(df), "/", len(raw))
