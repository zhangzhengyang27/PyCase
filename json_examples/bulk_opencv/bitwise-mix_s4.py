"""位运算合成（棋盘场景）
OpenCV 图像处理示例。与/或/异或三通道合成。
合成输入图像自包含，运行后在当前目录生成 cv_bitwise-mix__preview.png。
"""
import cv2
import numpy as np

img = np.kron(np.indices((9, 12)).sum(0) % 2, np.uint8(255))[:360, :480].astype(np.uint8) * 0
img[::40, :] = 120; img[:, ::40] = 120
cv2.rectangle(img, (100, 100), (380, 260), 255, -1)

h, w = img.shape[:2]
m1 = np.zeros_like(img); cv2.circle(m1, (w // 3, h // 2), 80, 255, -1)
m2 = np.zeros_like(img); cv2.rectangle(m2, (w // 2, 40), (w - 20, h - 40), 255, -1)
result = np.hstack([cv2.bitwise_and(m1, m2), cv2.bitwise_or(m1, m2), cv2.bitwise_xor(m1, m2)])
cv2.imwrite("cv_bitwise-mix__preview.png", result if "result" in dir() else img)
print("已生成 cv_bitwise-mix__preview.png")
