"""Atom feed：命名空间写法。"""
import xml.etree.ElementTree as ET

ATOM = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry><title>条目一</title><id>urn:1</id></entry>
  <entry><title>条目二</title><id>urn:2</id></entry>
</feed>"""
ns = {"a": "http://www.w3.org/2005/Atom"}
root = ET.fromstring(ATOM)
for entry in root.findall("a:entry", ns):
    print(entry.find("a:title", ns).text, "|", entry.find("a:id", ns).text)
