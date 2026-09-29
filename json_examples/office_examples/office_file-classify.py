"""文件分类：图片/文档/压缩包/其他 四类归档。"""
import shutil
from pathlib import Path

RULES = {
    "图片": {".jpg", ".png", ".gif", ".webp"},
    "文档": {".docx", ".pdf", ".md", ".txt", ".xlsx"},
    "压缩包": {".zip", ".7z"},
}
base = Path(".")
for p in list(base.iterdir()):
    if not p.is_file():
        continue
    folder = next((name for name, exts in RULES.items() if p.suffix in exts), "其他")
    dest = base / folder
    dest.mkdir(exist_ok=True)
    shutil.move(str(p), dest / p.name)
    print(f"{p.name} -> {folder}/")
