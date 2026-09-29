"""目录报告：子目录体积排行。"""
from pathlib import Path

def dir_size(d: Path) -> int:
    return sum(f.stat().st_size for f in d.rglob("*") if f.is_file())

base = Path(".")
sizes = [(dir_size(d), d.name) for d in base.iterdir() if d.is_dir()]
for size, name in sorted(sizes, reverse=True)[:10]:
    print(f"{size / 1024 / 1024:8.2f} MB  {name}")
