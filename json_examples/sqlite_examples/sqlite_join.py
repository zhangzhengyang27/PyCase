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

# ---- 类型：两表连接 ----
conn.execute("CREATE TABLE stock_notes (category TEXT PRIMARY KEY, note TEXT)")
conn.executemany("INSERT INTO stock_notes VALUES (?, ?)", [("外设", "热卖"), ("显示", "高客单")])
conn.commit()
kind = "LEFT"
sql = f"""
SELECT g.name, g.category, s.note FROM goods g {kind} JOIN stock_notes s ON g.category = s.category
"""
print(f"{kind} JOIN 结果:")
for r in conn.execute(sql):
    print(" ", r)
print("\nLEFT 保留无备注品类（note=NULL），INNER 会丢弃")
