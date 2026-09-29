"""class 模糊匹配：re.compile + find_all。"""
import re
from bs4 import BeautifulSoup

HTML = """
<div class="post-101 top">帖101</div>
<div class="post-102">帖102</div>
<div class="post-103 hot">帖103</div>"""
soup = BeautifulSoup(HTML, "html.parser")
posts = soup.find_all("div", class_=re.compile(r"^post-\d+$"))
print("帖子数:", len(posts), [p.text for p in posts])
hot = soup.find("div", class_=re.compile("hot"))
print("热帖:", hot.text)
