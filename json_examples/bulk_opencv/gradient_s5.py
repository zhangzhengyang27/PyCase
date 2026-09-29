"""形态学梯度（混合场景）
OpenCV 图像处理示例。膨胀 − 腐蚀 = 边缘带。
合成输入图像自包含，运行后在当前目录生成 cv_gradient__preview.png。
"""
import cv2
import numpy as np

rng = np.random.default_rng(15)
img = rng.integers(40, 120, (360, 480), dtype=np.uint8)
cv2.ellipse(img, (240, 180), (180, 90), 25, 0, 360, 230, -1)
cv2.rectangle(img, (60, 60), (160, 160), 255, 4)

kernel = np.ones(({{k}}, {{k}}), np.uint8)
result = cv2.morphologyEx(img, cv2.MORPH_GRADIENT, kernel)
cv2.imwrite("cv_gradient__preview.png", result if "result" in dir() else img)
print("已生成 cv_gradient__preview.png")
