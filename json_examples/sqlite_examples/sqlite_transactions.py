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

# ---- 类型：事务与回滚 ----
try:
    conn.execute("UPDATE goods SET stock = stock - 2 WHERE id = 1")
    conn.execute("UPDATE goods SET stock = stock + 2 WHERE id = 2")
    conn.execute("UPDATE goods SET stock = 库存 WHERE id = 3")  # 故意写错列名
    conn.commit()
except sqlite3.OperationalError as e:
    conn.rollback()
    print("出错回滚:", e)
after = conn.execute("SELECT id, stock FROM goods WHERE id IN (1, 2)").fetchall()
print("回滚后库存（1/2 号应保持 12/30）:", after)
conn.execute("UPDATE goods SET stock = stock - 2 WHERE id = 1")
conn.execute("UPDATE goods SET stock = stock + 2 WHERE id = 2")
conn.commit()
print("正常提交后:", conn.execute("SELECT id, stock FROM goods WHERE id IN (1, 2)").fetchall())
