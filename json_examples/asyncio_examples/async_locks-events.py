"""（并发实验室生成脚本：stdlib asyncio，离线可跑，有限轮次收尾）"""
import asyncio
import time

# ---- 类型：锁与事件 ----
n = 4
counter = {"value": 0}
lock = asyncio.Lock()
event = asyncio.Event()

async def worker(i):
    for _ in range(100):
        async with lock:
            counter["value"] += 1
    print(f"worker{i} 完成")
    if i == n - 1:
        event.set()

async def main():
    await asyncio.gather(*(worker(i) for i in range(n)))
    await event.wait()
    print(f"加锁保护后计数无损: {counter['value']}（期望 {n * 100}）")

asyncio.run(main())
