"""m3u8：HLS 视频的分段索引与下载模式（演示解析）。"""
M3U8 = """#EXTM3U
#EXT-X-TARGETDURATION:10
#EXTINF:9.5,
seg_0.ts
#EXTINF:9.2,
seg_1.ts
#EXTINF:8.8,
seg_2.ts
#EXT-X-ENDLIST"""
segments = []
for line in M3U8.splitlines():
    line = line.strip()
    if line and not line.startswith("#"):
        segments.append(line)
total = 10.0  # 真实场景解析 EXTINF 累加
print(f"共 {len(segments)} 段: {segments}")
print("真实抓取：requests 逐段下载 → 二进制拼接 → ffmpeg 合并转封装")
