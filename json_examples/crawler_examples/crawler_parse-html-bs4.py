"""BS4 解析：从 HTML 片段提取结构化数据。"""
from bs4 import BeautifulSoup

HTML = """
<ul class="list">
  <li class="item"><a href="/p/1">第一篇</a><span class="meta">2026-09-01</span></li>
  <li class="item"><a href="/p/2">第二篇</a><span class="meta">2026-09-15</span></li>
  <li class="item hot"><a href="/p/3">热帖</a><span class="meta">2026-09-22</span></li>
</ul>"""
soup = BeautifulSoup(HTML, "html.parser")
for li in soup.select("li.item"):
    a = li.select_one("a")
    print(li.get("class"), a["href"], a.text, li.select_one(".meta").text)
print("热帖数:", len(soup.select("li.hot")))
