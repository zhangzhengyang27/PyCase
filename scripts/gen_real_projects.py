#!/usr/bin/env python3
"""真实项目示例生成器：爬虫实战 + 办公自动化。

与 gen_bulk_examples.py 的参数化变体不同，本目录每条都是一段完整的业务代码
（真实请求链路 / 真实文档操作），面向「拿去改改就能用」的场景。
爬虫示例默认指向稳定端点（httpbin / jsonplaceholder / github api 等）或按
原库惯例给出 B 站、豆瓣等站点的标准抓取模式；全部带超时、异常处理与优雅退出。
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "json_examples"


def slug(text: str) -> str:
    import re
    return re.sub(r"[^0-9A-Za-z_.-]+", "-", text).strip("-").lower()


class Collection:
    def __init__(self, file: str, name: str, description: str, merge: bool = False):
        self.file = file
        self.name = name
        self.description = description
        self.examples = []
        self.seen_code = set()
        self.seen_id = set()
        existing = OUT_DIR / file
        if merge and existing.exists():
            for e in json.load(open(existing, encoding="utf-8")).get("examples", []):
                self.seen_id.add(e["id"])
                self.seen_code.add(hashlib.md5(e["code"].encode()).hexdigest())
                self.examples.append(e)

    def add(self, example_id: str, name: str, title: str, description: str,
            tags: list, requirements: list, code: str, category: str = "topics"):
        code = code.strip() + "\n"
        h = hashlib.md5(code.encode()).hexdigest()
        if h in self.seen_code:
            return False
        if example_id in self.seen_id:  # 同 id 重跑：更新内容（upsert）
            for i, e in enumerate(self.examples):
                if e["id"] == example_id:
                    self.examples[i] = {"id": example_id, "name": name, "category": category,
                                        "tags": tags, "title": title, "description": description,
                                        "requirements": requirements, "code": code}
                    return True
        self.seen_code.add(h)
        self.seen_id.add(example_id)
        self.examples.append({
            "id": example_id, "name": name, "category": category,
            "tags": tags, "title": title, "description": description,
            "requirements": requirements, "code": code,
        })
        return True

    def save(self) -> int:
        out = OUT_DIR / self.file
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"name": self.name, "description": self.description,
                       "examples": self.examples}, f, ensure_ascii=False, indent=1)
        return len(self.examples)


def build_crawler():
    c = Collection("crawler_examples.json", "爬虫实战",
                   "真实请求链路的爬虫示例：请求构造、解析、并发、限速、存储、反爬应对全流程。"
                   "演示目标以 httpbin / jsonplaceholder / github api 等稳定端点为主，B 站/豆瓣为标准抓取模式。")

    def add(pid, title, desc, code, tags=("爬虫",), reqs=("requests",), category="topics"):
        c.add(f"{category}_crawler-{pid}", f"crawler_{pid}.py", title, desc,
              list(tags), list(reqs), code, category)

    # ---- HTTP 基础与请求构造 ----
    add("http-get-basic", "GET 请求与响应解读", "requests 最小可用抓取：状态码、头、编码、JSON 反序列化。",
        '''"""GET 请求基础：httpbin 回显服务演示响应各部分。"""
import requests

resp = requests.get("https://httpbin.org/get", params={"q": "python", "page": 1}, timeout=10)
print("状态码:", resp.status_code)
print("响应头 Content-Type:", resp.headers.get("Content-Type"))
print("编码:", resp.encoding)
data = resp.json()  # httpbin 返回 JSON
print("服务端看到的查询参数:", data["args"])
print("请求 UA:", data["headers"].get("User-Agent", "<未知>")[:40], "...")
''')
    add("http-headers-ua", "请求头与 UA 伪装", "构造浏览器级请求头绕过基础 UA 检测（标准反爬第一课）。",
        '''"""请求头构造：模拟 Chrome 浏览器发起请求。"""
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

resp = requests.get("https://httpbin.org/user-agent", headers=HEADERS, timeout=10)
print("服务端收到的 UA:", resp.json()["user-agent"])
print("状态码:", resp.status_code)
''')
    add("http-timeout-retry", "超时与重试退避", "连接/读取超时分离 + 指数退避重试（生产必备）。",
        '''"""超时与重试：指数退避，最多 4 次。"""
import time
import requests

URL = "https://httpbin.org/status/200,503"
for attempt in range(1, 5):
    try:
        resp = requests.get(URL, timeout=(3.05, 10))  # (连接, 读取)
        if resp.status_code == 200:
            print(f"第 {attempt} 次成功")
            break
        print(f"第 {attempt} 次状态码 {resp.status_code}")
    except requests.RequestException as e:
        print(f"第 {attempt} 次异常: {type(e).__name__}")
    time.sleep(2 ** attempt)  # 1, 2, 4 秒退避
else:
    print("重试耗尽，放弃")
''')
    add("http-session-cookies", "会话与 Cookie", "requests.Session 保持登录态，Cookie 自动回传。",
        '''"""Session 会话：Cookie 在多次请求间自动保持。"""
import requests

with requests.Session() as s:
    s.headers["User-Agent"] = "Mozilla/5.0 (learning-demo)"
    s.get("https://httpbin.org/cookies/set/token/abc123", timeout=10)  # 服务端 Set-Cookie
    data = s.get("https://httpbin.org/cookies", timeout=10).json()
    print("会话内 Cookie:", data["cookies"])  # token 自动回传
''')
    add("http-post-form", "POST 表单提交", "表单字段与 JSON 体两种提交方式。",
        '''"""POST 提交：表单 vs JSON。"""
import requests

form = requests.post("https://httpbin.org/post", data={"user": "demo", "page": 2}, timeout=10)
print("表单字段:", form.json()["form"])

payload = {"items": [1, 2, 3], "verbose": True}
js = requests.post("https://httpbin.org/post", json=payload, timeout=10)
print("JSON 体:", js.json()["json"])
''')
    add("http-status-handle", "状态码分类处理", "2xx/3xx/4xx/5xx 的分支处理与 raise_for_status。",
        '''"""状态码分类：生产级响应处理骨架。"""
import requests

for code in (200, 301, 404, 500):
    resp = requests.get(f"https://httpbin.org/status/{code}", timeout=10, allow_redirects=False)
    kind = ("成功" if resp.status_code < 300
            else "重定向" if resp.status_code < 400
            else "客户端错误" if resp.status_code < 500 else "服务端错误")
    print(f"{code} -> {kind}")
try:
    requests.get("https://httpbin.org/status/404", timeout=10).raise_for_status()
except requests.HTTPError as e:
    print("raise_for_status:", e)
''')
    add("http-stream-download", "流式下载大文件", "chunked 流式写入，内存占用恒定。",
        '''"""流式下载：逐块写入，适合大文件。"""
import requests

url = "https://httpbin.org/bytes/3000"
dest = "download_demo.bin"
with requests.get(url, stream=True, timeout=15) as resp:
    resp.raise_for_status()
    total = 0
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024):
            f.write(chunk)
            total += len(chunk)
print(f"已下载 {total} 字节 -> {dest}")
''')
    add("http-proxy", "代理配置", "http/https 代理设置（内网抓取与 IP 轮换的基础）。",
        '''"""代理：企业内网/爬虫池的接入口径。"""
import requests

proxies = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
}
try:
    resp = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=5)
    print("出口 IP:", resp.json())
except requests.RequestException as e:
    print("代理不可达（本机未开 7890 端口属正常）:", type(e).__name__)
''')

    # ---- 解析 ----
    add("parse-json-api", "JSON API 解析", "嵌套 JSON 的字段提取、容错与列表推导。",
        '''"""JSON API 解析：jsonplaceholder 典型列表接口。"""
import requests

resp = requests.get("https://jsonplaceholder.typicode.com/users", timeout=10)
users = resp.json()
for u in users[:5]:
    print(f"{u['id']:>2} {u['name']:<22} {u['email']:<28} {u['address']['city']}")
print("共", len(users), "个用户；第一个公司:", users[0]["company"]["name"])
''')
    add("parse-html-bs4", "BeautifulSoup 解析", "CSS 选择器提取标题/链接/属性。",
        '''"""BS4 解析：从 HTML 片段提取结构化数据。"""
from bs4 import BeautifulSoup

HTML = """
<ul class="list">
  <li class="item"><a href="/p/1">第一篇</a><span class="meta">2026-09-01</span></li>
  <li class="item"><a href="/p/2">第二篇</a><span class="meta">2026-09-15</span></li>
  <li class="item hot"><a href="/p/3">热帖</a><span class="meta">2026-09-22</span></li>
