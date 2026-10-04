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

# ---- 类型：内存库与游标 ----
mem = sqlite3.connect(":memory:")
mem.execute("CREATE TABLE t (n INTEGER)")
mem.executemany("INSERT INTO t VALUES (?)", [(i,) for i in range(1, 11)])
cur = mem.execute("SELECT n FROM t")
batch = 3
while rows := cur.fetchmany(batch):
    print("一批:", [r[0] for r in rows])
print("聚合:", mem.execute("SELECT SUM(n), AVG(n) FROM t").fetchone())
