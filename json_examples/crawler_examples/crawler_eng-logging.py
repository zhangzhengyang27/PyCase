"""日志：控制台 + 文件双输出。"""
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
