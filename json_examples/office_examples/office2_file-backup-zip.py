"""目录备份：zip 打包 + 时间戳命名。"""
import zipfile
from datetime import datetime
from pathlib import Path

src = Path(".")
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
dest = Path(f"backup_{stamp}.zip")
with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
    for p in src.rglob("*"):
        if p.is_file() and "backup_" not in p.name and ".venv" not in p.parts:
            zf.write(p, p.relative_to(src))
print(f"备份完成: {dest.name} ({dest.stat().st_size // 1024} KB)")
