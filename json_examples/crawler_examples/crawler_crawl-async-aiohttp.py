"""异步抓取：aiohttp 协程并发（asyncio 入门实战）。"""
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
