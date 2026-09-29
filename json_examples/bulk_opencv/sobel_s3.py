"""Sobel 梯度（噪声场景）
OpenCV 图像处理示例。x/y 方向梯度合成幅值。
合成输入图像自包含，运行后在当前目录生成 cv_sobel__preview.png。
"""
import cv2
import numpy as np

rng = np.random.default_rng(13)
img = rng.integers(60, 200, (360, 480), dtype=np.uint8)
cv2.circle(img, (240, 180), 110, 255, -1)

gx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
gy = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)
result = np.clip(np.hypot(gx, gy), 0, 255).astype(np.uint8)
cv2.imwrite("cv_sobel__preview.png", result if "result" in dir() else img)
print("已生成 cv_sobel__preview.png")
