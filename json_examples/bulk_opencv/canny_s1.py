"""Canny 边缘（几何场景）
OpenCV 图像处理示例。高斯去噪 + 双阈值边缘提取。
合成输入图像自包含，运行后在当前目录生成 cv_canny__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
cv2.rectangle(img, (60, 60), (200, 200), 200, -1)
cv2.circle(img, (340, 140), 80, 140, -1)
cv2.line(img, (40, 300), (440, 320), 220, 6)

blur = cv2.GaussianBlur(img, (5, 5), 0)
result = cv2.Canny(blur, 100, 200)
cv2.imwrite("cv_canny__preview.png", result if "result" in dir() else img)
print("已生成 cv_canny__preview.png")