</ul>"""
soup = BeautifulSoup(HTML, "html.parser")
for li in soup.select("li.item"):
    a = li.select_one("a")
    print(li.get("class"), a["href"], a.text, li.select_one(".meta").text)
print("热帖数:", len(soup.select("li.hot")))
''', reqs=("requests", "beautifulsoup4"))
    add("parse-html-find", "find/find_all 链式定位", "按属性与文本定位节点，get_text 清洗。",
        '''"""find/find_all：属性定位与文本提取。"""
from bs4 import BeautifulSoup

HTML = '<div class="price"><em>￥</em>129.00<del>￥199.00</del></div>'
soup = BeautifulSoup(HTML, "html.parser")
box = soup.find("div", class_="price")
price = box.find(text=True, recursive=False).strip()
old = box.find("del").get_text(strip=True)
print("现价:", price, "| 原价:", old, "| 类型:", type(price).__name__)
''', reqs=("requests", "beautifulsoup4"))
    add("parse-regex-extract", "正则批量提取", "从非结构化文本中提取邮箱/手机号/日期。",
        '''"""正则提取：抓取结果里的结构化字段。"""
import re

TEXT = """
联系人: alice@example.com / 备用 bob@test.org
电话: 13812345678，传真 010-88889999
截止: 2026-10-01 之前
"""
emails = re.findall(r"[\\w.+-]+@[\\w-]+\\.[\\w.]+", TEXT)
phones = re.findall(r"1[3-9]\\d{9}", TEXT)
dates = re.findall(r"\\d{4}-\\d{2}-\\d{2}", TEXT)
print("邮箱:", emails)
print("手机:", phones)
print("日期:", dates)
''')
    add("parse-lxml-xpath", "lxml XPath", "XPath 轴定位：属性、包含文本、层级跳跃。",
        '''"""lxml XPath：大页面解析的首选（速度优于 bs4）。"""
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
''', reqs=("requests", "lxml"))
    add("parse-jsonpath-nested", "深层嵌套容错", "dict.get 链式安全取值，避免 KeyError 打断抓取。",
        '''"""深层嵌套容错：生产爬虫的安全取值习惯。"""
import requests

resp = requests.get("https://jsonplaceholder.typicode.com/users/1", timeout=10)
u = resp.json()
# 链式 get + or 默认值：任何一层缺失都不会抛异常
city = (u.get("address") or {}).get("city") or "未知"
geo = (u.get("address") or {}).get("geo") or {}
lat = geo.get("lat") or "-"
print(f"{u.get('name')} @ {city}（lat={lat}）")
print("不存在字段:", (u.get("profile") or {}).get("wechat") or "<无>")
''')

    # ---- 抓取模式 ----
    add("crawl-paginate", "分页抓取", "page 递增直到空页/达到上限，带礼貌延时。",
        '''"""分页抓取：jsonplaceholder 分页模式。"""
import time
import requests

BASE = "https://jsonplaceholder.typicode.com/posts"
all_items, page, max_page = [], 1, 5
while page <= max_page:
    resp = requests.get(BASE, params={"_page": page, "_limit": 20}, timeout=10)
    items = resp.json()
    if not items:
        print(f"第 {page} 页为空，停止")
        break
    all_items.extend(items)
    print(f"第 {page} 页 +{len(items)}")
    page += 1
    time.sleep(0.3)  # 礼貌延时
print("合计抓取:", len(all_items))
''')
    add("crawl-rate-limit", "限速器", "令牌桶式限速，控制 QPS 不触发封禁。",
        '''"""限速器：装饰器实现最小间隔。"""
import functools
import time

def rate_limit(min_interval):
    last = [0.0]
    def deco(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            wait = min_interval - (time.monotonic() - last[0])
            if wait > 0:
                time.sleep(wait)
            last[0] = time.monotonic()
            return func(*args, **kwargs)
        return wrapper
    return deco

@rate_limit(0.5)
def fetch(url):
    print("fetch", url, "@", time.strftime("%H:%M:%S"))
    return url

for i in range(4):
    fetch(f"https://example.com/item/{i}")
''')
    add("crawl-thread-pool", "线程池并发抓取", "ThreadPoolExecutor + as_completed 并发下载。",
        '''"""并发抓取：线程池 + as_completed 收集结果。"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

urls = [f"https://httpbin.org/delay/1/{i}" for i in range(5)]

def fetch(url):
    resp = requests.get(url, timeout=15)
    return url, resp.status_code

with ThreadPoolExecutor(max_workers=5) as pool:
    futures = [pool.submit(fetch, u) for u in urls]
    for fut in as_completed(futures):
        url, code = fut.result()
        print(f"{code} {url[-14:]}")
''')
    add("crawl-async-aiohttp", "asyncio 异步抓取", "aiohttp + asyncio.gather 高并发异步请求。",
        '''"""异步抓取：aiohttp 协程并发（asyncio 入门实战）。"""
import asyncio

import aiohttp

async def fetch(session, url):
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
        return url, resp.status

async def main():
    urls = [f"https://httpbin.org/get?i={i}" for i in range(6)]
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*(fetch(session, u) for u in urls))
    for url, code in results:
        print(code, url[-12:])

asyncio.run(main())
''', reqs=("requests", "aiohttp"))


    add("crawl-incremental", "增量抓取指纹", "内容哈希指纹跳过未更新条目（增量爬虫核心）。",
        '''"""增量抓取：内容指纹去重，只处理新条目。"""
import hashlib
import json
from pathlib import Path

STATE = Path("crawl_state.json")
seen = json.loads(STATE.read_text()) if STATE.exists() else {}

feed = [{"id": i, "title": f"文章{i}", "body": f"内容{i}" + ("更新" if i == 3 else "")}
        for i in range(1, 8)]
new_count = 0
for item in feed:
    fp = hashlib.md5((str(item["id"]) + item["body"]).encode()).hexdigest()
    if seen.get(str(item["id"])) == fp:
        continue  # 未更新
    seen[str(item["id"])] = fp
    new_count += 1
    print("新/更新:", item["title"])
STATE.write_text(json.dumps(seen, ensure_ascii=False, indent=1))
print(f"本次新增/更新 {new_count} 条")
''')

    # ---- 数据存储 ----
    add("store-csv-export", "抓取结果存 CSV", "csv.DictWriter 落盘，utf-8-sig 防 Excel 乱码。",
        '''"""CSV 存储：utf-8-sig 让 Excel 直接打开不乱码。"""
import csv

rows = [
    {"标题": "商品A", "价格": 129.0, "评分": 4.8},
    {"标题": "商品B", "价格": 89.5, "评分": 4.6},
    {"标题": "商品C", "价格": 259.0, "评分": 4.9},
]
with open("crawl_result.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=["标题", "价格", "评分"])
    writer.writeheader()
    writer.writerows(rows)
print("已写 crawl_result.csv，", len(rows), "行")
''')
    add("store-jsonl", "JSONL 追加存储", "每行一个 JSON 对象，追加写适合流式抓取。",
        '''"""JSONL：流式抓取的标准落盘格式。"""
import json
from pathlib import Path

dest = Path("crawl_result.jsonl")
with dest.open("a", encoding="utf-8") as f:
    for i in range(5):
        record = {"id": i, "title": f"条目{i}", "ts": "2026-09-23T10:00:00"}
        f.write(json.dumps(record, ensure_ascii=False) + "\\n")
print("追加 5 行 ->", dest)
print("当前行数:", sum(1 for _ in dest.open(encoding="utf-8")))
''')
    add("store-sqlite", "SQLite 入库", "抓取数据写 SQLite：建表、去重、查询。",
        '''"""SQLite 存储：抓取数据结构化入库。"""
import sqlite3

conn = sqlite3.connect("crawl.db")
conn.execute("""CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY, title TEXT, price REAL, crawled_at TEXT)""")
conn.executemany("INSERT OR REPLACE INTO items VALUES (?, ?, ?, ?)", [
    (1, "商品A", 129.0, "2026-09-23"),
    (2, "商品B", 89.5, "2026-09-23"),
])
conn.commit()
for row in conn.execute("SELECT id, title, price FROM items ORDER BY price DESC"):
    print(row)
conn.close()
''')

    # ---- 实战目标模式 ----
    add("target-github-api", "GitHub API 实战", "REST API + Rate-Limit 头读取。",
        '''"""GitHub API：抓取 Python 仓库 star 排行（免认证 60 次/小时）。"""
import requests

headers = {"Accept": "application/vnd.github+json"}
resp = requests.get("https://api.github.com/search/repositories",
                    params={"q": "language:python", "sort": "stars", "per_page": 5},
                    headers=headers, timeout=15)
print("剩余配额:", resp.headers.get("X-RateLimit-Remaining"))
for repo in resp.json().get("items", []):
    print(f"{repo['stargazers_count']:>7}  {repo['full_name']}")
''')
    add("target-jsonplaceholder-relations", "关联资源抓取", "posts→comments 主从关联聚合。",
        '''"""关联抓取：帖子与其评论的聚合。"""
import requests

posts = requests.get("https://jsonplaceholder.typicode.com/posts",
                     params={"_limit": 3}, timeout=10).json()
for post in posts:
    comments = requests.get(
        f"https://jsonplaceholder.typicode.com/posts/{post['id']}/comments",
        timeout=10).json()
    print(f"[{post['id']}] {post['title'][:20]}… 评论 {len(comments)} 条")
''')
    add("target-bilibili-view", "B 站视频信息", "B 站 view 接口标准抓取模式（与原库 bili_api 同源）。",
        '''"""B 站视频信息：公开 view 接口（BV 号解析）。"""
import re
import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
           "Referer": "https://www.bilibili.com/"}

def fetch_bv(bvid):
    resp = requests.get("https://api.bilibili.com/x/web-interface/view",
                        params={"bvid": bvid}, headers=HEADERS, timeout=10)
    code = resp.json().get("code")
    if code != 0:
        return None
    d = resp.json()["data"]
    return {"标题": d["title"], "播放": d["stat"]["view"],
            "弹幕": d["stat"]["danmaku"], "UP主": d["owner"]["name"]}

if __name__ == "__main__":
    url = "https://www.bilibili.com/video/BV1GJ411x7h7/"
    bvid = re.search(r"(BV[0-9A-Za-z]{10})", url).group(1)
    info = fetch_bv(bvid)
    print(info or "接口不可达（网络环境限制时属正常）")
