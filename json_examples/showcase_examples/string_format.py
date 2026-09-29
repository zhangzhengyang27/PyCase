"""字符串格式化：三代语法对照。"""
pi = 3.14159265
name, score = "小明", 92.5

# 1) %-格式化（C 风格）
print("%s 的成绩是 %.1f" % (name, score))
# 2) str.format
print("{} 的成绩是 {:.2f}，百分比 {:.0%}".format(name, score, score / 100))
# 3) f-string（推荐）：表达式、对齐、填充、进制
print(f"{name:=^10} 的成绩 {score:*>8.2f}")
print(f"圆周率保留三位: {pi:.3f}，十六进制: {255:x}，二进制: {5:b}")
print(f"大数分隔: {1234567890:,}")

# 三引号多行模板
report = f"""
=== 成绩单 ===
姓名: {name}
成绩: {score}
等级: {'优秀' if score >= 90 else '良好'}
"""
print(report)
