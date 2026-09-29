"""日期计算：{{d1}} 与 {{d2}} 之间隔多少天。"""
from datetime import date

d1 = date(2023, 12, 31)
d2 = date(2026, 1, 1)
diff = abs((d2 - d1).days)
print(f"间隔 {{diff}} 天（约 {{diff / 7:.1f}} 周）")
print("各自星期:", d1.strftime("%A"), "/", d2.strftime("%A"))
