"""（SQLite 实验室生成脚本：stdlib sqlite3，离线可跑，临时库自动清理）"""
import atexit
import os
import shutil
import sqlite3
import tempfile

workdir = tempfile.mkdtemp(prefix="sqlite-lab-")
atexit.register(shutil.rmtree, workdir, ignore_errors=True)
DB_PATH = os.path.join(workdir, "demo.db")
conn = sqlite3.connect(DB_PATH)
conn.execute(
    "CREATE TABLE goods (id INTEGER PRIMARY KEY, name TEXT NOT NULL, category TEXT, price REAL, stock INTEGER DEFAULT 0)"
)
SEED = [
    (1, "机械键盘", "外设", 329.0, 12),
    (2, "无线鼠标", "外设", 149.0, 30),
    (3, "显示器", "显示", 1299.0, 6),
    (4, "USB-C 扩展坞", "配件", 259.0, 18),
    (5, "笔记本支架", "配件", 89.0, 25),
]
conn.executemany("INSERT INTO goods VALUES (?, ?, ?, ?, ?)", SEED)
conn.commit()

# ---- 类型：CSV 批量导入导出 ----
import csv
import io

CSV_TEXT = "name,category,price,stock\n桌面音箱,外设,269,9\n网线,配件,19,100\n"
reader = csv.DictReader(io.StringIO(CSV_TEXT))
rows = [(r["name"], r["category"], float(r["price"]), int(r["stock"])) for r in reader]
conn.executemany("INSERT INTO goods (name, category, price, stock) VALUES (?, ?, ?, ?)", rows)
conn.commit()
out = io.StringIO()
w = csv.writer(out)
w.writerow(["name", "price"])
for r in conn.execute("SELECT name, price FROM goods WHERE category = '配件'"):
    w.writerow(r)
print("配件导出 CSV:")
print(out.getvalue().strip())
print("库内总行数:", conn.execute("SELECT COUNT(*) FROM goods").fetchone()[0])
