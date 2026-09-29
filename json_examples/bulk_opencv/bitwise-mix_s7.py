"""位运算合成（竖条纹）
OpenCV 图像处理示例。与/或/异或三通道合成。
合成输入图像自包含，运行后在当前目录生成 cv_bitwise-mix__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
for x in range(0, 480, 24):
    cv2.rectangle(img, (x, 0), (x + 10, 360), 220, -1)
cv2.circle(img, (240, 180), 70, 90, -1)

h, w = img.shape[:2]
m1 = np.zeros_like(img); cv2.circle(m1, (w // 3, h // 2), 80, 255, -1)
m2 = np.zeros_like(img); cv2.rectangle(m2, (w // 2, 40), (w - 20, h - 40), 255, -1)
result = np.hstack([cv2.bitwise_and(m1, m2), cv2.bitwise_or(m1, m2), cv2.bitwise_xor(m1, m2)])
cv2.imwrite("cv_bitwise-mix__preview.png", result if "result" in dir() else img)
print("已生成 cv_bitwise-mix__preview.png")
