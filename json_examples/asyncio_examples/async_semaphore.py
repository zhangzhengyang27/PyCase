"""（并发实验室生成脚本：stdlib asyncio，离线可跑，有限轮次收尾）"""
import asyncio
import time

# ---- 类型：信号量限并发 ----
limit = 2
sem = asyncio.Semaphore(limit)
ACTIVE = {"n": 0}
PEAK = {"n": 0}

async def fetch(i):
    async with sem:
        ACTIVE["n"] += 1
        PEAK["n"] = max(PEAK["n"], ACTIVE["n"])
        await asyncio.sleep(0.2)
        ACTIVE["n"] -= 1
        return i

async def main():
    await asyncio.gather(*(fetch(i) for i in range(6)))
    print(f"6 个任务、并发上限 {limit} → 实测同时运行峰值 {PEAK['n']}")

asyncio.run(main())
