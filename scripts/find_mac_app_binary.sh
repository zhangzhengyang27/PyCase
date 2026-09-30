#!/usr/bin/env bash
# 从目录/挂载点里找出 macOS .app 包的主可执行文件（打印绝对路径，找不到则以非 0 退出）。
#
# 为什么不用 `find <dir> -path '*/Contents/MacOS/*'`：
#   1. Electron 包的 Frameworks/ 下还有一组 Helper .app，同样匹配该模式——按遍历顺序取
#      第一个会拿到 "… Helper (GPU)"（本机对 dmg 实测踩过）；
#   2. 写死 -maxdepth 也救不了：dist 里 app 包外还有一层 mac-arm64/，dmg 挂载点里没有。
# 因此口径是「先定位顶层 .app 包（depth ≤3，避开嵌套 Helper），再按包名取 Contents/MacOS/<包名>」。
#
# 用法：APP_BIN=$(bash scripts/find_mac_app_binary.sh dist)   # 或 zip 解包目录 / dmg 挂载点
set -euo pipefail

root=${1:?用法: find_mac_app_binary.sh <目录或挂载点>}
bundle=$(find "$root" -maxdepth 3 -type d -name '*.app' | head -1)
if [ -z "$bundle" ]; then
  echo "[find-app] 找不到 .app 包（$root，depth ≤3）：" >&2
  find "$root" -maxdepth 3 | head -20 >&2
  exit 2
fi

bin="$bundle/Contents/MacOS/$(basename "$bundle" .app)"
if [ ! -x "$bin" ]; then
  # 包名与可执行名不一致时退回「MacOS 下第一个可执行文件」，并留下诊断
  echo "[find-app] $bin 不存在，回退取 Contents/MacOS 下第一个可执行文件" >&2
  bin=$(find "$bundle/Contents/MacOS" -maxdepth 1 -type f -perm -100 | head -1)
  if [ -z "$bin" ]; then
    echo "[find-app] $bundle/Contents/MacOS 下没有可执行文件：" >&2
    ls -la "$bundle/Contents/MacOS" >&2
    exit 2
  fi
fi
echo "$bin"
