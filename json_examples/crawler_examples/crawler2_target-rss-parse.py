"""RSS 解析：标准库解析订阅源结构。"""
import xml.etree.ElementTree as ET

RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel>
  <title>技术博客</title>
  <item><title>爬虫入门</title><pubDate>Mon, 21 Sep 2026</pubDate><link>/p/1</link></item>
  <item><title>办公自动化</title><pubDate>Tue, 22 Sep 2026</pubDate><link>/p/2</link></item>
</channel></rss>"""
root = ET.fromstring(RSS)
print("频道:", root.find("channel/title").text)
for item in root.findall("channel/item"):
    print(f"  {item.find('pubDate').text}  {item.find('title').text}  {item.find('link').text}")
