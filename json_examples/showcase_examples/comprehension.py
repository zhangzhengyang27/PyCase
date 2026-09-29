"""推导式：Pythonic 数据变换的核心写法。"""
nums = range(1, 21)

# 列表推导：平方 + 过滤
squares = [n * n for n in nums if n % 2 == 0]
print("偶数的平方:", squares)

# 字典推导：单词 -> 长度
words = ["apple", "banana", "cherry", "avocado"]
lengths = {w: len(w) for w in words}
print("词长字典:", lengths)

# 集合推导：去重首字母
firsts = {w[0] for w in words}
print("首字母集合:", firsts)

# 嵌套推导：九九乘法表上三角
table = [(i, j, i * j) for i in range(1, 6) for j in range(i, 6)]
print("乘法组合数:", len(table))

# 生成器表达式：惰性求值省内存
total = sum(n * n for n in nums)
print("1~20 平方和:", total)
