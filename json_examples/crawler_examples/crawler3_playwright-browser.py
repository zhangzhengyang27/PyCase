"""Playwright：JS 渲染页面的抓取（需 pip install playwright && playwright install chromium）。"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://example.com", wait_until="domcontentloaded")
    print("标题:", page.title())
    page.screenshot(path="page.png", full_page=True)
    browser.close()
print("截图已保存 page.png（本机未装浏览器时此脚本报缺依赖，属正常）")