''')
    add("crawl-robots-respect", "robots.txt 礼仪", "urllib.robotparser 解析抓取许可（合规爬虫第一课）。",
        '''"""robots.txt：抓取前先读规则。"""
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse

def can_fetch(url, ua="*"):
    rp = RobotFileParser()
    rp.set_url(f"{urlparse(url).scheme}://{urlparse(url).netloc}/robots.txt")
    try:
        rp.read()
    except Exception as e:
        print("robots.txt 读取失败（默认允许）:", type(e).__name__)
        return True
    return rp.can_fetch(ua, url)

for u in ["https://www.baidu.com/s?wd=python", "https://httpbin.org/get"]:
    print(u[:40], "可抓取" if can_fetch(u) else "被 robots 禁止")
''')

    # ---- 工程化 ----
    add("eng-logging", "抓取日志", "logging 模块记录抓取过程（生产排障必备）。",
        '''"""日志：控制台 + 文件双输出。"""
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("crawler.log", encoding="utf-8")],
)
log = logging.getLogger("crawler")

for i in range(3):
    log.info("抓取第 %d 页", i + 1)
    if i == 1:
        log.warning("第 %d 页响应变慢", i + 1)
log.error("模拟一次失败（不影响整体）")
print("日志已写入 crawler.log")
''')
    add("eng-config-dataclass", "爬虫配置类", "dataclass 集中管理抓取参数。",
        '''"""配置类：把散落的抓取参数集中管理。"""
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
''')
    add("eng-cli-argparse", "命令行入口", "argparse 构造可复用的抓取脚本入口。",
        '''"""CLI：python crawler_cli.py --pages 3 --keyword 爬虫"""
import argparse


def main():
    parser = argparse.ArgumentParser(description="通用抓取脚本骨架")
    parser.add_argument("--pages", type=int, default=1, help="抓取页数")
    parser.add_argument("--keyword", default="", help="过滤关键词")
    parser.add_argument("--output", default="out.jsonl", help="输出文件")
    args = parser.parse_args()
    print(f"计划抓取 {args.pages} 页，关键词={args.keyword or '无'}，输出={args.output}")
    for p in range(1, args.pages + 1):
        print(f"  第 {p} 页 …（此处接入真实抓取逻辑）")


''')
    add("eng-graceful-shutdown", "优雅退出", "KeyboardInterrupt 与 finally 保证状态落盘。",
        '''"""优雅退出：Ctrl+C 不丢已抓数据。"""
import sys
import time

items = []

def save():
    print(f"落盘 {len(items)} 条已抓数据")

def main():
    try:
        for i in range(10):
            items.append(f"条目{i}")
            time.sleep(0.2)
            if i == 2:
                raise KeyboardInterrupt  # 模拟 Ctrl+C
    except KeyboardInterrupt:
        print("收到中断信号")
    finally:
        save()
        sys.exit(0)

main()
''')
    add("eng-dedup-queue", "URL 去重队列", "set + 队列的待抓/已抓管理（爬虫调度核心）。",
        '''"""URL 队列：待抓/已抓去重 + 深度限制。"""
from collections import deque

start = "https://example.com/"
queue = deque([(start, 0)])
seen = {start}
results = []
MAX_DEPTH = 2

def fake_links(url):
    return [f"{url}/page{i}" for i in range(2)]

while queue:
    url, depth = queue.popleft()
    results.append((url, depth))
    if depth >= MAX_DEPTH:
        continue
    for link in fake_links(url):
        if link not in seen:
            seen.add(link)
            queue.append((link, depth + 1))

print(f"共发现 {len(results)} 个 URL，最大深度 {max(d for _, d in results)}")
for u, d in results[:6]:
    print("  " * d, u[-20:])
''')
    return c.save()


def build_office():
    c = Collection("office_examples.json", "办公自动化",
                   "真实办公场景脚本：Excel/Word/PDF/批量文件/文本报表。文档类示例自生成文件、自包含可运行。")

    def add(pid, title, desc, code, tags=("办公",), reqs=("openpyxl",), category="tools"):
        c.add(f"{category}_office-{pid}", f"office_{pid}.py", title, desc,
              list(tags), list(reqs), code, category)

    # ---- Excel (openpyxl) ----
    add("xls-create", "Excel 建表入门", "创建工作簿、写表头与数据、保存。",
        '''"""Excel 建表：生成月度销售表。"""
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "销售明细"
ws.append(["日期", "商品", "数量", "金额"])
rows = [["2026-09-01", "键盘", 3, 897.0], ["2026-09-02", "鼠标", 5, 495.0],
        ["2026-09-03", "显示器", 2, 2998.0]]
for r in rows:
    ws.append(r)
wb.save("销售明细.xlsx")
print("已生成 销售明细.xlsx，", ws.max_row - 1, "条记录")
''')
    add("xls-read", "Excel 读取与遍历", "加载工作簿按行迭代，values_only 快速取值。",
        '''"""Excel 读取：遍历 + 汇总。"""
from openpyxl import load_workbook

wb = load_workbook("销售明细.xlsx")
ws = wb["销售明细"]
total = 0.0
for row in ws.iter_rows(min_row=2, values_only=True):
    date, item, qty, amount = row
    print(f"{date} {item} ×{qty} = {amount}")
    total += amount
