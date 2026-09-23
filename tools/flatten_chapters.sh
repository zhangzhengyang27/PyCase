#!/bin/zsh
set -u
cd "$(dirname "$0")/../python-basics"

# 可扁平化的纯示例章节
CHAPTERS=("04-字符串&列表&元祖" "05-代码" "06-函数" "07-函数进阶" "09-面向对象")

# 需保留（含包/完整项目）的子目录名
KEEP=("03-学员管理系统" "geekbang_sanguo" "geekbang_21" "learn-python")

for d in "${CHAPTERS[@]}"; do
  for sub in "$d"/*/; do
    [ -d "$sub" ] || continue
    base=$(basename "$sub")
    skip=0
    for k in "${KEEP[@]}"; do
      [ "$base" = "$k" ] && skip=1 && break
    done
    [ $skip -eq 1 ] && continue
    # 移动子目录下所有 .py 到章目录同层
    for f in "$sub"*.py; do
      [ -e "$f" ] || continue
      if [ -e "$d/$(basename "$f")" ]; then
        echo "[冲突] 目标已存在，跳过: $d/$(basename "$f")"
      else
        mv -n "$f" "$d/"
      fi
    done
    # 仅当子目录无残留非 .py 文件时删除
    leftover=$(find "$sub" -maxdepth 1 -type f ! -name "*.py" | head -1)
    if [ -z "$leftover" ]; then
      if rmdir "$sub"; then
        echo "[删空目录] $sub"
      else
        echo "[保留] 目录删除失败(非空): $sub"
      fi
    else
      echo "[保留-有非py文件] $sub"
    fi
  done
done

echo ""
echo "=== 扁平化后各章状态 ==="
for d in "${CHAPTERS[@]}"; do
  pycount=$(find "$d" -maxdepth 1 -name "*.py" | wc -l | tr -d ' ')
  subs=$(find "$d" -maxdepth 1 -type d ! -name "$d" -exec basename {} \; | tr '\n' ' ')
  echo "## $d : ${pycount} 个 .py | 残留子目录: ${subs}"
done
