"""（并发实验室生成脚本：stdlib asyncio，离线可跑，有限轮次收尾）"""
import asyncio
import time

# ---- 类型：生产者消费者 ----
producers_n = 2
nc = 2
queue = asyncio.Queue()
DONE = []

async def producer(pid):
    for i in range(3):
        await queue.put(f"p{pid}-任务{i}")

async def consumer(cid):
    while True:
        item = await queue.get()
        await asyncio.sleep(0.1)
        DONE.append(f"消费者{cid}:{item}")
        queue.task_done()

async def main():
    producers = [asyncio.create_task(producer(p)) for p in range(producers_n)]
    consumers = [asyncio.create_task(consumer(c)) for c in range(nc)]
    await asyncio.gather(*producers)
    await queue.join()
    for c in consumers:
        c.cancel()
    print(f"{producers_n} 生产者 × 3 任务 → {nc} 消费者共处理 {len(DONE)} 件:")
    print(DONE)

asyncio.run(main())
