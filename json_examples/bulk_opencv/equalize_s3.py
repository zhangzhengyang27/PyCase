"""直方图均衡（噪声场景）
OpenCV 图像处理示例。对比度均衡（CLAHE 局部版）。
合成输入图像自包含，运行后在当前目录生成 cv_equalize__preview.png。
"""
import cv2
import numpy as np

rng = np.random.default_rng(13)
img = rng.integers(60, 200, (360, 480), dtype=np.uint8)
cv2.circle(img, (240, 180), 110, 255, -1)

clahe = cv2.createCLAHE(clipLimit={{clip}}, tileGridSize=(8, 8))
result = clahe.apply(img)
cv2.imwrite("cv_equalize__preview.png", result if "result" in dir() else img)
print("已生成 cv_equalize__preview.png")
