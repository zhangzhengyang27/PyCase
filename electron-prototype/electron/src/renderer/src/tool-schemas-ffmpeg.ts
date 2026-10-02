// tool-schemas-ffmpeg.ts：W11 命令构建器 ×11（媒体处理；需要本机安装 ffmpeg/ffprobe）。
// 形态：file/dir 字段 + 参数 UI → 生成并运行 ffmpeg 命令；产物留在运行工作区，
// 结果 JSON 报告输出文件名与体积（视频/音频二进制暂不在抽屉预览，见规划 §8.3）。
import type { InteractiveToolSchema } from './interactive-tools'

const str = (v: unknown): string => String(v ?? '')
const FILE_FIELD = (label: string) => ({
  key: 'file',
  label,
  type: 'file' as const,
  required: true,
  accept: ['mp4', 'mov', 'mkv', 'avi', 'mp3', 'm4a', 'wav']
})

/** 产物 JSON + ffmpeg 探测的公共收尾 */
const FOOT = (outVar: string): string => `import json
import os

import shutil
import subprocess

FF = shutil.which("ffmpeg")
if not FF:
    raise SystemExit("未找到 ffmpeg（brew install ffmpeg / apt install ffmpeg）")
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print(r.stderr[-800:])
    raise SystemExit("ffmpeg 运行失败（详见上方日志）")
size = os.path.getsize(${outVar}) / 1024 / 1024
print("<<<JSON>>>")
print(json.dumps({"rows": [{"label": "产物", "value": ${outVar}, "copy": True},
                           {"label": "体积", "value": f"{size:.1f} MB"}]}, ensure_ascii=False))
print("<<<END>>>")
`

const MEDIA_NOTE = '（需本机安装 ffmpeg）'

// ---------------------------------------------------------------------------
// 1. 视频压缩（CRF 质量档 + preset）
// ---------------------------------------------------------------------------
export const videoCompressSchema: InteractiveToolSchema = {
  id: 'interactive:video-compress',
  title: '视频压缩',
  description: `CRF 质量档压缩 H.264${MEDIA_NOTE}：18 高质量 ~ 28 高压缩，产物留在运行工作区。`,
  tags: ['媒体', '构建器'],
  fields: [
    FILE_FIELD('视频文件'),
    { key: 'crf', label: '质量 CRF', type: 'number', default: 26, width: 'half', help: '18 高 ~ 28 压' },
    {
      key: 'preset',
      label: '速度档',
      type: 'select',
      default: 'fast',
      width: 'half',
      options: ['fast', 'medium', 'slow'].map((p) => ({ value: p, label: p }))
    }
  ],
  computeVia: 'sidecar',
  compute: (v) => {
    if (!str(v.file)) return { error: '请选择视频文件' }
    const crf = Math.trunc(Number(v.crf ?? 26))
    if (!Number.isFinite(crf) || crf < 14 || crf > 34) return { error: 'CRF 需为 14~34 的整数' }
    return {
      rows: [
        { label: '源文件', value: str(v.file), copy: true },
        { label: '参数', value: `CRF ${crf} / ${str(v.preset ?? 'fast')}` }
      ]
    }
  },
  pyCode: (v) => {
    const file = str(v.file)
    const crf = Math.trunc(Number(v.crf ?? 26))
    const preset = str(v.preset ?? 'fast')
    if (!file || !Number.isFinite(crf)) return '# 选择视频文件后自动生成代码'
    return `"""视频压缩：CRF ${crf} / ${preset}。"""
cmd = [FF, "-i", ${JSON.stringify(file)}, "-c:v", "libx264", "-crf", "${crf}", "-preset", "${preset}", "-c:a", "aac", "compressed.mp4", "-y"]
${FOOT('"compressed.mp4"')}`
  }
}

