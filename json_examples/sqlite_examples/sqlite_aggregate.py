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

# ---- 类型：分组聚合 ----
floor = 1000
sql = """
SELECT category, COUNT(*) AS cnt, ROUND(SUM(price * stock), 1) AS total
FROM goods GROUP BY category HAVING SUM(price * stock) > ? ORDER BY total DESC
"""
print(f"HAVING 库存总值 > {floor}:")
for r in conn.execute(sql, (floor,)):
    print(" ", r)
print("\n全局极值:")
print(conn.execute("SELECT MAX(price), MIN(price), ROUND(AVG(price),1) FROM goods").fetchone())
