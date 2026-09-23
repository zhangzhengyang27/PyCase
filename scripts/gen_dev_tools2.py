#!/usr/bin/env python3
"""实用工具箱·第二辑：图片批处理（Pillow）+ 音视频（ffmpeg 封装）。

ffmpeg 类工具运行前自动探测系统 ffmpeg/ffprobe 可执行文件，支持 --dry-run
预览命令行；图片类全部 Pillow 实现、自包含可运行。
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "json_examples"


class Collection:
    def __init__(self, file: str, merge: bool = True):
        self.file = file
        self.examples = []
        self.seen_code = set()
        self.seen_id = set()
        existing = OUT_DIR / file
        if merge and existing.exists():
            for e in json.load(open(existing, encoding="utf-8")).get("examples", []):
                self.seen_id.add(e["id"])
                self.seen_code.add(hashlib.md5(e["code"].encode()).hexdigest())
                self.examples.append(e)

    def add(self, example_id, name, title, description, tags, requirements, code, category="tools"):
        code = code.strip() + "\n"
        h = hashlib.md5(code.encode()).hexdigest()
        if h in self.seen_code or example_id in self.seen_id:
            return False
        self.seen_code.add(h)
        self.seen_id.add(example_id)
        self.examples.append({"id": example_id, "name": name, "category": category,
                              "tags": tags, "title": title, "description": description,
                              "requirements": requirements, "code": code})
        return True

    def save(self):
        with open(OUT_DIR / self.file, "w", encoding="utf-8") as f:
            json.dump({"examples": self.examples}, f, ensure_ascii=False, indent=1)
        return len(self.examples)


def build_image_tools():
    c = Collection("devtools_examples.json")

    def add(pid, title, desc, code, tags=("图片", "批处理"), reqs=("pillow",)):
        c.add(f"tools_img2-{pid}", f"imgtool2_{pid}.py", title, desc, list(tags), list(reqs), code)

    add("batch-resize", "批量缩放", "长边等比缩放到指定上限，输出到子目录。",
        '''"""批量缩放：python xxx.py <目录> --max-side 1600"""
import argparse
from pathlib import Path

from PIL import Image

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--max-side", type=int, default=1600)
    ap.add_argument("--quality", type=int, default=85)
    args = ap.parse_args()

    out = Path(args.directory) / "resized"
    out.mkdir(exist_ok=True)
    for p in sorted(Path(args.directory).iterdir()):
        if p.suffix.lower() not in SUPPORTED or not p.is_file():
            continue
        with Image.open(p) as im:
            im = im.convert("RGB")
            scale = min(1.0, args.max_side / max(im.size))
            if scale < 1.0:
                im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
            dest = out / (p.stem + ".jpg")
            im.save(dest, "JPEG", quality=args.quality, optimize=True)
        print(f"{p.name} -> {dest.name} ({im.size[0]}×{im.size[1]})")


if __name__ == "__main__":
    main()
''')
    add("batch-convert", "批量格式转换", "PNG/JPEG/WEBP 任意方向批量互转。",
        '''"""格式转换：python xxx.py <目录> --to webp"""
import argparse
from pathlib import Path

from PIL import Image

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--to", choices=["png", "jpg", "webp"], default="webp")
    ap.add_argument("--quality", type=int, default=85)
    args = ap.parse_args()
    fmt = "JPEG" if args.to in ("jpg", "jpeg") else args.to.upper()

    for p in sorted(Path(args.directory).iterdir()):
        if p.suffix.lower() not in SUPPORTED or not p.is_file():
            continue
        with Image.open(p) as im:
            im = im.convert("RGB") if fmt == "JPEG" else im
            dest = p.with_suffix("." + args.to)
            im.save(dest, fmt, quality=args.quality)
        print(f"{p.name} -> {dest.name}")


if __name__ == "__main__":
    main()
''')
    add("batch-crop-ratio", "批量裁剪比例", "居中裁剪到目标宽高比（16:9 / 1:1 / 4:3）。",
        '''"""比例裁剪：python xxx.py <目录> --ratio 16:9"""
import argparse
from pathlib import Path

from PIL import Image

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp"}


def center_crop(im, rw, rh):
    target = rw / rh
    w, h = im.size
    cur = w / h
    if cur > target:  # 太宽，裁左右
        new_w = int(h * target)
        box = ((w - new_w) // 2, 0, (w + new_w) // 2, h)
    else:             # 太高，裁上下
        new_h = int(w / target)
        box = (0, (h - new_h) // 2, w, (h + new_h) // 2)
    return im.crop(box)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--ratio", default="16:9")
    args = ap.parse_args()
    rw, rh = (int(x) for x in args.ratio.split(":"))

    out = Path(args.directory) / "cropped"
    out.mkdir(exist_ok=True)
    for p in sorted(Path(args.directory).iterdir()):
        if p.suffix.lower() not in SUPPORTED or not p.is_file():
            continue
        with Image.open(p) as im:
            cropped = center_crop(im.convert("RGB"), rw, rh)
            dest = out / (p.stem + ".jpg")
            cropped.save(dest, "JPEG", quality=88)
        print(f"{p.name} -> {dest.name} {cropped.size}")


if __name__ == "__main__":
    main()
''')
    add("contact-sheet", "缩略图拼贴", "目录图片自动拼成 N 列 contact sheet（素材预览墙）。",
        '''"""拼贴墙：python xxx.py <目录> --cols 4 --cell 240"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--cell", type=int, default=240)
    ap.add_argument("-o", default="contact_sheet.jpg")
    args = ap.parse_args()

    imgs = []
    for p in sorted(Path(args.directory).iterdir()):
        if p.suffix.lower() in SUPPORTED and p.is_file():
            im = Image.open(p).convert("RGB")
            im.thumbnail((args.cell, args.cell))
            imgs.append((p.name, im))
    if not imgs:
        print("无图片")
        return
    rows = (len(imgs) + args.cols - 1) // args.cols
    sheet = Image.new("RGB", (args.cols * (args.cell + 8) + 8, rows * (args.cell + 26) + 8), "#181c24")
    d = ImageDraw.Draw(sheet)
    for i, (name, im) in enumerate(imgs):
        x = 8 + (i % args.cols) * (args.cell + 8)
        y = 8 + (i // args.cols) * (args.cell + 26)
        sheet.paste(im, (x + (args.cell - im.width) // 2, y + (args.cell - im.height) // 2))
        d.text((x, y + args.cell + 4), name[:28], fill="#cfd8e3")
    sheet.save(args.o, quality=88)
    print(f"拼贴 {len(imgs)} 张 -> {args.o}")


if __name__ == "__main__":
    main()
''')
    add("batch-watermark", "批量水印", "文字水印平铺到目录内全部图片（右下角或平铺）。",
        '''"""批量水印：python xxx.py <目录> --text '© 2026' --mode corner|tile"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--text", default="© 示例库")
    ap.add_argument("--mode", choices=["corner", "tile"], default="corner")
    ap.add_argument("--opacity", type=int, default=110)
    args = ap.parse_args()

    out = Path(args.directory) / "watermarked"
    out.mkdir(exist_ok=True)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 22)
    except OSError:
        font = ImageFont.load_default()

    for p in sorted(Path(args.directory).iterdir()):
        if p.suffix.lower() not in SUPPORTED or not p.is_file():
            continue
        base = Image.open(p).convert("RGBA")
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        if args.mode == "corner":
            d.text((base.width - 130, base.height - 40), args.text,
                   fill=(255, 255, 255, args.opacity), font=font)
        else:
            for y in range(0, base.height, 90):
                for x in range(0, base.width, 200):
                    d.text((x, y), args.text, fill=(255, 255, 255, args.opacity), font=font)
        result = Image.alpha_composite(base, layer).convert("RGB")
        dest = out / p.name
        result.save(dest, quality=90)
        print(f"{p.name} -> {dest.name}")


if __name__ == "__main__":
    main()
''')
    add("dominant-color", "主色调提取", "缩图量化取主色，输出 HEX 色板。",
        '''"""主色调：缩图 + 量化取出现最多的颜色。"""
import argparse
from PIL import Image

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--top", type=int, default=5)
    args = ap.parse_args()
    im = Image.open(args.image).convert("RGB")
    im.thumbnail((80, 80))
    counts = {}
    for px in im.getdata():
        quant = (px[0] // 16 * 16, px[1] // 16 * 16, px[2] // 16 * 16)
        counts[quant] = counts.get(quant, 0) + 1
    total = sum(counts.values())
    for (r, g, b), n in sorted(counts.items(), key=lambda x: -x[1])[:args.top]:
        print(f"#{r:02x}{g:02x}{b:02x}  {100 * n / total:5.1f}%  {'█' * int(100 * n / total / 4)}")


if __name__ == "__main__":
    main()
''')
    add("gif-extract", "GIF 帧提取", "把 GIF 逐帧导出为 PNG 序列。",
        '''"""GIF 拆帧：python xxx.py anim.gif -o frames"""
import argparse
from pathlib import Path

from PIL import Image, ImageSequence


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gif")
    ap.add_argument("-o", default="frames")
    args = ap.parse_args()
    out = Path(args.o)
    out.mkdir(exist_ok=True)
    with Image.open(args.gif) as im:
        for i, frame in enumerate(ImageSequence.Iterator(im)):
            frame.convert("RGB").save(out / f"frame_{i:03d}.png")
    print(f"已导出 {i + 1} 帧 -> {out}")


if __name__ == "__main__":
    main()
''')
    add("gif-compose", "图片合成 GIF", "PNG 序列合成动图（可调帧率与循环）。",
        '''"""合成 GIF：python xxx.py frame_*.png 所在目录 -o out.gif --fps 8"""
import argparse
from pathlib import Path

from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("-o", default="out.gif")
    ap.add_argument("--fps", type=int, default=8)
    ap.add_argument("--width", type=int, default=480)
    args = ap.parse_args()
    frames = []
    for p in sorted(Path(args.directory).glob("*.png")):
        im = Image.open(p).convert("RGB")
        scale = args.width / im.width
        frames.append(im.resize((args.width, int(im.height * scale))))
    if not frames:
        print("无 PNG 帧")
        return
    duration = int(1000 / args.fps)
    frames[0].save(args.o, save_all=True, append_images=frames[1:],
                   duration=duration, loop=0)
    print(f"已合成 {len(frames)} 帧 -> {args.o}")


if __name__ == "__main__":
    main()
''')
    add("batch-enhance", "批量亮度/对比度", "增强系数可调的批量画质调整。",
        '''"""画质调整：python xxx.py <目录> --brightness 1.1 --contrast 1.15"""
import argparse
from pathlib import Path

from PIL import Image, ImageEnhance

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--brightness", type=float, default=1.0)
    ap.add_argument("--contrast", type=float, default=1.0)
    ap.add_argument("--saturation", type=float, default=1.0)
    args = ap.parse_args()

    out = Path(args.directory) / "enhanced"
    out.mkdir(exist_ok=True)
    for p in sorted(Path(args.directory).iterdir()):
        if p.suffix.lower() not in SUPPORTED or not p.is_file():
            continue
        with Image.open(p) as im:
            im = im.convert("RGB")
            if args.brightness != 1.0:
                im = ImageEnhance.Brightness(im).enhance(args.brightness)
            if args.contrast != 1.0:
                im = ImageEnhance.Contrast(im).enhance(args.contrast)
            if args.saturation != 1.0:
                im = ImageEnhance.Color(im).enhance(args.saturation)
            dest = out / p.name
            im.save(dest, quality=90)
        print(f"{p.name} -> {dest.name}")


if __name__ == "__main__":
    main()
''')
    add("img-info-report", "图片信息报告", "批量输出尺寸/格式/体积报表（素材盘点）。",
        '''"""图片报告：目录内图片尺寸/格式/体积一览。"""
import argparse
from pathlib import Path

from PIL import Image

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", nargs="?", default=".")
    args = ap.parse_args()
    total = 0
    print(f"{'文件':<30}{'尺寸':<12}{'格式':<6}{'体积':>9}")
    for p in sorted(Path(args.directory).iterdir()):
        if p.suffix.lower() not in SUPPORTED or not p.is_file():
            continue
        with Image.open(p) as im:
            kb = p.stat().st_size / 1024
            total += kb
            print(f"{p.name[:28]:<30}{f'{im.width}×{im.height}':<12}{im.format:<6}{kb:>7.0f}KB")
    print(f"合计 {total:.0f} KB")


if __name__ == "__main__":
    main()
''')
    add("rounded-border", "圆角与边框", "批量加圆角/描边（头像处理常用）。",
        '''"""圆角边框：python xxx.py <目录> --radius 24 --border 3"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp"}


def rounded(im, radius):
    mask = Image.new("L", im.size, 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=radius, fill=255)
    out = Image.new("RGBA", im.size)
    out.paste(im, (0, 0), mask)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--radius", type=int, default=24)
    ap.add_argument("--border", type=int, default=0)
    args = ap.parse_args()
    out = Path(args.directory) / "styled"
    out.mkdir(exist_ok=True)
    for p in sorted(Path(args.directory).iterdir()):
        if p.suffix.lower() not in SUPPORTED or not p.is_file():
            continue
        with Image.open(p) as im:
            im = rounded(im.convert("RGB"), args.radius)
            if args.border:
                d = ImageDraw.Draw(im)
                d.rounded_rectangle([0, 0, im.width - 1, im.height - 1],
                                    radius=args.radius, outline="#ffffff", width=args.border)
            dest = out / (p.stem + ".png")
            im.save(dest)
        print(f"{p.name} -> {dest.name}")


if __name__ == "__main__":
    main()
''')
    return c.save()


def build_media_tools():
    c = Collection("devtools_examples.json")

    def add(pid, title, desc, code, tags=("音视频", "ffmpeg")):
        c.add(f"tools_media-{pid}", f"media_{pid}.py", title, desc, list(tags), ["ffmpeg"], code)

    ffmpeg_guard = '''import shutil
import subprocess
import sys

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")
if not FFMPEG:
    print("未找到 ffmpeg（brew install ffmpeg / apt install ffmpeg）")
    sys.exit(1)
'''
    probe_fn = '''
def probe(path):
    """ffprobe 取时长/码率/分辨率（JSON）。"""
    r = subprocess.run(
        [FFPROBE, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True)
    import json as _json
    return _json.loads(r.stdout or "{}")
'''

    add("media-probe", "媒体信息探测", "ffprobe JSON 解析：时长/分辨率/编码/码率。",
        ffmpeg_guard + probe_fn + '''

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("media", nargs="+")
    args = ap.parse_args()
    for path in args.media:
        info = probe(path)
        fmt = info.get("format", {})
        v = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
        print(f"{path}")
        print(f"  时长 {float(fmt.get('duration', 0)):.1f}s | "
              f"{v.get('width', '?')}×{v.get('height', '?')} | "
              f"{v.get('codec_name', '?')} | {int(fmt.get('bit_rate', 0)) // 1024} kbps")


if __name__ == "__main__":
    main()
''')
    add("media-convert", "视频格式转换", "任意输入 → mp4 (H.264+AAC)，兼容性优先。",
        '''"""格式转换：python xxx.py input.mov [-o output.mp4]"""
import argparse
from pathlib import Path

''' + ffmpeg_guard + '''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--output")
    args = ap.parse_args()
    src = Path(args.input)
    dest = Path(args.output or src.with_suffix(".mp4"))
    r = subprocess.run([FFMPEG, "-y", "-i", str(src),
                        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                        "-c:a", "aac", "-b:a", "128k", str(dest)],
                       capture_output=True, text=True)
    if r.returncode == 0:
        print(f"转换完成 -> {dest} ({dest.stat().st_size // 1024 // 1024} MB)")
    else:
        print("失败:", r.stderr.strip().splitlines()[-1] if r.stderr else r.returncode)


if __name__ == "__main__":
    main()
''')
    add("media-compress", "视频压缩", "CRF 质量档压缩（体积直降，画质可控）。",
        '''"""视频压缩：python xxx.py input.mp4 --crf 26 --preset fast"""
import argparse
from pathlib import Path

''' + ffmpeg_guard + '''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--crf", type=int, default=26, help="18 高质量 ~ 28 高压缩")
    ap.add_argument("--preset", default="fast")
    args = ap.parse_args()
    src = Path(args.input)
    if not src.exists():
        print("输入文件不存在:", src)
        return
    dest = src.with_name(src.stem + "_compressed.mp4")
    before = src.stat().st_size
    r = subprocess.run([FFMPEG, "-y", "-i", str(src), "-c:v", "libx264",
                        "-preset", args.preset, "-crf", str(args.crf),
                        "-c:a", "aac", "-b:a", "96k", str(dest)],
                       capture_output=True, text=True)
    if r.returncode == 0:
        after = dest.stat().st_size
        print(f"{before // 1024 // 1024} MB -> {after // 1024 // 1024} MB "
              f"（{100 - after * 100 // before}% 缩减）")
    else:
        print("失败:", r.stderr.strip().splitlines()[-1] if r.stderr else r.returncode)


if __name__ == "__main__":
    main()
''')
    add("media-extract-audio", "提取音频", "视频 → mp3/m4a 音轨抽取。",
        '''"""提取音频：python xxx.py input.mp4 -o audio.mp3"""
import argparse
from pathlib import Path

''' + ffmpeg_guard + '''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--output")
    ap.add_argument("--bitrate", default="192k")
    args = ap.parse_args()
    src = Path(args.input)
    dest = Path(args.output or src.with_suffix(".mp3"))
    r = subprocess.run([FFMPEG, "-y", "-i", str(src), "-vn",
                        "-c:a", "libmp3lame", "-b:a", args.bitrate, str(dest)],
                       capture_output=True, text=True)
    print(f"提取完成 -> {dest}（{dest.stat().st_size // 1024} KB）" if r.returncode == 0
          else "失败: " + (r.stderr.strip().splitlines()[-1] if r.stderr else str(r.returncode)))


if __name__ == "__main__":
    main()
''')
    add("media-trim", "音视频裁剪", "-ss/-t 指定起止时间裁剪片段（流复制快速模式）。",
        '''"""裁剪：python xxx.py input.mp4 --start 00:00:10 --duration 30"""
import argparse
from pathlib import Path

''' + ffmpeg_guard + '''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--start", default="00:00:00")
    ap.add_argument("--duration", type=float, default=10)
    ap.add_argument("-o", "--output")
    args = ap.parse_args()
    src = Path(args.input)
    dest = Path(args.output or src.with_name(src.stem + "_clip" + src.suffix))
    r = subprocess.run([FFMPEG, "-y", "-ss", args.start, "-i", str(src),
                        "-t", str(args.duration), "-c", "copy", str(dest)],
                       capture_output=True, text=True)
    print(f"裁剪完成 -> {dest}" if r.returncode == 0 else "失败: " + r.stderr[-120:])


if __name__ == "__main__":
    main()
''')
    add("media-volume", "音量调整", "音量倍数/归一化（loudnorm 一键拉平响度）。",
        '''"""音量：python xxx.py input.mp4 --gain 1.5 | --normalize"""
import argparse
from pathlib import Path

''' + ffmpeg_guard + '''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--gain", type=float, default=1.0, help="音量倍数")
    ap.add_argument("--normalize", action="store_true", help="loudnorm 响度归一化")
    args = ap.parse_args()
    src = Path(args.input)
    dest = src.with_name(src.stem + "_vol" + src.suffix)
    if args.normalize:
        af = "loudnorm=I=-16:TP=-1.5:LRA=11"
    else:
        af = f"volume={args.gain}"
    r = subprocess.run([FFMPEG, "-y", "-i", str(src), "-af", af,
                        "-c:v", "copy", str(dest)], capture_output=True, text=True)
    print(f"完成 -> {dest}" if r.returncode == 0 else "失败: " + r.stderr[-120:])


if __name__ == "__main__":
    main()
''')
    add("media-screenshot", "视频截图", "指定时间取帧 / 每 N 秒批量截帧。",
        '''"""截图：单帧 --at 00:00:30，或 --every 5 批量截帧。"""
import argparse
from pathlib import Path

''' + ffmpeg_guard + '''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--at", default="00:00:05", help="单帧时间点")
    ap.add_argument("--every", type=float, default=0, help="每 N 秒一帧（批量模式）")
    ap.add_argument("-o", default="frame.png")
    args = ap.parse_args()
    if args.every > 0:
        r = subprocess.run([FFMPEG, "-y", "-i", args.input, "-vf",
                            f"fps=1/{args.every}", "shot_%03d.png"], capture_output=True, text=True)
        print("批量截帧完成" if r.returncode == 0 else "失败")
    else:
        r = subprocess.run([FFMPEG, "-y", "-ss", args.at, "-i", args.input,
                            "-frames:v", "1", args.o], capture_output=True, text=True)
        print(f"截图 -> {args.o}" if r.returncode == 0 else "失败")


if __name__ == "__main__":
    main()
''')
    add("media-concat", "视频合并", "concat 协议/解复用器顺序拼接多段视频。",
        '''"""合并：python xxx.py a.mp4 b.mp4 c.mp4 -o merged.mp4"""
import argparse
from pathlib import Path

''' + ffmpeg_guard + '''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("-o", default="merged.mp4")
    args = ap.parse_args()
    if len(args.inputs) < 2:
        print("至少两个输入")
        return
    import tempfile
    lst = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
    for p in args.inputs:
        lst.write(f"file '{Path(p).resolve()}'\\n")
    lst.close()
    r = subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0",
                        "-i", lst.name, "-c", "copy", args.o],
                       capture_output=True, text=True)
    Path(lst.name).unlink()
    print(f"合并 {len(args.inputs)} 段 -> {args.o}" if r.returncode == 0 else "失败（编码不一致时先统一转码）")


if __name__ == "__main__":
    main()
''')
    add("media-strip-audio", "去除音轨", "-an 静音视频（素材交付常用）。",
        '''"""去音轨：python xxx.py input.mp4"""
import argparse
from pathlib import Path

''' + ffmpeg_guard + '''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    args = ap.parse_args()
    src = Path(args.input)
    dest = src.with_name(src.stem + "_mute" + src.suffix)
    r = subprocess.run([FFMPEG, "-y", "-i", str(src), "-an", "-c:v", "copy", str(dest)],
                       capture_output=True, text=True)
    print(f"静音版 -> {dest}" if r.returncode == 0 else "失败")


if __name__ == "__main__":
    main()
''')
    add("media-audio-compress", "音频压缩转码", "mp3/m4a 码率压缩（语音 64k / 音乐 128k 建议）。",
        '''"""音频压缩：python xxx.py input.wav --bitrate 96k"""
import argparse
from pathlib import Path

''' + ffmpeg_guard + '''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--bitrate", default="128k")
    ap.add_argument("--codec", choices=["libmp3lame", "aac", "opus"], default="libmp3lame")
    args = ap.parse_args()
    src = Path(args.input)
    ext = {"libmp3lame": ".mp3", "aac": ".m4a", "opus": ".opus"}[args.codec]
    dest = src.with_name(src.stem + "_small" + ext)
    before = src.stat().st_size // 1024
    r = subprocess.run([FFMPEG, "-y", "-i", str(src), "-c:a", args.codec,
                        "-b:a", args.bitrate, str(dest)], capture_output=True, text=True)
    after = dest.stat().st_size // 1024 if dest.exists() else 0
    print(f"{before} KB -> {after} KB ({dest.name})" if r.returncode == 0 else "失败")


if __name__ == "__main__":
    main()
''')
    add("media-batch-convert", "批量转码", "目录内全部视频批量转 mp4（多线程进度）。",
        '''"""批量转码：python xxx.py <目录> --crf 24"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

''' + ffmpeg_guard + '''

def convert(p, crf):
    dest = p.with_suffix(".mp4")
    if dest.exists():
        return f"跳过（已存在）: {dest.name}"
    r = subprocess.run([FFMPEG, "-y", "-i", str(p), "-c:v", "libx264",
                        "-crf", str(crf), "-c:a", "aac", str(dest)],
                       capture_output=True, text=True)
    return f"{'✓' if r.returncode == 0 else '✗'} {p.name} -> {dest.name}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--crf", type=int, default=24)
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()
    videos = [p for p in Path(args.directory).iterdir()
              if p.suffix.lower() in {".mov", ".avi", ".mkv", ".webm", ".flv"} and p.is_file()]
    with ThreadPoolExecutor(args.workers) as pool:
        for line in pool.map(lambda p: convert(p, args.crf), videos):
            print(line)


if __name__ == "__main__":
    main()
''')
    add("media-gif", "视频转 GIF", "视频片段 → 表情包 GIF（fps/宽度可调）。",
        '''"""视频转 GIF：python xxx.py clip.mp4 --start 5 --duration 3 --width 480"""
import argparse
from pathlib import Path

''' + ffmpeg_guard + '''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--start", type=float, default=0)
    ap.add_argument("--duration", type=float, default=3)
    ap.add_argument("--width", type=int, default=480)
    ap.add_argument("--fps", type=int, default=12)
    ap.add_argument("-o", default="out.gif")
    args = ap.parse_args()
    vf = (f"fps={args.fps},scale={args.width}:-1:flags=lanczos,"
          "split[a][b];[a]palettegen[p];[b][p]paletteuse")
    r = subprocess.run([FFMPEG, "-y", "-ss", str(args.start), "-t", str(args.duration),
                        "-i", args.input, "-vf", vf, args.o], capture_output=True, text=True)
    if r.returncode == 0:
        size = Path(args.o).stat().st_size // 1024
        print(f"已生成 {args.o}（{size} KB）")
    else:
        print("失败:", r.stderr[-120:])


if __name__ == "__main__":
    main()
''')
    return c.save()