print("合计金额:", total)
''')
    add("xls-style", "Excel 样式", "字体/填充/对齐/列宽，产出可直接交付的表。",
        '''"""Excel 样式：表头加粗白字 + 蓝底 + 定宽列。"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

wb = Workbook()
ws = wb.active
ws.append(["姓名", "部门", "工资"])
for r in [["张三", "研发", 25000], ["李四", "市场", 18000], ["王五", "研发", 27000]]:
    ws.append(r)
header_font = Font(bold=True, color="FFFFFF")
header_fill = PatternFill("solid", fgColor="4472C4")
for cell in ws[1]:
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = Alignment(horizontal="center")
for col in "ABC":
    ws.column_dimensions[col].width = 14
wb.save("员工表.xlsx")
print("已生成带样式的 员工表.xlsx")
''')
    add("xls-formula", "Excel 公式与汇总", "写入 SUMIF 与 SUM 公式单元格。",
        '''"""Excel 公式：SUMIF 与总计行。"""
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.append(["部门", "金额"])
ws.append(["研发", 25000])
ws.append(["市场", 18000])
ws.append(["研发", 12000])
last = ws.max_row
ws.append(["研发小计", f"=SUMIF(A2:A{last}, \\"研发\\", B2:B{last})"])
ws.append(["总计", f"=SUM(B2:B{last})"])
wb.save("汇总表.xlsx")
print("公式已写入（用 Excel 打开可见计算结果）")
''')
    add("xls-multi-sheet", "多 Sheet 拆分", "按部门把总表拆到多个工作表。",
        '''"""多 Sheet：按部门拆分工作表。"""
from openpyxl import Workbook

data = [("研发", "张三", 25000), ("市场", "李四", 18000), ("研发", "王五", 27000)]
wb = Workbook()
wb.remove(wb.active)
sheets = {}
for dept, name, salary in data:
    ws = sheets.setdefault(dept, wb.create_sheet(dept))
    if ws["A1"].value is None:
        ws.append(["姓名", "工资"])
    ws.append([name, salary])
wb.save("部门拆分.xlsx")
print("工作表:", wb.sheetnames)
''')
    add("xls-dedup-merge", "Excel 去重合并", "以工号为主键去重合并两份名单。",
        '''"""Excel 去重合并：重复工号只保留首条。"""
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.append(["工号", "姓名", "电话"])
seen = set()
for sheet_data in [[["E001", "张三", "13800000001"], ["E002", "李四", "13800000002"]],
                   [["E002", "李四", "13900000002"], ["E003", "王五", "13800000003"]]]:
    for row in sheet_data:
        if row[0] in seen:
            continue
        seen.add(row[0])
        ws.append(row)
wb.save("合并去重.xlsx")
print("合并后:", ws.max_row - 1, "条")
''')
    add("xls-chart", "Excel 内嵌图表", "openpyxl BarChart 直接入表。",
        '''"""Excel 图表：月度数据的内嵌柱状图。"""
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference

wb = Workbook()
ws = wb.active
ws.append(["月份", "销售额"])
for m, v in zip(["1月", "2月", "3月", "4月"], [120, 135, 150, 142]):
    ws.append([m, v])
chart = BarChart()
chart.title = "月度销售额"
data = Reference(ws, min_col=2, min_row=1, max_row=5)
cats = Reference(ws, min_col=1, min_row=2, max_row=5)
chart.add_data(data, titles_from_data=True)
chart.set_categories(cats)
ws.add_chart(chart, "D2")
wb.save("月度图表.xlsx")
print("已生成含图表的 月度图表.xlsx")
''')

    # ---- Word (python-docx) ----
    add("docx-create", "Word 文档生成", "python-docx 创建标题、段落与项目符号。",
        '''"""Word 生成：会议纪要模板。"""
from docx import Document

doc = Document()
doc.add_heading("项目周会纪要", level=1)
doc.add_paragraph("时间：2026-09-23 10:00\\n地点：3F 会议室")
doc.add_heading("一、本周进展", level=2)
doc.add_paragraph("爬虫模块联调完成", style="List Bullet")
doc.add_paragraph("数据看板上线", style="List Bullet")
doc.add_heading("二、风险项", level=2)
doc.add_paragraph("第三方接口限流，需申请配额", style="Intense Quote")
doc.save("周会纪要.docx")
print("已生成 周会纪要.docx")
''', reqs=("python-docx",))
    add("docx-table", "Word 表格", "插入表格并填充数据、套用样式。",
        '''"""Word 表格：数据报表插入。"""
from docx import Document

doc = Document()
doc.add_heading("季度数据", level=1)
table = doc.add_table(rows=1, cols=3)
table.style = "Light Grid Accent 1"
for i, h in enumerate(["季度", "营收(万)", "同比"]):
    table.rows[0].cells[i].text = h
for row in [("Q1", 120, "+8%"), ("Q2", 135, "+12%"), ("Q3", 150, "+11%")]:
    cells = table.add_row().cells
    for i, v in enumerate(row):
        cells[i].text = str(v)
doc.save("季度数据.docx")
print("已生成含表格的 季度数据.docx")
''', reqs=("python-docx",))
    add("docx-read", "Word 读取", "遍历段落提取文本。",
        '''"""Word 读取：先跑 docx-create 生成文件，再提取内容。"""
from docx import Document

doc = Document("周会纪要.docx")
print("== 段落 ==")
for p in doc.paragraphs[:6]:
    if p.text.strip():
        print(f"  [{p.style.name}] {p.text[:30]}")
''', reqs=("python-docx",))

    # ---- 纯标准库办公 ----
    add("file-batch-rename", "批量重命名", "目录内文件按规则批量改名（含预览模式）。",
        '''"""批量重命名：默认预览，--apply 执行。"""
import argparse
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--prefix", default="file")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    files = sorted(p for p in Path(args.directory).iterdir() if p.is_file())
    plan = [(p, p.with_name(f"{args.prefix}_{i:03d}{p.suffix}")) for i, p in enumerate(files, 1)]
    for old, new in plan:
        print(f"{old.name} -> {new.name}")
    if args.apply:
        for old, new in plan:
            old.rename(new)
        print(f"已重命名 {len(plan)} 个")


''', reqs=[])
    add("file-classify", "文件自动分类", "按扩展名把目录文件归档到子目录。",
        '''"""文件分类：图片/文档/压缩包/其他 四类归档。"""
import shutil
from pathlib import Path

RULES = {
    "图片": {".jpg", ".png", ".gif", ".webp"},
    "文档": {".docx", ".pdf", ".md", ".txt", ".xlsx"},
    "压缩包": {".zip", ".7z"},
}
base = Path(".")
for p in list(base.iterdir()):
    if not p.is_file():
        continue
    folder = next((name for name, exts in RULES.items() if p.suffix in exts), "其他")
    dest = base / folder
    dest.mkdir(exist_ok=True)
    shutil.move(str(p), dest / p.name)
    print(f"{p.name} -> {folder}/")
''', reqs=[])
    add("file-duplicate-find", "重复文件查找", "内容 MD5 指纹找重复文件。",
        '''"""重复文件：按内容哈希分组。"""
import hashlib
from pathlib import Path
from collections import defaultdict

groups = defaultdict(list)
for p in Path(".").iterdir():
    if p.is_file() and p.stat().st_size < 1024 * 1024:
        h = hashlib.md5(p.read_bytes()).hexdigest()
        groups[h].append(p)

for h, paths in groups.items():
    if len(paths) > 1:
        print("重复组:", [str(p) for p in paths])
print("扫描完成")
''', reqs=[])
    add("file-tree-report", "目录体积报告", "统计各子目录大小并排序输出。",
        '''"""目录报告：子目录体积排行。"""
from pathlib import Path

def dir_size(d: Path) -> int:
    return sum(f.stat().st_size for f in d.rglob("*") if f.is_file())

base = Path(".")
sizes = [(dir_size(d), d.name) for d in base.iterdir() if d.is_dir()]
for size, name in sorted(sizes, reverse=True)[:10]:
    print(f"{size / 1024 / 1024:8.2f} MB  {name}")
''', reqs=[])
    add("text-report", "文本日报生成", "从数据拼装纯文本日报（模板化输出）。",
        '''"""文本日报：数据 → 模板化报告。"""
data = {
    "date": "2026-09-23",
    "new_users": 128,
    "active_users": 1532,
    "revenue": 9820.5,
    "incidents": ["接口超时 2 次", "缓存抖动 1 次"],
}
lines = [
    f"运营日报 {data['date']}",
    "=" * 30,
    f"新增用户: {data['new_users']}",
    f"活跃用户: {data['active_users']}",
    f"营收: ¥{data['revenue']:,.2f}",
    "",
    "异常事件:",
]
lines += [f"  - {x}" for x in data["incidents"]]
report = "\\n".join(lines)
print(report)
with open("日报.txt", "w", encoding="utf-8") as f:
    f.write(report)
''', reqs=[])
    add("mail-compose-eml", "邮件构造与落盘", "email 模块构造 MIME 邮件并存为 .eml（离线安全）。",
        '''"""邮件构造：生成 .eml 文件（不实际发送）。"""
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from pathlib import Path

msg = MIMEMultipart()
msg["From"] = "report-bot@example.com"
msg["To"] = "boss@example.com"
msg["Subject"] = "【自动】运营日报 2026-09-23"
msg["Date"] = formatdate(localtime=True)
msg.attach(MIMEText("各位好，\\n\\n今日数据请见附件（演示正文）。\\n\\n-- 自动报表机器人", "plain", "utf-8"))
Path("日报邮件.eml").write_bytes(msg.as_bytes())
print("已生成 日报邮件.eml（可用邮件客户端打开预览）")
''', reqs=[])
    add("sched-once-task", "一次性定时任务", "sched 模块延时执行（简单调度入门）。",
        '''"""定时任务：sched 延时执行一次。"""
import sched
import time

scheduler = sched.scheduler(time.time, time.sleep)

def task(name):
    print(f"[{time.strftime('%H:%M:%S')}] 执行任务: {name}")

print("当前:", time.strftime("%H:%M:%S"))
scheduler.enter(2, 1, task, ("每日数据同步",))
scheduler.enter(4, 1, task, ("清理临时文件",))
scheduler.run()
print("队列执行完毕")
''', reqs=[])
    return c.save()


def syntax_check(coll_data):
    import ast as _ast
    import warnings
    bad = 0
    for e in coll_data["examples"]:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                _ast.parse(e["code"])
            except SyntaxError as err:
                bad += 1
                print(f"  ✗ {e['id']}: line {err.lineno} {err.msg}")
    return bad


def main():
    for label, builder, file in [
        ("爬虫实战", build_crawler, "crawler_examples.json"),
        ("办公自动化", build_office, "office_examples.json"),
    ]:
        builder()
        if label == "爬虫实战":
            build_crawler2()
            build_crawler3()
        else:
            build_office2()
            build_office3()
        data = json.load(open(OUT_DIR / file))
        bad = syntax_check(data)
        print(f"OK {label}: {len(data['examples'])} 条 (语法错误 {bad})")




"""第二批真实项目示例：追加到 crawler_examples.json / office_examples.json（合并模式）。"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "json_examples"


def slug(text: str) -> str:
    import re
    return re.sub(r"[^0-9A-Za-z_.-]+", "-", text).strip("-").lower()


