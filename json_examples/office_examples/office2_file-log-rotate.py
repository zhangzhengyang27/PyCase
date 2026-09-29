"""日志轮转：超过阈值切分为 .1/.2 文件。"""
from pathlib import Path

log = Path("app.log")
log.write_text("\n".join(f"line {i}" for i in range(100)), encoding="utf-8")

MAX_BYTES = 400
if log.exists() and log.stat().st_size > MAX_BYTES:
    content = log.read_text(encoding="utf-8").splitlines(keepends=True)
    part, idx = [], 1
    size = 0
    for ln in content:
        if size + len(ln) > MAX_BYTES:
            Path(f"app.log.{idx}").write_text("".join(part), encoding="utf-8")
            part, size, idx = [], 0, idx + 1
        part.append(ln)
        size += len(ln)
    if part:
        Path(f"app.log.{idx}").write_text("".join(part), encoding="utf-8")
    log.unlink()
    print(f"已切分为 {idx} 个文件")
