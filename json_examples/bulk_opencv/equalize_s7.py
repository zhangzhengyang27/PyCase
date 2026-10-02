"""直方图均衡（竖条纹）
OpenCV 图像处理示例。对比度均衡（CLAHE 局部版）。
合成输入图像自包含，运行后在当前目录生成 cv_equalize__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
for x in range(0, 480, 24):
    cv2.rectangle(img, (x, 0), (x + 10, 360), 220, -1)
cv2.circle(img, (240, 180), 70, 90, -1)

clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
result = clahe.apply(img)
cv2.imwrite("cv_equalize__preview.png", result if "result" in dir() else img)
print("已生成 cv_equalize__preview.png")
