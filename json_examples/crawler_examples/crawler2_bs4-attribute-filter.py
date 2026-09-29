"""属性过滤：外部链接与自定义属性。"""
from bs4 import BeautifulSoup

HTML = """
<nav>
  <a href="/internal/1">站内</a>
  <a href="https://out.com/x" rel="nofollow">站外</a>
  <a class="btn primary large" data-track="cta">立即注册</a>
</nav>"""
soup = BeautifulSoup(HTML, "html.parser")
external = [a["href"] for a in soup.find_all("a", href=lambda h: h and h.startswith("https://"))]
cta = soup.find("a", attrs={"data-track": "cta"})
multi = soup.find("a", class_=["primary", "large"])
print("外链:", external)
print("CTA:", cta.text, "| 多class:", multi.text)
