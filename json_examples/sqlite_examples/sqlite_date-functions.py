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

# ---- 类型：日期函数 ----
conn.execute("CREATE TABLE logs (id INTEGER PRIMARY KEY, event TEXT, ts TEXT)")
conn.executemany(
    "INSERT INTO logs (event, ts) VALUES (?, datetime('now', ?))",
    [("启动", "-3 days"), ("登录", "-1 hours"), ("下单", "-10 minutes"), ("支付", "0 minutes")],
)
conn.commit()
print("最近 1 天的事件:")
for r in conn.execute("SELECT event, ts FROM logs WHERE ts >= datetime('now', '-1 day') ORDER BY ts"):
    print(" ", r)
print("\n按日期分组:")
for r in conn.execute("SELECT date(ts), COUNT(*) FROM logs GROUP BY date(ts)"):
    print(" ", r)