def build_crawler2():
    c = Collection("crawler_examples.json", "爬虫实战", "真实请求链路的爬虫示例（第二批）。", merge=True)

    def add(pid, title, desc, code, tags=("爬虫",), reqs=("requests",)):
        c.add(f"topics_crawler2-{pid}", f"crawler2_{pid}.py", title, desc, list(tags), list(reqs), code)

    add("bs4-quote-extract", "名言站点解析", "quotes.toscrape 教学站的经典解析链路（CSS 选择器 + 翻页）。",
        '''"""名言站点：CSS 选择器 + 分页（教学专用站点，允许抓取）。"""
import requests
from bs4 import BeautifulSoup

url, page, all_quotes = "https://quotes.toscrape.com/", 1, []
while url and page <= 3:
    soup = BeautifulSoup(requests.get(url, timeout=10).text, "html.parser")
    for q in soup.select("div.quote"):
        all_quotes.append({
            "text": q.select_one("span.text").get_text(strip=True),
            "author": q.select_one("small.author").text,
            "tags": [t.text for t in q.select("a.tag")],
        })
    nxt = soup.select_one("li.next > a")
    url = "https://quotes.toscrape.com" + nxt["href"] if nxt else None
    page += 1
for q in all_quotes[:5]:
    print(q["author"], "|", q["text"][:30], "|", q["tags"][:2])
print("合计:", len(all_quotes))
''')
    add("bs4-table-parse", "HTML 表格解析", "把页面表格逐行转成结构化字典列表。",
        '''"""表格解析：table → list[dict]。"""
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
''', reqs=("requests", "beautifulsoup4"))
    add("bs4-attribute-filter", "属性过滤定位", "href 开头匹配、data 属性与多 class 定位。",
        '''"""属性过滤：外部链接与自定义属性。"""
from bs4 import BeautifulSoup

HTML = """
<nav>
  <a href="/internal/1">站内</a>
  <a href="https://out.com/x" rel="nofollow">站外</a>
  <a class="btn primary large" data-track="cta">立即注册</a>
</nav>"""
soup = BeautifulSoup(HTML, "html.parser")
external = [a["href"] for a in soup.find_all("a", href=lambda h: h and h.startswith("https://"))]
cta = soup.find("a", attrs={"data-track": "cta"})
multi = soup.find("a", class_=["primary", "large"])
print("外链:", external)
print("CTA:", cta.text, "| 多class:", multi.text)
''', reqs=("requests", "beautifulsoup4"))
    add("bs4-navigate-tree", "节点树导航", "parent/next_sibling/children 树关系遍历。",
        '''"""树导航：相邻节点与父子关系。"""
from bs4 import BeautifulSoup

HTML = "<ul><li>A</li><li class='mark'>B</li><li>C</li></ul>"
soup = BeautifulSoup(HTML, "html.parser")
mark = soup.find("li", class_="mark")
print("前一个:", mark.find_previous_sibling("li").text)
print("后一个:", mark.find_next_sibling("li").text)
print("父节点:", mark.parent.name)
print("全部兄弟:", [li.text for li in mark.find_parent("ul").children if li.name])
''', reqs=("requests", "beautifulsoup4"))
    add("bs4-regex-class", "正则 class 匹配", "class_ 含正则模式的模糊定位。",
        '''"""class 模糊匹配：re.compile + find_all。"""
import re
from bs4 import BeautifulSoup

HTML = """
<div class="post-101 top">帖101</div>
<div class="post-102">帖102</div>
<div class="post-103 hot">帖103</div>"""
soup = BeautifulSoup(HTML, "html.parser")
posts = soup.find_all("div", class_=re.compile(r"^post-\\d+$"))
print("帖子数:", len(posts), [p.text for p in posts])
hot = soup.find("div", class_=re.compile("hot"))
print("热帖:", hot.text)
''', reqs=("requests", "beautifulsoup4"))
    add("antiban-header-pool", "UA 池轮换", "随机 UA 池 + 每次请求轮换。",
        '''"""UA 池：每次请求随机挑一个身份。"""
import random
import requests

UA_POOL = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/126.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/126.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 14) Chrome/125.0.0.0 Mobile",
]
for _ in range(3):
    ua = random.choice(UA_POOL)
    resp = requests.get("https://httpbin.org/user-agent",
                        headers={"User-Agent": ua}, timeout=10)
    print(resp.json()["user-agent"][:44])
''')
    add("antiban-backoff-jitter", "退避抖动", "指数退避 + 随机抖动，避免重试风暴。",
        '''"""退避抖动：base * 2^n + jitter。"""
import random
import time

def backoff(attempt, base=0.5, cap=8.0):
    return min(cap, base * 2 ** attempt) + random.uniform(0, 0.3)

for n in range(5):
    print(f"第 {n} 次重试等待 {backoff(n):.2f}s")
    time.sleep(0.05)  # 演示用缩短
''')
    add("antiban-cookie-login", "Cookie 登录态", "加载浏览器导出的 Cookie 文件恢复登录态。",
        '''"""Cookie 登录态：从 JSON 文件恢复（配合浏览器导出）。"""
import json
import requests

# cookie 文件格式: [{"name": "sessdata", "value": "...", "domain": ".bilibili.com"}, ...]
SAMPLE = [{"name": "demo_session", "value": "abc123"}]
cookie_file = "cookies.json"
with open(cookie_file, "w", encoding="utf-8") as f:
    json.dump(SAMPLE, f)

s = requests.Session()
for ck in json.load(open(cookie_file)):
    s.cookies.set(ck["name"], ck["value"])
print("已装载 Cookie:", [(c.name, c.value) for c in s.cookies])
resp = s.get("https://httpbin.org/cookies", timeout=10)
print("服务端视角:", resp.json()["cookies"])
''')
    add("antiban-throttle-domain", "分域限速", "多域名独立限速的调度器。",
        '''"""分域限速：每个域名独立的最小间隔。"""
import time
from collections import defaultdict
from urllib.parse import urlparse

_last = defaultdict(float)
INTERVALS = {"api.github.com": 2.0, "httpbin.org": 0.5}

def throttled(url, fn):
    host = urlparse(url).netloc
    wait = INTERVALS.get(host, 1.0) - (time.monotonic() - _last[host])
    if wait > 0:
        time.sleep(wait)
    _last[host] = time.monotonic()
    return fn(url)

for u in ["https://httpbin.org/get?a=1", "https://httpbin.org/get?a=2",
          "https://api.github.com/zen"]:
    print("调度:", urlparse(u).netloc)
    throttled(u, lambda x: None)
''')
    add("store-dataset-clean", "抓取数据清洗", "空值/去空格/类型转换/异常行剔除流水线。",
        '''"""数据清洗：抓取结果的标准化流水线。"""
raw = [
    {"name": " 商品A ", "price": "129.00", "stock": "12"},
    {"name": "", "price": "89.5", "stock": "3"},
    {"name": "商品B", "price": "暂无", "stock": "0"},
    {"name": "商品C", "price": " 259 ", "stock": "7"},
]
clean = []
for r in raw:
    name = (r.get("name") or "").strip()
    try:
        price = float(r["price"])
        stock = int(r["stock"])
    except ValueError:
        continue  # 坏数据丢弃并记录（生产中打日志）
    if not name or price <= 0:
        continue
    clean.append({"name": name, "price": price, "stock": stock})
print(clean)
''')
    add("store-export-excel-like", "汇总报表输出", "分组聚合 + 格式化输出（抓取 → 报表）。",
        '''"""汇总报表：按类目聚合抓取结果。"""
from collections import defaultdict

items = [
    {"cat": "数码", "name": "键盘", "amount": 299},
    {"cat": "数码", "name": "鼠标", "amount": 99},
    {"cat": "图书", "name": "Python Cookbook", "amount": 128},
    {"cat": "图书", "name": "算法图解", "amount": 78},
]
by_cat = defaultdict(list)
for it in items:
    by_cat[it["cat"]].append(it)
print(f"{'类目':<6}{'条数':>4}{'金额合计':>10}")
for cat, rows in by_cat.items():
    total = sum(r["amount"] for r in rows)
    print(f"{cat:<6}{len(rows):>4}{total:>10}")
''')
    add("target-rss-parse", "RSS 订阅解析", "xml.etree 解析 RSS feed（博客/新闻订阅）。",
        '''"""RSS 解析：标准库解析订阅源结构。"""
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
''')
    add("target-xml-namespaces", "带命名空间的 XML", "namespace 感知的 Atom feed 解析。",
        '''"""Atom feed：命名空间写法。"""
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
''')
    add("eng-checkpoint-resume", "断点续抓", "游标落盘，重启后从断点继续。",
        '''"""断点续抓：游标状态持久化。"""
import json
from pathlib import Path

STATE = Path("cursor.json")
cursor = json.loads(STATE.read_text())["cursor"] if STATE.exists() else 0
TOTAL = 10
print(f"从游标 {cursor} 继续")
for page in range(cursor, TOTAL):
    print(f"处理页 {page}")
    cursor = page + 1
    if page == 5:  # 模拟中断
        break
STATE.write_text(json.dumps({"cursor": cursor}))
print(f"游标已存至 {cursor}，重跑将继续")
''')
    add("eng-structure-project", "爬虫项目结构", "配置/调度/解析/存储 分层的最小项目骨架。",
        '''"""项目分层：一个可维护爬虫的最小骨架。"""
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
''')
    add("eng-test-spider", "爬虫单测", "用固定 HTML 样本对解析函数做单元测试（不入网络）。",
        '''"""解析函数单测：离线样本测试（pytest 风格）。"""
from bs4 import BeautifulSoup

def parse_items(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    return [{"title": q.select_one("h3").text,
             "link": q.select_one("a")["href"]} for q in soup.select("div.item")]

SAMPLE = """<div class="item"><h3>标题一</h3><a href="/1"></a></div>
<div class="item"><h3>标题二</h3><a href="/2"></a></div>"""

def test_parse_items():
    got = parse_items(SAMPLE)
    assert len(got) == 2
    assert got[0] == {"title": "标题一", "link": "/1"}

test_parse_items()
print("解析单测通过（离线，无网络）")
''', reqs=("requests", "beautifulsoup4"))
    return c.save()