// ---------------------------------------------------------------------------
// 2. 视频格式转换（容器/编码）
// ---------------------------------------------------------------------------
export const videoConvertSchema: InteractiveToolSchema = {
  id: 'interactive:video-convert',
  title: '视频格式转换',
  description: `容器转换（mp4/mkv/webm，H.264+AAC）${MEDIA_NOTE}。`,
  tags: ['媒体', '构建器'],
  fields: [
    FILE_FIELD('视频文件'),
    {
      key: 'format',
      label: '目标容器',
      type: 'select',
      default: 'mkv',
      width: 'half',
      options: ['mp4', 'mkv', 'webm'].map((x) => ({ value: x, label: x.toUpperCase() }))
    }
  ],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.file)
      ? {
          rows: [
            { label: '源文件', value: str(v.file), copy: true },
            { label: '目标', value: str(v.format ?? 'mkv').toUpperCase() }
          ]
        }
      : { error: '请选择视频文件' },
  pyCode: (v) => {
    const file = str(v.file)
    const fmt = str(v.format ?? 'mkv')
    if (!file) return '# 选择视频文件后自动生成代码'
    const codec = fmt === 'webm' ? '"-c:v", "libvpx-vp9", "-c:a", "libopus"' : '"-c:v", "libx264", "-c:a", "aac"'
    return `"""格式转换 → ${fmt.toUpperCase()}。"""
cmd = [FF, "-i", ${JSON.stringify(file)}, ${codec}, "converted.${fmt}", "-y"]
${FOOT(`"converted.${fmt}"`)}`
  }
}

// ---------------------------------------------------------------------------
// 3. 视频合并（concat demuxer，目录内排序多段）
// ---------------------------------------------------------------------------
export const videoMergeSchema: InteractiveToolSchema = {
  id: 'interactive:video-merge',
  title: '视频合并',
  description: `目录内视频按文件名顺序无损拼接（concat demuxer，要求同编码同参数）${MEDIA_NOTE}。`,
  tags: ['媒体', '构建器'],
  fields: [{ key: 'dir', label: '视频目录（同参数多段）', type: 'dir', required: true }],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.dir) ? { rows: [{ label: '目录', value: str(v.dir), copy: true }] } : { error: '请选择视频目录' },
  pyCode: (v) => {
    const dir = str(v.dir)
    if (!dir) return '# 选择视频目录后自动生成代码'
    return `"""视频合并（concat demuxer 无损拼接）。"""
import glob

parts = sorted(glob.glob(os.path.join(${JSON.stringify(dir)}, "*.mp4")))
if len(parts) < 2:
    raise SystemExit("目录里至少要有两段 mp4")
with open("parts.txt", "w", encoding="utf-8") as f:
    for p in parts:
        f.write(f"file '{p}'\\n")
cmd = [FF, "-f", "concat", "-safe", "0", "-i", "parts.txt", "-c", "copy", "merged.mp4", "-y"]
${FOOT('"merged.mp4"')}`
  }
}

// ---------------------------------------------------------------------------
// 4. 视频转 GIF（时间段 + 帧率 + 宽度）
// ---------------------------------------------------------------------------
export const videoToGifSchema: InteractiveToolSchema = {
  id: 'interactive:video-to-gif',
  title: '视频转 GIF',
  description: `取视频片段转 GIF（fps/宽度可调，palette 优化画质）${MEDIA_NOTE}。`,
  tags: ['媒体', '构建器'],
  fields: [
    FILE_FIELD('视频文件'),
    { key: 'start', label: '起始秒', type: 'number', default: 0, width: 'half' },
    { key: 'dur', label: '时长(秒)', type: 'number', default: 5, width: 'half' },
    { key: 'fps', label: '帧率', type: 'number', default: 12, width: 'half' },
    { key: 'width', label: '宽度(px)', type: 'number', default: 480, width: 'half' }
  ],
  computeVia: 'sidecar',
  compute: (v) => {
    if (!str(v.file)) return { error: '请选择视频文件' }
    const fps = Math.trunc(Number(v.fps ?? 12))
    if (!Number.isFinite(fps) || fps < 5 || fps > 30) return { error: '帧率需为 5~30 的整数' }
    return {
      rows: [
        { label: '源文件', value: str(v.file), copy: true },
        { label: '片段', value: `${str(v.start ?? 0)}s 起 ${str(v.dur ?? 5)}s @ ${fps}fps` }
      ]
    }
  },
  pyCode: (v) => {
    const file = str(v.file)
    const start = Number(v.start ?? 0)
    const dur = Number(v.dur ?? 5)
    const fps = Number.isFinite(Number(v.fps)) ? Math.trunc(Number(v.fps)) : 12
    const width = Number.isFinite(Number(v.width)) ? Math.trunc(Number(v.width)) : 480
    if (!file) return '# 选择视频文件后自动生成代码'
    return `"""视频转 GIF（palettegen 优化）。"""
cmd = [FF, "-ss", "${Number.isFinite(start) ? start : 0}", "-t", "${Number.isFinite(dur) && dur > 0 ? dur : 5}", "-i", ${JSON.stringify(file)},
       "-vf", f"fps=${fps},scale=${width}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
       "clip.gif", "-y"]
${FOOT('"clip.gif"')}`
  }
}

