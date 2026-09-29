"""名言站点：CSS 选择器 + 分页（教学专用站点，允许抓取）。"""
import requests
from bs4 import BeautifulSoup

url, page, all_quotes = "https://quotes.toscrape.com/", 1, []
while url and page <= 3:
    soup = BeautifulSoup(requests.get(url, timeout=10).text, "html.parser")
    for q in soup.select("div.quote"):
        all_quotes.append({
            "text": q.select_one("span.text").get_text(strip=True),
            "author": q.select_one("small.author").text,
            "tags": [t.text for t in q.select("a.tag")],
        })
    nxt = soup.select_one("li.next > a")
    url = "https://quotes.toscrape.com" + nxt["href"] if nxt else None
    page += 1
for q in all_quotes[:5]:
    print(q["author"], "|", q["text"][:30], "|", q["tags"][:2])
print("合计:", len(all_quotes))