def build_office2():
    c = Collection("office_examples.json", "办公自动化", "真实办公场景脚本（第二批）。", merge=True)

    def add(pid, title, desc, code, tags=("办公",), reqs=("openpyxl",)):
        c.add(f"tools_office2-{pid}", f"office2_{pid}.py", title, desc, list(tags), list(reqs), code, category="tools")

    add("xls-freeze-header", "冻结表头", "冻结首行 + 自动筛选，大表浏览体验。",
        '''"""冻结窗格与自动筛选。"""
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.append(["订单号", "客户", "金额", "状态"])
for i in range(1, 21):
    ws.append([f"SO{i:04d}", f"客户{i}", i * 37.5, "已付" if i % 2 else "未付"])
ws.freeze_panes = "A2"          # 冻结首行
ws.auto_filter.ref = ws.dimensions  # 表头筛选
wb.save("订单表.xlsx")
print("已生成 冻结首行 + 筛选的 订单表.xlsx")
''')
    add("xls-conditional", "条件格式", "金额超标自动标红（CellIsRule）。",
        '''"""条件格式：超阈值标红。"""
from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Font, PatternFill

wb = Workbook()
ws = wb.active
ws.append(["项目", "支出"])
for r in [["服务器", 3200], ["差旅", 880], ["外包", 5600], ["培训", 1500]]:
    ws.append(r)
red = PatternFill("solid", fgColor="FFC7CE")
ws.conditional_formatting.add(
    f"B2:B{ws.max_row}",
    CellIsRule(operator="greaterThan", formula=["3000"], fill=red, font=Font(color="9C0006")))
wb.save("支出表.xlsx")
print("超 3000 的行已自动标红")
''')
    add("xls-sort-in-place", "Excel 数据排序", "按列排序后回写（读取 → sorted → 重写）。",
        '''"""Excel 排序：按金额降序重写。"""
from openpyxl import Workbook, load_workbook

wb = Workbook()
ws = wb.active
ws.append(["姓名", "分数"])
for r in [["甲", 78], ["乙", 92], ["丙", 85], ["丁", 66]]:
    ws.append(r)
wb.save("成绩原始.xlsx")

rows = list(load_workbook("成绩原始.xlsx").active.iter_rows(min_row=2, values_only=True))
rows.sort(key=lambda r: -r[1])
out = Workbook()
osheet = out.active
osheet.append(["姓名", "分数"])
for r in rows:
    osheet.append(r)
out.save("成绩排序.xlsx")
print("排序完成:", rows)
''')
    add("xls-validate", "数据校验", "工时表合法性校验（范围/必填/类型）。",
        '''"""Excel 数据校验：错误行收集报告。"""
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.append(["日期", "工时", "备注"])
data = [["2026-09-20", 8, ""], ["2026-09-21", 12, "加班"], ["2026-09-22", 0, ""], ["2026-09-23", -2, ""]]
errors = []
for i, (d, h, note) in enumerate(data, start=2):
    if not isinstance(h, (int, float)) or not (0 < h <= 16):
        errors.append(f"第{i}行 工时非法: {h}")
        continue
    ws.append([d, h, note])
wb.save("工时表.xlsx")
print("校验报告:", errors or "全部通过")
''')
    add("xls-two-file-diff", "两表对比", "找出两份名单的差异（新增/消失）。",
        '''"""两表对比：新增与移除名单。"""
from openpyxl import Workbook

old = {"E001": "张三", "E002": "李四", "E003": "王五"}
new = {"E002": "李四", "E003": "王五", "E004": "赵六"}

added = {k: v for k, v in new.items() if k not in old}
removed = {k: v for k, v in old.items() if k not in new}
print("新增:", added)
print("移除:", removed)

wb = Workbook()
ws = wb.active
ws.append(["变更类型", "工号", "姓名"])
for k, v in added.items():
    ws.append(["新增", k, v])
for k, v in removed.items():
    ws.append(["移除", k, v])
wb.save("人员变更.xlsx")
''')
    add("xls-csv-convert", "CSV ↔ Excel 互转", "CSV 导入为 xlsx，再导回 CSV 验证。",
        '''"""CSV ↔ Excel 互转。"""
import csv
from openpyxl import Workbook, load_workbook

# CSV → Excel
with open("data.csv", "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows([["城市", "人口"], ["上海", 2487], ["北京", 2189], ["深圳", 1756]])

wb = Workbook()
ws = wb.active
with open("data.csv", encoding="utf-8") as f:
    for row in csv.reader(f):
        ws.append(row)
wb.save("城市.xlsx")

# Excel → CSV
rows = load_workbook("城市.xlsx").active.iter_rows(values_only=True)
with open("还原.csv", "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(rows)
print("互转完成，内容一致:", open("data.csv").read() == open("还原.csv").read())
''')
    add("docx-batch-letters", "Word 批量函件", "模板 + 名单批量生成个性化函件。",
        '''"""批量函件：模板替换生成多份 Word。"""
from docx import Document

template = "尊敬的 {name}：\\n\\n    您在本系统的账号 {account} 已通过审核。\\n\\n运营团队"
members = [{"name": "张三", "account": "zs001"}, {"name": "李四", "account": "ls002"},
           {"name": "王五", "account": "ww003"}]
for m in members:
    doc = Document()
    doc.add_paragraph(template.format(**m))
    doc.save(f"函件_{m['account']}.docx")
print(f"已生成 {len(members)} 份函件")
''', reqs=("python-docx",))
    add("docx-image", "Word 插入图片", "生成图片并插入文档（配合 matplotlib 出图）。",
        '''"""Word 插图：matplotlib 出图 → 插入 Word。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from docx import Document
from docx.shared import Inches

fig, ax = plt.subplots(figsize=(5, 3))
ax.bar(["Q1", "Q2", "Q3"], [120, 135, 150], color="#4472C4")
fig.savefig("季度图.png", dpi=100)
plt.close(fig)

doc = Document()
doc.add_heading("季度营收", level=1)
doc.add_picture("季度图.png", width=Inches(4.5))
doc.save("季度报告.docx")
print("已生成含图的 季度报告.docx")
''', reqs=("python-docx", "matplotlib"))
    add("file-backup-zip", "目录打包备份", "zipfile 增量命名备份目录。",
        '''"""目录备份：zip 打包 + 时间戳命名。"""
import zipfile
from datetime import datetime
from pathlib import Path

src = Path(".")
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
dest = Path(f"backup_{stamp}.zip")
with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
    for p in src.rglob("*"):
        if p.is_file() and "backup_" not in p.name and ".venv" not in p.parts:
            zf.write(p, p.relative_to(src))
print(f"备份完成: {dest.name} ({dest.stat().st_size // 1024} KB)")
''', reqs=[])
    add("file-log-rotate", "日志轮转", "按大小切分日志文件（RotatingHandler 思路的手写版）。",
        '''"""日志轮转：超过阈值切分为 .1/.2 文件。"""
from pathlib import Path

log = Path("app.log")
log.write_text("\\n".join(f"line {i}" for i in range(100)), encoding="utf-8")

MAX_BYTES = 400
if log.exists() and log.stat().st_size > MAX_BYTES:
    content = log.read_text(encoding="utf-8").splitlines(keepends=True)
    part, idx = [], 1
    size = 0
    for ln in content:
        if size + len(ln) > MAX_BYTES:
            Path(f"app.log.{idx}").write_text("".join(part), encoding="utf-8")
            part, size, idx = [], 0, idx + 1
        part.append(ln)
        size += len(ln)
    if part:
        Path(f"app.log.{idx}").write_text("".join(part), encoding="utf-8")
    log.unlink()
    print(f"已切分为 {idx} 个文件")
''', reqs=[])
    add("todo-markdown", "Markdown 待办清单", "从数据生成/解析 Markdown 待办（任务管理最小实现）。",
        '''"""Markdown 待办：生成与统计。"""
from pathlib import Path

tasks = [("已完成", "恢复示例库"), ("已完成", "修复构建链路"),
         ("进行中", "扩充示例规模"), ("待办", "补拍 README 截图")]
lines = ["# 待办清单", ""]
for status, task in tasks:
    mark = {"已完成": "x", "进行中": " ", "待办": " "}[status]
    lines.append(f"- [{mark}] {task}（{status}）")
Path("TODO.md").write_text("\\n".join(lines), encoding="utf-8")
print("\\n".join(lines))
done = sum(1 for s, _ in tasks if s == "已完成")
print(f"完成度: {done}/{len(tasks)}")
''', reqs=[])
    add("clipboard-inventory", "库存盘点脚本", "字典合并盘点：期初 + 入库 − 出库 = 期末。",
        '''"""库存盘点：期初/入库/出库 三表核算。"""
from collections import defaultdict

opening = {"键盘": 12, "鼠标": 30, "显示器": 5}
inflow = {"键盘": 10, "鼠标": 5}
outflow = {"键盘": 8, "鼠标": 15, "显示器": 2}

stock = defaultdict(int, opening)
for k, v in inflow.items():
    stock[k] += v
for k, v in outflow.items():
    stock[k] -= v
print(f"{'商品':<6}{'期末库存':>8}")
for k in sorted(stock):
    flag = " ⚠️需补货" if stock[k] < 5 else ""
    print(f"{k:<6}{stock[k]:>8}{flag}")
''', reqs=[])
    return c.save()




