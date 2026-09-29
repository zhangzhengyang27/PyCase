"""解析函数单测：离线样本测试（pytest 风格）。"""
from bs4 import BeautifulSoup

def parse_items(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    return [{"title": q.select_one("h3").text,
             "link": q.select_one("a")["href"]} for q in soup.select("div.item")]

SAMPLE = """<div class="item"><h3>标题一</h3><a href="/1"></a></div>
<div class="item"><h3>标题二</h3><a href="/2"></a></div>"""

def test_parse_items():
    got = parse_items(SAMPLE)
    assert len(got) == 2
    assert got[0] == {"title": "标题一", "link": "/1"}

test_parse_items()
print("解析单测通过（离线，无网络）")
