"""配置类：把散落的抓取参数集中管理。"""
from dataclasses import dataclass, field


@dataclass
class CrawlerConfig:
    base_url: str = "https://httpbin.org"
    max_pages: int = 5
    concurrency: int = 4
    timeout: float = 10.0
    headers: dict = field(default_factory=lambda: {"User-Agent": "demo/1.0"})
    keywords: list = field(default_factory=lambda: ["python", "爬虫"])

    def page_url(self, page: int) -> str:
        return f"{self.base_url}/get?page={page}"


cfg = CrawlerConfig(max_pages=3, keywords=["demo"])
print(cfg)
print(cfg.page_url(2), "| 关键词:", cfg.keywords)
