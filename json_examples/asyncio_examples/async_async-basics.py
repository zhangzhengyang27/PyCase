"""（并发实验室生成脚本：stdlib asyncio，离线可跑，有限轮次收尾）"""
import asyncio
import time

# ---- 类型：async/await 入门 ----
n = 3

async def job(i):
    await asyncio.sleep(0.3)
    return f"任务{i} 完成"

async def main():
    t0 = time.monotonic()
    for i in range(n):
        await job(i)
    seq = time.monotonic() - t0
    t0 = time.monotonic()
    results = await asyncio.gather(*(job(i) for i in range(n)))
    par = time.monotonic() - t0
    print("顺序:", results[0], "…耗时 %.2fs" % seq)
    print("并发:", results, "耗时 %.2fs" % par)
    print(f"提速约 {seq / par:.1f} 倍（IO 等待重叠）")

asyncio.run(main())
