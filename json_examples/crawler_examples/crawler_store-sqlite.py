"""SQLite 存储：抓取数据结构化入库。"""
import sqlite3

conn = sqlite3.connect("crawl.db")
conn.execute("""CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY, title TEXT, price REAL, crawled_at TEXT)""")
conn.executemany("INSERT OR REPLACE INTO items VALUES (?, ?, ?, ?)", [
    (1, "商品A", 129.0, "2026-09-23"),
    (2, "商品B", 89.5, "2026-09-23"),
])
conn.commit()
for row in conn.execute("SELECT id, title, price FROM items ORDER BY price DESC"):
    print(row)
conn.close()
