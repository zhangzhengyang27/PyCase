"""直方图均衡（几何场景）
OpenCV 图像处理示例。对比度均衡（CLAHE 局部版）。
合成输入图像自包含，运行后在当前目录生成 cv_equalize__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
cv2.rectangle(img, (60, 60), (200, 200), 200, -1)
cv2.circle(img, (340, 140), 80, 140, -1)
cv2.line(img, (40, 300), (440, 320), 220, 6)

clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
result = clahe.apply(img)
cv2.imwrite("cv_equalize__preview.png", result if "result" in dir() else img)
print("已生成 cv_equalize__preview.png")
