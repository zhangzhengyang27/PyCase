"""正文提取：脚本+样式剔除，块级标签换行。"""
from bs4 import BeautifulSoup

HTML = """
<html><head><style>body{color:red}</style><script>var x=1;</script></head>
<body><h1>标题</h1><p>第一段正文。</p><p>第二段，含<a href="#">链接</a>。</p></body></html>"""
soup = BeautifulSoup(HTML, "html.parser")
for tag in soup(["style", "script", "noscript"]):
    tag.decompose()
text = soup.get_text("\n")
lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
print("\n".join(lines))
