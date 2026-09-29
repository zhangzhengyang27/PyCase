"""树导航：相邻节点与父子关系。"""
from bs4 import BeautifulSoup

HTML = "<ul><li>A</li><li class='mark'>B</li><li>C</li></ul>"
soup = BeautifulSoup(HTML, "html.parser")
mark = soup.find("li", class_="mark")
print("前一个:", mark.find_previous_sibling("li").text)
print("后一个:", mark.find_next_sibling("li").text)
print("父节点:", mark.parent.name)
print("全部兄弟:", [li.text for li in mark.find_parent("ul").children if li.name])
