"""Gamma 校正（混合场景）
OpenCV 图像处理示例。查找表法伽马亮度校正。
合成输入图像自包含，运行后在当前目录生成 cv_gamma__preview.png。
"""
import cv2
import numpy as np

rng = np.random.default_rng(15)
img = rng.integers(40, 120, (360, 480), dtype=np.uint8)
cv2.ellipse(img, (240, 180), (180, 90), 25, 0, 360, 230, -1)
cv2.rectangle(img, (60, 60), (160, 160), 255, 4)

table = np.array([(i / 255.0) ** {{gamma}} * 255 for i in range(256)]).astype(np.uint8)
result = cv2.LUT(img, table)
cv2.imwrite("cv_gamma__preview.png", result if "result" in dir() else img)
print("已生成 cv_gamma__preview.png")
