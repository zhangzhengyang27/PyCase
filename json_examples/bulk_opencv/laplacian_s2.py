"""Laplacian 锐边（渐变场景）
OpenCV 图像处理示例。二阶导数边缘响应。
合成输入图像自包含，运行后在当前目录生成 cv_laplacian__preview.png。
"""
import cv2
import numpy as np

img = np.tile(np.linspace(30, 220, 480, dtype=np.uint8), (360, 1))
cv2.putText(img, "CV", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 4, 255, 12)

blur = cv2.GaussianBlur(img, (3, 3), 0)
result = np.clip(np.abs(cv2.Laplacian(blur, cv2.CV_64F)), 0, 255).astype(np.uint8)
cv2.imwrite("cv_laplacian__preview.png", result if "result" in dir() else img)
print("已生成 cv_laplacian__preview.png")
