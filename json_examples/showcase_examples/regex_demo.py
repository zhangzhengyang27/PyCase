"""正则表达式：提取、分组与替换。"""
import re

text = """
联系人: alice@example.com, 备用: bob.smith@mail.org
会议时间: 2026-09-22 14:30 ~ 2026-09-23 09:00
订单号: ORD-2026-0922-001, 金额: ￥1,299.00
"""

# 邮箱提取
emails = re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
print("邮箱:", emails)

# 命名分组解析日期
for m in re.finditer(r"(?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})", text):
    print("日期:", m.groupdict())

# 分组替换：订单号脱敏
masked = re.sub(r"(ORD-\d{4})-\d{4}-(\d+)", r"\1-****-\2", text)
print("脱敏:", masked.strip().splitlines()[-1])

# 贪婪 vs 非贪婪
print("贪婪:", re.findall(r"时间: .*?\d", text)[0][:20])
