"""位运算合成（几何场景）
OpenCV 图像处理示例。与/或/异或三通道合成。
合成输入图像自包含，运行后在当前目录生成 cv_bitwise-mix__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
cv2.rectangle(img, (60, 60), (200, 200), 200, -1)
cv2.circle(img, (340, 140), 80, 140, -1)
cv2.line(img, (40, 300), (440, 320), 220, 6)

h, w = img.shape[:2]
m1 = np.zeros_like(img); cv2.circle(m1, (w // 3, h // 2), 80, 255, -1)
m2 = np.zeros_like(img); cv2.rectangle(m2, (w // 2, 40), (w - 20, h - 40), 255, -1)
result = np.hstack([cv2.bitwise_and(m1, m2), cv2.bitwise_or(m1, m2), cv2.bitwise_xor(m1, m2)])
cv2.imwrite("cv_bitwise-mix__preview.png", result if "result" in dir() else img)
print("已生成 cv_bitwise-mix__preview.png")
