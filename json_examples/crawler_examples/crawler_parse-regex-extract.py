"""正则提取：抓取结果里的结构化字段。"""
import re

TEXT = """
联系人: alice@example.com / 备用 bob@test.org
电话: 13812345678，传真 010-88889999
截止: 2026-10-01 之前
"""
emails = re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", TEXT)
phones = re.findall(r"1[3-9]\d{9}", TEXT)
dates = re.findall(r"\d{4}-\d{2}-\d{2}", TEXT)
print("邮箱:", emails)
print("手机:", phones)
print("日期:", dates)