"""第三批真实项目示例：爬虫进阶 + 办公进阶（合并到既有集合文件）。"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "json_examples"


def build_crawler3():
    c = Collection("crawler_examples.json", "爬虫实战", "真实请求链路的爬虫示例（第三批追加）。", merge=True)

    def add(pid, title, desc, code, tags=("爬虫", "进阶"), reqs=("requests",)):
        c.add(f"topics_crawler3-{pid}", f"crawler3_{pid}.py", title, desc, list(tags), list(reqs), code)

    add("etag-conditional", "ETag 条件请求", "If-None-Match / 304 未变更跳过（增量抓取标准做法）。",
        '''"""ETag 条件请求：内容未变时 304，省流量。"""
import requests

cache = {"etag": None, "body": None}
url = "https://httpbin.org/etag/w3s4all"
headers = {"If-None-Match": cache["etag"]} if cache["etag"] else {}
resp = requests.get(url, headers=headers, timeout=10)
if resp.status_code == 304:
    print("内容未变（304），使用缓存")
else:
    cache["etag"] = resp.headers.get("ETag")
    cache["body"] = resp.text
    print("新内容已缓存，ETag =", cache["etag"])
''')
    add("last-modified", "Last-Modified 增量", "If-Modified-Since 时间戳增量。",
        '''"""Last-Modified：按修改时间增量抓取。"""
import requests

since = "Sat, 20 Sep 2026 00:00:00 GMT"
resp = requests.get("https://httpbin.org/response-headers",
                    params={"Last-Modified": since}, timeout=10)
print("响应 Last-Modified:", resp.headers.get("Last-Modified"))
print("真实场景：本地存时间戳，未变更则跳过解析")
''')
    add("open-meteo-weather", "开放天气 API", "Open-Meteo 免费无 key 天气接口（真实可运行）。",
        '''"""Open-Meteo：上海 7 天天气预报（免费无需 key）。"""
import requests

resp = requests.get("https://api.open-meteo.com/v1/forecast",
                    params={"latitude": 31.23, "longitude": 121.47,
                            "daily": "temperature_2m_max,temperature_2m_min",
                            "timezone": "Asia/Shanghai"}, timeout=10)
daily = resp.json()["daily"]
for d, tmax, tmin in zip(daily["time"], daily["temperature_2m_max"], daily["temperature_2m_min"]):
    print(f"{d}  {tmin}~{tmax}°C")
''')
    add("exchange-rate-api", "汇率 API 抓取", "open.er-api 实时汇率（免费无 key）。",
        '''"""汇率抓取：open.er-api.com 实时牌价。"""
import requests

resp = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
rates = resp.json()["rates"]
for cur in ("CNY", "EUR", "JPY", "HKD"):
    print(f"1 USD = {rates.get(cur, '?')} {cur}")
print("更新时间:", resp.json().get("time_last_update_utc"))
''')
    add("wikipedia-api", "Wikipedia API", "维基百科 REST 摘要接口（免 key）。",
        '''"""Wikipedia 摘要接口：词条概要抓取。"""
import requests

resp = requests.get("https://zh.wikipedia.org/api/rest_v1/page/summary/Python",
                    headers={"User-Agent": "learning-demo/1.0"}, timeout=10)
data = resp.json()
print("标题:", data.get("title"))
print("摘要:", (data.get("extract") or "")[:80], "...")
''')
    add("api-sign-hmac", "API 签名（HMAC）", "timestamp + HMAC-SHA256 请求签名的标准构造。",
        '''"""API 签名：私有接口的标准鉴权构造。"""
import hashlib
import hmac
import time
from urllib.parse import urlencode

API_KEY, SECRET = "demo-key", "demo-secret"
params = {"symbol": "BTCUSDT", "timestamp": int(time.time() * 1000)}
query = urlencode(params)
sign = hmac.new(SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
print("待签名串:", query)
print("签名:", sign[:32], "...")
print("完整请求: /api/v1/order?" + query + "&signature=" + sign[:16] + "…")
''')
    add("websocket-stream", "WebSocket 行情流", "websocket-client 订阅实时推送（连接管理 + 心跳）。",
        '''"""WebSocket 订阅：实时数据流消费模式。"""
import json

# 同步演示：真实连接替换 ws.connect(...) 的目标地址
SAMPLE_MSGS = [
    {"channel": "trades", "data": {"price": 64500.1, "side": "buy"}},
    {"channel": "trades", "data": {"price": 64501.5, "side": "sell"}},
]
print("订阅 trades 频道 → 消费 2 条演示消息")
for msg in SAMPLE_MSGS:
    print(json.dumps(msg, ensure_ascii=False))
# 真实写法:
# from websocket import create_app  # pip install websocket-client
# ws = create_app("wss://stream.example.com/ws")
# ws.send(json.dumps({"op": "subscribe", "channel": "trades"}))
# while True: handle(json.loads(ws.recv()))
''')
    add("playwright-browser", "浏览器自动化（Playwright）", "JS 渲染页面的标准解法：无头浏览器截图与取值。",
        '''"""Playwright：JS 渲染页面的抓取（需 pip install playwright && playwright install chromium）。"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://example.com", wait_until="domcontentloaded")
    print("标题:", page.title())
    page.screenshot(path="page.png", full_page=True)
    browser.close()
print("截图已保存 page.png（本机未装浏览器时此脚本报缺依赖，属正常）")
''', reqs=("requests", "playwright"))
    add("selenium-login-pattern", "Selenium 登录模式", "显式等待 + 表单填写 + Cookie 导出的标准流程。",
        '''"""Selenium：显式等待的登录流程骨架。"""
# 需 pip install selenium 并配置浏览器驱动
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

print("""Selenium 登录骨架（伪代码演示，实际需浏览器环境）:
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)
    driver.get("https://example.com/login")
    wait.until(lambda d: d.find_element(By.ID, "username")).send_keys("user")
    driver.find_element(By.ID, "password").send_keys("pass")
    driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
    cookies = driver.get_cookies()   # 导出后供 requests 会话使用
""")
''', reqs=("requests", "selenium"))
    add("mini-scrapy-framework", "迷你爬虫框架", "调度器+下载器+解析器+管道的 40 行微型框架。",
        '''"""迷你框架：理解 Scrapy 的核心抽象。"""
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
''')
    add("data-pandas-clean", "pandas 数据清洗", "read_json + 去空/去重/类型转换（DataFrame 版）。",
        '''"""pandas 清洗：抓取数据标准化。"""
import pandas as pd

raw = pd.DataFrame([
    {"name": " 商品A ", "price": "129.00", "stock": 12},
    {"name": None, "price": "89.5", "stock": 3},
    {"name": "商品B", "price": None, "stock": 0},
    {"name": "商品A ", "price": "129.00", "stock": 12},
])
df = raw.assign(name=raw["name"].str.strip(), price=pd.to_numeric(raw["price"], errors="coerce"))
df = df.dropna(subset=["name", "price"]).drop_duplicates(subset=["name"])
df["stock"] = df["stock"].astype(int)
print(df)
print("清洗后:", len(df), "/", len(raw))
''', reqs=("requests", "pandas"))
    add("scheduler-apscheduler", "apscheduler 定时抓取", "BackgroundScheduler 每小时任务（生产调度）。",
        '''"""apscheduler：后台定时抓取（演示跑一轮即退出）。"""
from apscheduler.schedulers.background import BackgroundScheduler

runs = []

def hourly_fetch():
    runs.append("fetch")

sched = BackgroundScheduler()
sched.add_job(hourly_fetch, "interval", seconds=1, id="hourly")
sched.start()
import time
time.sleep(2.5)
sched.shutdown()
print(f"2.5 秒内触发 {len(runs)} 次（真实场景设 hours=1）")
''', reqs=("requests", "apscheduler"))
    add("health-check", "抓取健康监控", "多目标可用性探测 + 汇总报告。",
        '''"""健康检查：多目标探测与报告。"""
import time
import requests

TARGETS = [
    ("httpbin", "https://httpbin.org/status/200"),
    ("jsonplaceholder", "https://jsonplaceholder.typicode.com/posts/1"),
    ("github", "https://api.github.com"),
]
report = []
for name, url in TARGETS:
    t0 = time.monotonic()
    try:
        code = requests.get(url, timeout=8).status_code
        ok = code < 400
    except requests.RequestException:
        code, ok = 0, False
    report.append((name, code, (time.monotonic() - t0) * 1000, ok))
for name, code, ms, ok in report:
    print(f"{'✓' if ok else '✗'} {name:<16} {code or '-':>3}  {ms:6.0f}ms")
''')
    add("image-batch-download", "图片批量下载", "URL 列表 → 并发落盘 + 扩展名推断。",
        '''"""图片批量下载：内容类型决定扩展名。"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests

IMAGES = ["https://httpbin.org/image/png", "https://httpbin.org/image/jpeg"]
dest = Path("images")
dest.mkdir(exist_ok=True)

def download(url):
    resp = requests.get(url, timeout=15)
    ctype = resp.headers.get("Content-Type", "")
    ext = ".png" if "png" in ctype else ".jpg" if "jpeg" in ctype else ".bin"
    p = dest / f"img_{abs(hash(url)) % 10000}{ext}"
    p.write_bytes(resp.content)
    return p.name, len(resp.content)

with ThreadPoolExecutor(4) as pool:
    for name, size in pool.map(download, IMAGES):
        print(f"{name} {size // 1024}KB")
''')
    add("m3u8-pattern", "m3u8 视频分段模式", "HLS 分段索引解析与顺序下载（标准模式演示）。",
        '''"""m3u8：HLS 视频的分段索引与下载模式（演示解析）。"""
M3U8 = """#EXTM3U
#EXT-X-TARGETDURATION:10
#EXTINF:9.5,
seg_0.ts
#EXTINF:9.2,
seg_1.ts
#EXTINF:8.8,
seg_2.ts
#EXT-X-ENDLIST"""
segments = []
for line in M3U8.splitlines():
    line = line.strip()
    if line and not line.startswith("#"):
        segments.append(line)
total = 10.0  # 真实场景解析 EXTINF 累加
print(f"共 {len(segments)} 段: {segments}")
print("真实抓取：requests 逐段下载 → 二进制拼接 → ffmpeg 合并转封装")
''')
    add("headers-order-honesty", "请求指纹与自报家门", "为什么爬虫要诚实声明身份 + 合规清单。",
        '''"""合规清单：真实项目的自我要求。"""
CHECKLIST = """
□ 遵守 robots.txt 与站点条款
□ 控制 QPS，加礼貌延时（≥1s 对小型站点）
□ 填写真实 Contact 的 UA，便于站长联系
□ 只抓公开数据，绝不绕过鉴权
□ 数据不转售、不侵犯隐私（个人信息保护法）
□ 失败重试有上限，避免打挂对方
"""
print(CHECKLIST)
print("爬虫的合法边界：公开数据 + 非垄断用途 + 尊重站点意愿")
''')
    return c.save()


def build_office3():
    c = Collection("office_examples.json", "办公自动化", "真实办公场景脚本（第三批追加）。", merge=True)

    def add(pid, title, desc, code, tags=("办公", "进阶"), reqs=("openpyxl",)):
        c.add(f"tools_office3-{pid}", f"office3_{pid}.py", title, desc, list(tags), list(reqs), code, category="tools")

    add("pptx-create", "PPT 幻灯片生成", "python-pptx 生成标题页 + 要点页 + 数据页。",
        '''"""PPT 生成：三页周报幻灯片。"""
