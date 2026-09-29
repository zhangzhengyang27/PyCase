"""快速排序：50 个随机整数。"""
import random
random.seed(2)
data = [random.randint(0, 500) for _ in range(50)]

def qsort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    mid = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return qsort(left) + mid + qsort(right)

print("原:", data[:12], "...")
print("排序后:", qsort(data)[:12], "...")
