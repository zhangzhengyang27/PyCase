"""阈值分割（噪声场景）
OpenCV 图像处理示例。Otsu 全局阈值二值化。
合成输入图像自包含，运行后在当前目录生成 cv_threshold__preview.png。
"""
import cv2
import numpy as np

rng = np.random.default_rng(13)
img = rng.integers(60, 200, (360, 480), dtype=np.uint8)
cv2.circle(img, (240, 180), 110, 255, -1)

blur = cv2.GaussianBlur(img, (7, 7), 0)
_, result = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
cv2.imwrite("cv_threshold__preview.png", result if "result" in dir() else img)
print("已生成 cv_threshold__preview.png")
