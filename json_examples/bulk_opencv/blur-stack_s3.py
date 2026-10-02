"""模糊对比（噪声场景）
OpenCV 图像处理示例。均值/高斯/中值三种模糊并排。
合成输入图像自包含，运行后在当前目录生成 cv_blur-stack__preview.png。
"""
import cv2
import numpy as np

rng = np.random.default_rng(13)
img = rng.integers(60, 200, (360, 480), dtype=np.uint8)
cv2.circle(img, (240, 180), 110, 255, -1)

a = cv2.blur(img, (5, 5))
b = cv2.GaussianBlur(img, (5, 5), 0)
c = cv2.medianBlur(img, 5)
result = np.hstack([a, b, c])
cv2.imwrite("cv_blur-stack__preview.png", result if "result" in dir() else img)
print("已生成 cv_blur-stack__preview.png")
