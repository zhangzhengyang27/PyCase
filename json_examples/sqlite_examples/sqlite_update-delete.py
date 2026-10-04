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

# ---- 类型：更新与删除 ----
d = 0.8
cur = conn.execute("UPDATE goods SET price = ROUND(price * ?, 1) WHERE category = '外设'", (d,))
print(f"外设打折 ×{d}，影响 {cur.rowcount} 行")
conn.commit()
cur2 = conn.execute("DELETE FROM goods WHERE stock < ?", (10,))
print(f"删除库存<10：{cur2.rowcount} 行")
conn.commit()
print("剩余:")
for r in conn.execute("SELECT id, name, price, stock FROM goods"):
    print(" ", r)
