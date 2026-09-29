"""find/find_all：属性定位与文本提取。"""
from bs4 import BeautifulSoup

HTML = '<div class="price"><em>￥</em>129.00<del>￥199.00</del></div>'
soup = BeautifulSoup(HTML, "html.parser")
box = soup.find("div", class_="price")
price = box.find(text=True, recursive=False).strip()
old = box.find("del").get_text(strip=True)
print("现价:", price, "| 原价:", old, "| 类型:", type(price).__name__)
