"""磁盘仪表：分区使用率进度条。"""
import psutil

for part in psutil.disk_partitions():
    try:
        u = psutil.disk_usage(part.mountpoint)
    except PermissionError:
        continue
    pct = u.percent / 100
    bar = "█" * int(pct * 24) + "░" * (24 - int(pct * 24))
    warn = " ⚠️" if u.percent > 90 else ""
    print(f"{part.mountpoint:<14} {bar} {u.percent:5.1f}%  "
          f"剩余 {u.free / 1024**3:.0f}GB/{u.total / 1024**3:.0f}GB{warn}")
