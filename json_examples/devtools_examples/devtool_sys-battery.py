"""电池状态：电量与预估续航。"""
import psutil

bat = psutil.sensors_battery()
if bat is None:
    print("未检测到电池（台式机）")
else:
    plug = "充电中 ⚡" if bat.power_plugged else "电池供电"
    print(f"电量 {bat.percent:.0f}%  {plug}")
    if bat.secsleft and bat.secsleft != psutil.POWER_TIME_UNLIMITED and bat.secsleft > 0:
        h, m = divmod(bat.secsleft // 60, 60)
        print(f"预估剩余 {h}小时{m}分钟")
