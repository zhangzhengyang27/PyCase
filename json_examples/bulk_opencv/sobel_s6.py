"""Sobel 梯度（点阵圆环）
OpenCV 图像处理示例。x/y 方向梯度合成幅值。
合成输入图像自包含，运行后在当前目录生成 cv_sobel__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
for r in range(40, 200, 24):
    cv2.circle(img, (240, 180), r, 200, 3)
for a in range(0, 360, 15):
    cv2.circle(img, (int(240 + 120 * np.cos(np.radians(a))), int(180 + 120 * np.sin(np.radians(a)))), 5, 255, -1)

gx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
gy = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)
result = np.clip(np.hypot(gx, gy), 0, 255).astype(np.uint8)
cv2.imwrite("cv_sobel__preview.png", result if "result" in dir() else img)
print("已生成 cv_sobel__preview.png")
