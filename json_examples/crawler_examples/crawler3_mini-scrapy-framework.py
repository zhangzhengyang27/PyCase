"""迷你框架：理解 Scrapy 的核心抽象。"""
from collections import deque


class Scheduler:
    def __init__(self):
        self.queue = deque()
        self.seen = set()

    def push(self, url):
        if url not in self.seen:
            self.seen.add(url)
            self.queue.append(url)

    def pop(self):
        return self.queue.popleft() if self.queue else None


def download(url):  # 下载器（真实场景替换为 requests）
    return f"<html of {url}>"


def parse(response):  # 解析器：产出条目与新链接
    return [{"url": response}], []


def pipeline(items):  # 管道：存储
    for it in items:
        print("入库:", it["url"][-10:])


spider = Scheduler()
spider.push("https://a.com")
spider.push("https://b.com")
while (url := spider.pop()):
    items, links = parse(download(url))
    pipeline(items)
    for link in links:
        spider.push(link)
print("框架演示完成")
