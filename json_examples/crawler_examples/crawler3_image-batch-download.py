"""图片批量下载：内容类型决定扩展名。"""
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
