"""系统报告：平台/硬件/Python 环境。"""
import platform
import sys

import psutil

print("系统:", platform.platform())
print("主机名:", platform.node())
print("CPU:", platform.machine(), psutil.cpu_count(logical=True), "逻辑核")
mem = psutil.virtual_memory()
print(f"内存: {mem.total / 1024**3:.0f}GB（可用 {mem.available / 1024**3:.1f}GB）")
disk = psutil.disk_usage("/")
print(f"根盘: {disk.total / 1024**3:.0f}GB（已用 {disk.percent:.0f}%）")
print("Python:", sys.version.split()[0], "@", sys.executable)
