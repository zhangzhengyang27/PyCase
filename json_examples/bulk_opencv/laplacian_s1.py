"""Laplacian 锐边（几何场景）
OpenCV 图像处理示例。二阶导数边缘响应。
合成输入图像自包含，运行后在当前目录生成 cv_laplacian__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
cv2.rectangle(img, (60, 60), (200, 200), 200, -1)
cv2.circle(img, (340, 140), 80, 140, -1)
cv2.line(img, (40, 300), (440, 320), 220, 6)

blur = cv2.GaussianBlur(img, (3, 3), 0)
result = np.clip(np.abs(cv2.Laplacian(blur, cv2.CV_64F)), 0, 255).astype(np.uint8)
cv2.imwrite("cv_laplacian__preview.png", result if "result" in dir() else img)
print("已生成 cv_laplacian__preview.png")
