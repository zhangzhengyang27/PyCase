"""优雅退出：Ctrl+C 不丢已抓数据。"""
import sys
import time

items = []

def save():
    print(f"落盘 {len(items)} 条已抓数据")

def main():
    try:
        for i in range(10):
            items.append(f"条目{i}")
            time.sleep(0.2)
            if i == 2:
                raise KeyboardInterrupt  # 模拟 Ctrl+C
    except KeyboardInterrupt:
        print("收到中断信号")
    finally:
        save()
        sys.exit(0)

main()
