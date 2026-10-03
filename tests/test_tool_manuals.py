"""工具手册生成器守卫（W7 手册页基座）。

钉两件事：
1. 覆盖率——除显式排除（已有交互页 15 + 页面化反而更差 4）外，
   每个 category=tools 条目都必须有手册（"剩余工具全部有页面"的底线）；
2. 新鲜度——仓库内 tool-manuals.json 与重新生成的结果逐字节一致（防手改漂移）。
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "electron-prototype/electron/src/renderer/src/tool-manuals.json"
GENERATOR = ROOT / "scripts/gen_tool_manuals.py"

EXCLUDED_TITLES = {
    # 已有交互页（CLI 与交互页并存）
    "正则测试器", "JSON 格式化校验", "JSON → dataclass", "CSV ↔ JSON 互转",
    "时间戳转换器", "UUID/短 ID 生成器", "颜色转换器", "科学单位换算", "密码强度检查",
    "CSV ↔ Excel 互转", "PDF 文本提取", "图片转 PDF", "图片批量水印", "密码生成器",
    "图片批量压缩",
    # W14 终局补齐（交互页面即文档）
    "哈希校验器", "网页正文提取", "统一压缩解压器", "临时文件清理器", "目录打包备份",
    "日志轮转", "目录同步器", "敏感文件粉碎器", "Word 插入图片", "PPT 数据表", "花销记账本",
    # 页面化反而更差
    "本地密码保险库", "命令行番茄钟", "文件变更监听", "站点可用性监控",
}


def _expected_ids() -> set[str]:
    ids: set[str] = set()
    for p in (ROOT / "json_examples").glob("*.json"):
        if p.name == "facts.json":
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        for e in data.get("examples", []):
            if e.get("category") != "tools":
                continue
            if (e.get("title") or "") in EXCLUDED_TITLES:
                continue
            ids.add(e["id"])
    return ids


def test_manuals_cover_all_non_excluded_tools():
    data = json.loads(OUT.read_text(encoding="utf-8"))
    manuals = data["manuals"]
    expected = _expected_ids()
    missing = expected - set(manuals)
    assert not missing, f"缺手册 {len(missing)} 份，如 {sorted(missing)[:5]}——重跑 scripts/gen_tool_manuals.py"
    extra = set(manuals) - expected
    assert not extra, f"多出手册 {len(extra)} 份（排除表与生成器不同步），如 {sorted(extra)[:5]}"


def test_manuals_file_is_fresh():
    before = OUT.read_bytes()
    subprocess.run([sys.executable, str(GENERATOR)], check=True, capture_output=True)
    after = OUT.read_bytes()
    assert before == after, "tool-manuals.json 与生成器输出不一致（被手改或生成器已更新）——重跑 scripts/gen_tool_manuals.py"


def test_manual_entries_have_required_fields():
    data = json.loads(OUT.read_text(encoding="utf-8"))
    for mid, m in list(data["manuals"].items())[:5]:
        assert m["title"].strip(), mid
        assert m["summary"].strip(), mid
        assert m["usage"].strip(), mid
        assert isinstance(m["params"], list), mid
