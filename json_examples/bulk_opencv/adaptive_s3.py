"""自适应阈值（噪声场景）
OpenCV 图像处理示例。局部均值自适应阈值（光照不均友好）。
合成输入图像自包含，运行后在当前目录生成 cv_adaptive__preview.png。
"""
import cv2
import numpy as np

rng = np.random.default_rng(13)
img = rng.integers(60, 200, (360, 480), dtype=np.uint8)
cv2.circle(img, (240, 180), 110, 255, -1)

blur = cv2.medianBlur(img, 5)
result = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 6)
cv2.imwrite("cv_adaptive__preview.png", result if "result" in dir() else img)
print("已生成 cv_adaptive__preview.png")