// ---------------------------------------------------------------------------
// 5. 视频截图（时间点取帧）
// ---------------------------------------------------------------------------
export const videoShotSchema: InteractiveToolSchema = {
  id: 'interactive:video-shot',
  title: '视频截图',
  description: `指定时间点取一帧 PNG（产物是图片，抽屉直接预览下载）${MEDIA_NOTE}。`,
  tags: ['媒体', '构建器'],
  fields: [FILE_FIELD('视频文件'), { key: 'at', label: '时间点(秒)', type: 'number', default: 3, width: 'half' }],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.file)
      ? {
          rows: [
            { label: '源文件', value: str(v.file), copy: true },
            { label: '时间点', value: `${str(v.at ?? 3)}s` }
          ]
        }
      : { error: '请选择视频文件' },
  pyCode: (v) => {
    const file = str(v.file)
    const at = Number(v.at ?? 3)
    if (!file) return '# 选择视频文件后自动生成代码'
    return `"""视频截图。"""
cmd = [FF, "-ss", "${Number.isFinite(at) && at >= 0 ? at : 3}", "-i", ${JSON.stringify(file)}, "-frames:v", "1", "shot.png", "-y"]
${FOOT('"shot.png"')}`
  }
}

// ---------------------------------------------------------------------------
// 6. 去除音轨
// ---------------------------------------------------------------------------
export const removeAudioSchema: InteractiveToolSchema = {
  id: 'interactive:remove-audio',
  title: '去除音轨',
  description: `无损去掉视频的音轨（-an，流复制不重编码）${MEDIA_NOTE}。`,
  tags: ['媒体', '构建器'],
  fields: [FILE_FIELD('视频文件')],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.file) ? { rows: [{ label: '源文件', value: str(v.file), copy: true }] } : { error: '请选择视频文件' },
  pyCode: (v) => {
    const file = str(v.file)
    if (!file) return '# 选择视频文件后自动生成代码'
    return `"""去除音轨（流复制）。"""
cmd = [FF, "-i", ${JSON.stringify(file)}, "-an", "-c:v", "copy", "muted.mp4", "-y"]
${FOOT('"muted.mp4"')}`
  }
}

// ---------------------------------------------------------------------------
// 7. 音视频裁剪（-ss/-t 流复制）
// ---------------------------------------------------------------------------
export const avTrimSchema: InteractiveToolSchema = {
  id: 'interactive:av-trim',
  title: '音视频裁剪',
  description: `按起止时间裁剪片段（流复制快速模式，起止落在关键帧附近）${MEDIA_NOTE}。`,
  tags: ['媒体', '构建器'],
  fields: [
    FILE_FIELD('音视频文件'),
    { key: 'start', label: '起始秒', type: 'number', default: 0, width: 'half' },
    { key: 'dur', label: '时长(秒)', type: 'number', default: 30, width: 'half' }
  ],
  computeVia: 'sidecar',
  compute: (v) => {
    if (!str(v.file)) return { error: '请选择音视频文件' }
    const dur = Number(v.dur ?? 30)
    if (!Number.isFinite(dur) || dur <= 0) return { error: '时长需为正数' }
    return {
      rows: [
        { label: '源文件', value: str(v.file), copy: true },
        { label: '片段', value: `${str(v.start ?? 0)}s 起 ${dur}s` }
      ]
    }
  },
  pyCode: (v) => {
    const file = str(v.file)
    const start = Number(v.start ?? 0)
    const dur = Number(v.dur ?? 30)
    if (!file) return '# 选择音视频文件后自动生成代码'
    return `"""音视频裁剪（流复制）。"""
cmd = [FF, "-ss", "${Number.isFinite(start) && start >= 0 ? start : 0}", "-i", ${JSON.stringify(file)}, "-t", "${Number.isFinite(dur) && dur > 0 ? dur : 30}", "-c", "copy", "trimmed.mp4", "-y"]
${FOOT('"trimmed.mp4"')}`
  }
}

