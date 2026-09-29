"""SQLite → Excel：查询结果报表化。"""
import sqlite3
from openpyxl import Workbook

conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE sales (dept TEXT, month TEXT, amount REAL)")
conn.executemany("INSERT INTO sales VALUES (?, ?, ?)",
                 [("研发", "1月", 120), ("研发", "2月", 135), ("市场", "1月", 90)])
conn.commit()

wb = Workbook()
ws = wb.active
cols = [d[0] for d in conn.execute("SELECT * FROM sales LIMIT 0").description]
ws.append(cols)
for row in conn.execute("SELECT * FROM sales ORDER BY amount DESC"):
    ws.append(row)
wb.save("数据库报表.xlsx")
print("数据库查询已导出为 数据库报表.xlsx")
