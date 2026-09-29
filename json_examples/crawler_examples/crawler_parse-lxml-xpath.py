"""lxml XPath：大页面解析的首选（速度优于 bs4）。"""
from lxml import html

DOC = html.fromstring("""
<div id="main">
  <h2>商品列表</h2>
  <a class="buy" data-id="1" href="/buy/1">苹果</a>
  <a class="buy" data-id="2" href="/buy/2">香蕉</a>
  <span class="sold-out">售罄</span>
</div>""")
print("标题:", DOC.xpath("//h2/text()"))
print("链接:", DOC.xpath("//a[@class='buy']/@href"))
print("含'果'的:", DOC.xpath("//a[contains(text(), '果')]/text()"))
print("data-id:", DOC.xpath("//a/@data-id"))