// ---------------------------------------------------------------------------
// 8. 音量调整
// ---------------------------------------------------------------------------
export const volumeAdjustSchema: InteractiveToolSchema = {
  id: 'interactive:volume-adjust',
  title: '音量调整',
  description: `音量倍数（0.5 减半 / 1.5 增强 / 2.0 翻倍，重编码音轨）${MEDIA_NOTE}。`,
  tags: ['媒体', '构建器'],
  fields: [
    FILE_FIELD('音视频文件'),
    { key: 'vol', label: '音量倍数', type: 'number', default: 1.5, width: 'half', help: '0.1~3.0' }
  ],
  computeVia: 'sidecar',
  compute: (v) => {
    if (!str(v.file)) return { error: '请选择文件' }
    const vol = Number(v.vol ?? 1.5)
    if (!Number.isFinite(vol) || vol < 0.1 || vol > 3) return { error: '音量倍数需为 0.1~3.0' }
    return {
      rows: [
        { label: '源文件', value: str(v.file), copy: true },
        { label: '音量', value: `×${vol}` }
      ]
    }
  },
  pyCode: (v) => {
    const file = str(v.file)
    const vol = Number(v.vol ?? 1.5)
    if (!file || !Number.isFinite(vol)) return '# 选择文件后自动生成代码'
    return `"""音量调整 ×${Number.isFinite(vol) && vol >= 0.1 ? vol : 1.5}。"""
cmd = [FF, "-i", ${JSON.stringify(file)}, "-af", "volume=${Number.isFinite(vol) && vol >= 0.1 ? vol : 1.5}", "-c:v", "copy", "adjusted.mp4", "-y"]
${FOOT('"adjusted.mp4"')}`
  }
}

// ---------------------------------------------------------------------------
// 9. 提取音频
// ---------------------------------------------------------------------------
export const extractAudioSchema: InteractiveToolSchema = {
  id: 'interactive:extract-audio',
  title: '提取音频',
  description: `视频 → mp3 音轨（libmp3lame 192k）${MEDIA_NOTE}。`,
  tags: ['媒体', '构建器'],
  fields: [FILE_FIELD('视频文件')],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.file) ? { rows: [{ label: '源文件', value: str(v.file), copy: true }] } : { error: '请选择视频文件' },
  pyCode: (v) => {
    const file = str(v.file)
    if (!file) return '# 选择视频文件后自动生成代码'
    return `"""提取音频 → mp3。"""
cmd = [FF, "-i", ${JSON.stringify(file)}, "-vn", "-c:a", "libmp3lame", "-b:a", "192k", "audio.mp3", "-y"]
${FOOT('"audio.mp3"')}`
  }
}

