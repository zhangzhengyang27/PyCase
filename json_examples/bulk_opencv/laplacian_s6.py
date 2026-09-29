"""Laplacian 锐边（点阵圆环）
OpenCV 图像处理示例。二阶导数边缘响应。
合成输入图像自包含，运行后在当前目录生成 cv_laplacian__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
for r in range(40, 200, 24):
    cv2.circle(img, (240, 180), r, 200, 3)
for a in range(0, 360, 15):
    cv2.circle(img, (int(240 + 120 * np.cos(np.radians(a))), int(180 + 120 * np.sin(np.radians(a)))), 5, 255, -1)

blur = cv2.GaussianBlur(img, (3, 3), 0)
result = np.clip(np.abs(cv2.Laplacian(blur, cv2.CV_64F)), 0, 255).astype(np.uint8)
cv2.imwrite("cv_laplacian__preview.png", result if "result" in dir() else img)
print("已生成 cv_laplacian__preview.png")
