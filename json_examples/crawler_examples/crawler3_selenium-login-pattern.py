"""Selenium：显式等待的登录流程骨架。"""
# 需 pip install selenium 并配置浏览器驱动
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

print("""Selenium 登录骨架（伪代码演示，实际需浏览器环境）:
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)
    driver.get("https://example.com/login")
    wait.until(lambda d: d.find_element(By.ID, "username")).send_keys("user")
    driver.find_element(By.ID, "password").send_keys("pass")
    driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
    cookies = driver.get_cookies()   # 导出后供 requests 会话使用
""")