from pptx import Presentation
from pptx.util import Inches, Pt

prs = Presentation()
s1 = prs.slides.add_slide(prs.slide_layouts[0])
s1.shapes.title.text = "项目周报"
s1.placeholders[1].text = "2026-09-23 · 自动生成"

s2 = prs.slides.add_slide(prs.slide_layouts[1])
s2.shapes.title.text = "本周要点"
for line in ["爬虫模块联调完成", "示例库扩充至 3000+", "看板数据接入"]:
    s2.placeholders[1].text_frame.add_paragraph().text = line

s3 = prs.slides.add_slide(prs.slide_layouts[5])
s3.shapes.title.text = "数据概览"
s3.shapes.add_textbox(Inches(1), Inches(2), Inches(8), Inches(2)).text_frame.text = "3120 个示例 · 13 个集合 · 测试全绿"
prs.save("项目周报.pptx")
print("已生成 项目周报.pptx（3 页）")
''', reqs=("python-pptx",))
    add("pptx-table", "PPT 数据表", "幻灯片内插入表格与图片。",
        '''"""PPT 表格与图片页。"""
from pptx import Presentation
from pptx.util import Inches

prs = Presentation()
slide = prs.slides.add_slide(prs.slide_layouts[5])
slide.shapes.title.text = "指标表"
rows, cols = 3, 3
table = slide.shapes.add_table(rows, cols, Inches(1), Inches(2), Inches(8), Inches(2)).table
for c, h in enumerate(["指标", "本周", "上周"]):
    table.cell(0, c).text = h
for r, row in enumerate([["示例数", "3120", "176"], ["测试", "全绿", "全绿"]], 1):
    for c, v in enumerate(row):
        table.cell(r, c).text = str(v)
prs.save("指标汇报.pptx")
print("已生成 指标汇报.pptx")
''', reqs=("python-pptx",))
    add("pdf-split", "PDF 拆分", "把多页 PDF 按页拆成单页文件。",
        '''"""PDF 拆分：每页一个文件。"""
import io
from pypdf import PdfReader, PdfWriter

buf = io.BytesIO()
w = PdfWriter()
for _ in range(3):
    w.add_blank_page(width=595, height=842)
w.write(buf)
buf.seek(0)

reader = PdfReader(buf)
for i, page in enumerate(reader.pages):
    out = PdfWriter()
    out.add_page(page)
    with open(f"第{i + 1}页.pdf", "wb") as f:
        out.write(f)
print(f"已拆分为 {len(reader.pages)} 个单页 PDF")
''', reqs=("pypdf",))
    add("pdf-extract-text", "PDF 文本提取", "逐页提取文本（扫描件需 OCR 另议）。",
        '''"""PDF 文本提取。"""
from pypdf import PdfReader
from pypdf import PdfWriter
import io

buf = io.BytesIO()
w = PdfWriter()
page = w.add_blank_page(width=595, height=842)
w.write(buf); buf.seek(0)
reader = PdfReader(buf)
for i, page in enumerate(reader.pages):
    text = page.extract_text() or ""
    print(f"第{i + 1}页文本长度: {len(text)}（空白页为 0）")
''', reqs=("pypdf",))
    add("xls-pivot-groupby", "Excel 透视汇总", "groupby 聚合后写透视结果表。",
        '''"""透视：按部门/月份双维聚合。"""
from collections import defaultdict
from openpyxl import Workbook

rows = [("研发", "1月", 120), ("研发", "2月", 135), ("市场", "1月", 90),
        ("市场", "2月", 110), ("研发", "1月", 60)]
pivot = defaultdict(float)
for dept, month, amount in rows:
    pivot[(dept, month)] += amount
depts = sorted({r[0] for r in rows})
months = sorted({r[1] for r in rows})

wb = Workbook()
ws = wb.active
ws.append(["部门"] + months)
for d in depts:
    ws.append([d] + [pivot.get((d, m), 0) for m in months])
wb.save("透视表.xlsx")
print("透视完成：", wb.sheetnames, ws.max_row - 1, "行")
''')
    add("xls-vlookup-join", "跨表关联", "Excel 版 VLOOKUP：按工号拼两表字段。",
        '''"""跨表关联：主表 + 字典表拼接。"""
from openpyxl import Workbook

main = [["E001", "销售", 8000], ["E002", "研发", 12000], ["E003", "市场", 9000]]
lookup = {"E001": "张三", "E002": "李四", "E003": "王五"}
wb = Workbook()
ws = wb.active
ws.append(["工号", "姓名", "部门", "工资"])
for emp_id, dept, salary in main:
    ws.append([emp_id, lookup.get(emp_id, "<未知>"), dept, salary])
wb.save("关联结果.xlsx")
print("关联完成:", ws.max_row - 1, "行")
''')
    add("xls-protect", "工作表保护", "锁定公式列，仅允许编辑指定区域。",
        '''"""工作表保护：锁定公式，开放输入列。"""
from openpyxl import Workbook
from openpyxl.styles import Protection

wb = Workbook()
ws = wb.active
ws.append(["数量", "单价", "金额"])
for i in range(1, 4):
    ws.append([None, 25.0, None])
    ws.cell(row=i + 1, column=3, value=f"=A{i + 1}*B{i + 1}")
for row in ws.iter_rows(min_row=2, min_col=1, max_col=2):  # 输入列解锁
    for cell in row:
        cell.protection = Protection(locked=False)
ws.protection.sheet = True
wb.save("受保护表.xlsx")
print("公式列已锁定，数量/单价列可编辑")
''')
    add("xls-merged-cells", "合并单元格表头", "跨列合并的分组表头。",
        '''"""合并单元格：两级表头。"""
from openpyxl import Workbook
from openpyxl.styles import Alignment

wb = Workbook()
ws = wb.active
ws.merge_cells("A1:A2"); ws["A1"] = "月份"
ws.merge_cells("B1:C1"); ws["B1"] = "销售额"
ws["B2"], ws["C2"] = "线上", "线下"
for cell in ("A1", "B1"):
    ws[cell].alignment = Alignment(horizontal="center", vertical="center")
ws.append(["1月", 100, 60])
ws.append(["2月", 120, 75])
wb.save("分组表头.xlsx")
print("两级表头已生成")
''')
    add("xls-annotation", "单元格批注", "写批注说明数据口径。",
        '''"""批注：给数据加口径说明。"""
from openpyxl import Workbook
from openpyxl.comments import Comment

wb = Workbook()
ws = wb.active
ws.append(["指标", "数值"])
ws["B2"] = 3120
ws["B2"].comment = Comment("示例库总量，2026-09-23 快照", "报表机器人")
ws["B3"] = 39
ws["B3"].comment = Comment("共享依赖包数（requirements.txt）", "报表机器人")
wb.save("带批注.xlsx")
print("批注已写入（悬停单元格可见）")
''')
    add("img-watermark", "图片批量水印", "PIL 半透明文字水印铺满图片。",
        '''"""批量水印：右下角半透明文字。"""
from PIL import Image, ImageDraw, ImageFont

base = Image.new("RGB", (640, 420), "#2b3a55")
d = ImageDraw.Draw(base)
for x in range(0, 640, 80):
    d.line([(x, 0), (x, 420)], fill="#3b4a66", width=1)

watermark = Image.new("RGBA", base.size, (0, 0, 0, 0))
wd = ImageDraw.Draw(watermark)
for y in range(20, 420, 90):
    for x in range(20, 640, 200):
        wd.text((x, y), "© 示例库", fill=(255, 255, 255, 90))
result = Image.alpha_composite(base.convert("RGBA"), watermark).convert("RGB")
result.save("水印图.png")
print("已生成 水印图.png")
''', reqs=("pillow",))
    add("img-to-pdf", "图片转 PDF", "多张图片合成一个 PDF（img2pdf 思路，Pillow 实现）。",
        '''"""图片转 PDF：Pillow 多页保存。"""
from PIL import Image

pages = []
for color in ("#e74c3c", "#2ecc71", "#3498db"):
    pages.append(Image.new("RGB", (595, 842), color))
pages[0].save("图片合集.pdf", save_all=True, append_images=pages[1:])
print("已生成 图片合集.pdf（3 页）")
''', reqs=("pillow",))
    add("xls-sqlite-export", "SQLite ↔ Excel", "数据库查询结果导出为 Excel 报表。",
        '''"""SQLite → Excel：查询结果报表化。"""
import sqlite3
from openpyxl import Workbook

conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE sales (dept TEXT, month TEXT, amount REAL)")
conn.executemany("INSERT INTO sales VALUES (?, ?, ?)",
                 [("研发", "1月", 120), ("研发", "2月", 135), ("市场", "1月", 90)])
conn.commit()

wb = Workbook()
ws = wb.active
cols = [d[0] for d in conn.execute("SELECT * FROM sales LIMIT 0").description]
ws.append(cols)
for row in conn.execute("SELECT * FROM sales ORDER BY amount DESC"):
    ws.append(row)
wb.save("数据库报表.xlsx")
print("数据库查询已导出为 数据库报表.xlsx")
''')
    return c.save()


if __name__ == "__main__":
    main()
