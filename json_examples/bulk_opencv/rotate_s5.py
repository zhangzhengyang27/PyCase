"""仿射旋转（混合场景）
OpenCV 图像处理示例。以中心旋转并缩放。
合成输入图像自包含，运行后在当前目录生成 cv_rotate__preview.png。
"""
import cv2
import numpy as np

rng = np.random.default_rng(15)
img = rng.integers(40, 120, (360, 480), dtype=np.uint8)
cv2.ellipse(img, (240, 180), (180, 90), 25, 0, 360, 230, -1)
cv2.rectangle(img, (60, 60), (160, 160), 255, 4)

h, w = img.shape[:2]
M = cv2.getRotationMatrix2D((w / 2, h / 2), 30, 1.1)
result = cv2.warpAffine(img, M, (w, h))
cv2.imwrite("cv_rotate__preview.png", result if "result" in dir() else img)
print("已生成 cv_rotate__preview.png")