// ---------------------------------------------------------------------------
// 10. 音频压缩转码
// ---------------------------------------------------------------------------
export const audioCompressSchema: InteractiveToolSchema = {
  id: 'interactive:audio-compress',
  title: '音频压缩转码',
  description: `音频转 AAC/MP3（码率可选）${MEDIA_NOTE}。`,
  tags: ['媒体', '构建器'],
  fields: [
    FILE_FIELD('音频文件'),
    {
      key: 'format',
      label: '目标格式',
      type: 'select',
      default: 'm4a',
      width: 'half',
      options: [
        { value: 'm4a', label: 'AAC（m4a）' },
        { value: 'mp3', label: 'MP3' }
      ]
    },
    { key: 'bitrate', label: '码率 kbps', type: 'number', default: 128, width: 'half' }
  ],
  computeVia: 'sidecar',
  compute: (v) => {
    if (!str(v.file)) return { error: '请选择音频文件' }
    const br = Math.trunc(Number(v.bitrate ?? 128))
    if (!Number.isFinite(br) || br < 32 || br > 320) return { error: '码率需为 32~320 kbps' }
    return {
      rows: [
        { label: '源文件', value: str(v.file), copy: true },
        { label: '目标', value: `${str(v.format ?? 'm4a').toUpperCase()} @ ${br}k` }
      ]
    }
  },
  pyCode: (v) => {
    const file = str(v.file)
    const fmt = str(v.format ?? 'm4a')
    const br = Number.isFinite(Number(v.bitrate)) ? Math.trunc(Number(v.bitrate)) : 128
    if (!file) return '# 选择音频文件后自动生成代码'
    const codec = fmt === 'mp3' ? '"libmp3lame"' : '"aac"'
    return `"""音频压缩转码 → ${fmt.toUpperCase()} @ ${br}k。"""
cmd = [FF, "-i", ${JSON.stringify(file)}, "-vn", "-c:a", ${codec}, "-b:a", "${br}k", "compressed.${fmt}", "-y"]
${FOOT(`"compressed.${fmt}"`)}`
  }
}

// ---------------------------------------------------------------------------
// 11. 批量转码（目录）
// ---------------------------------------------------------------------------
export const batchTranscodeSchema: InteractiveToolSchema = {
  id: 'interactive:batch-transcode',
  title: '批量转码',
  description: `目录内全部视频转 mp4（H.264+AAC，CRF 可调）${MEDIA_NOTE}。`,
  tags: ['媒体', '构建器', '批量'],
  fields: [
    { key: 'dir', label: '视频目录', type: 'dir', required: true },
    { key: 'crf', label: '质量 CRF', type: 'number', default: 26, width: 'half', help: '18 高 ~ 28 压' }
  ],
  computeVia: 'sidecar',
  compute: (v) => {
    if (!str(v.dir)) return { error: '请选择视频目录' }
    const crf = Math.trunc(Number(v.crf ?? 26))
    if (!Number.isFinite(crf) || crf < 14 || crf > 34) return { error: 'CRF 需为 14~34 的整数' }
    return {
      rows: [
        { label: '目录', value: str(v.dir), copy: true },
        { label: 'CRF', value: String(crf) }
      ]
    }
  },
  pyCode: (v) => {
    const dir = str(v.dir)
    const crf = Number.isFinite(Number(v.crf)) ? Math.trunc(Number(v.crf)) : 26
    if (!dir) return '# 选择视频目录后自动生成代码'
    return `"""批量转码 → mp4（CRF ${crf}）。"""
import glob
import json
import os
import shutil
import subprocess

FF = shutil.which("ffmpeg")
if not FF:
    raise SystemExit("未找到 ffmpeg（brew install ffmpeg / apt install ffmpeg）")
ok = fail = 0
for i, f in enumerate(sorted(glob.glob(os.path.join(${JSON.stringify(dir)}, "*.mp4")) + glob.glob(os.path.join(${JSON.stringify(dir)}, "*.mov"))), 1):
    out = f"transcoded_{i:03d}.mp4"
    r = subprocess.run([FF, "-i", f, "-c:v", "libx264", "-crf", "${crf}", "-preset", "fast", "-c:a", "aac", out, "-y"],
                       capture_output=True, text=True)
    if r.returncode == 0:
        ok += 1
        print(f"OK   {os.path.basename(f)} → {out}")
    else:
        fail += 1
        print(f"FAIL {os.path.basename(f)}（{r.stderr[-120:]}）")
print("<<<JSON>>>")
print(json.dumps({"primary": {"value": f"{ok}/{ok + fail}", "unit": "成功/总数"}}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

export const FFMPEG_SCHEMAS: InteractiveToolSchema[] = [
  videoCompressSchema,
  videoConvertSchema,
  videoMergeSchema,
  videoToGifSchema,
  videoShotSchema,
  removeAudioSchema,
  avTrimSchema,
  volumeAdjustSchema,
  extractAudioSchema,
  audioCompressSchema,
  batchTranscodeSchema
]
