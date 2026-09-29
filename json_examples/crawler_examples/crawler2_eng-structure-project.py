"""项目分层：一个可维护爬虫的最小骨架。"""
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Spider:
    name: str
    start_urls: list
    parser: Callable  # 解析函数注入：结构与逻辑分离
    pipeline: list = field(default_factory=list)  # 存储/清洗管道

    def run(self):
        items = []
        for url in self.start_urls:
            items.extend(self.parser(url))  # 真实场景替换为 HTTP 请求
        for stage in self.pipeline:
            items = [x for x in (stage(it) for it in items) if x is not None]
        return items


def parse(url):
    return [{"source": url, "value": 1}]


def drop_zero(item):
    return item if item["value"] > 0 else None


spider = Spider("demo", ["https://a.com", "https://b.com"], parse, [drop_zero])
print(spider.run())
