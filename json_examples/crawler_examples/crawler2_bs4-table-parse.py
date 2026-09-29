"""表格解析：table → list[dict]。"""
from bs4 import BeautifulSoup

HTML = """
<table id="score">
  <tr><th>姓名</th><th>语文</th><th>数学</th></tr>
  <tr><td>小明</td><td>92</td><td>88</td></tr>
  <tr><td>小红</td><td>95</td><td>91</td></tr>
</table>"""
soup = BeautifulSoup(HTML, "html.parser")
headers = [th.text for th in soup.select("#score th")]
rows = []
for tr in soup.select("#score tr")[1:]:
    cells = [td.text for td in tr.select("td")]
    rows.append(dict(zip(headers, cells)))
print(rows)
