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

# ---- 类型：参数化插入与查询 ----
conn.execute("INSERT INTO goods VALUES (?, ?, ?, ?, ?)", (6, "摄像头", "外设", 399.0, 8))
conn.commit()
gid = 3
row = conn.execute("SELECT name, price FROM goods WHERE id = ?", (gid,)).fetchone()
print("按 id 查询:", row)
print("全部商品:")
for r in conn.execute("SELECT id, name, price FROM goods ORDER BY id"):
    print(" ", r)
print("总数:", conn.execute("SELECT COUNT(*) FROM goods").fetchone()[0])
