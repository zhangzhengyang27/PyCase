"""（并发实验室生成脚本：stdlib asyncio，离线可跑，有限轮次收尾）"""
import asyncio
import time

# ---- 类型：任务取消与异常 ----
async def worker():
    try:
        await asyncio.sleep(10)
    except asyncio.CancelledError:
        print("worker 收到取消信号，做清理")
        raise

async def failing():
    await asyncio.sleep(0.05)
    raise RuntimeError("业务异常")

async def main():
    t = asyncio.create_task(worker())
    await asyncio.sleep(0.1)
    t.cancel()
    try:
        await t
    except asyncio.CancelledError:
        print("任务已取消")
    try:
        await failing()
    except RuntimeError as e:
        print("捕获任务异常:", e)

asyncio.run(main())
