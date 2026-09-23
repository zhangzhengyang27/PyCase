#!/usr/bin/env bash
# 合并到 01-代码 同层 + 统一 NN- 编号
cd "$(dirname "$0")/../python-basics/01-代码"

# 映射表：源 -> 目标
declare -A MAP
MAP[01-注释.py]="01-注释.py"
MAP[learn-python/hello_world.py]="02-第一个程序.py"
MAP[01-基础语法碎片.py]="03-基础语法碎片.py"
MAP[02-变量.py]="04-变量.py"
MAP[hm_01_输入.py]="05-输入.py"
MAP[数据类型转换/hm_01_快速体验数据类型转换.py]="06-数据类型转换_快速体验.py"
MAP[数据类型转换/hm_02_数据类型转换函数.py]="07-数据类型转换_转换函数.py"
MAP[04-认识数据类型.py]="08-认识数据类型.py"
MAP[05-格式化输出.py]="09-格式化输出.py"
MAP[hm_01_复合赋值运算符.py]="10-复合赋值运算符.py"
MAP[hm_02_逻辑运算符.py]="11-逻辑运算符.py"
MAP[learn-python/数字运算.py]="12-数字运算.py"
MAP[learn-python/我的python练习1.py]="13-我的python练习1.py"
MAP[my_first_python.py]="14-my_first_python.py"

for src in "${!MAP[@]}"; do
    dst="${MAP[$src]}"
    if [ -e "$dst" ]; then
        echo "[冲突] 目标已存在: $dst"
        continue
    fi
    if [ ! -e "$src" ]; then
        echo "[缺失] 源不存在: $src"
        continue
    fi
    mv "$src" "$dst" && echo "[移动] $src -> $dst"
done

# 删除空的子目录
rmdir learn-python 2>/dev/null && echo "[删空目录] learn-python"
rmdir 数据类型转换 2>/dev/null && echo "[删空目录] 数据类型转换"

echo ""
echo "=== 合并后 01-代码 现状 ==="
ls -1
