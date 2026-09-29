"""流式下载：逐块写入，适合大文件。"""
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
