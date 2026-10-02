"""Gamma 校正（渐变场景）
OpenCV 图像处理示例。查找表法伽马亮度校正。
合成输入图像自包含，运行后在当前目录生成 cv_gamma__preview.png。
"""
import cv2
import numpy as np

img = np.tile(np.linspace(30, 220, 480, dtype=np.uint8), (360, 1))
cv2.putText(img, "CV", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 4, 255, 12)

table = np.array([(i / 255.0) ** 1.2 * 255 for i in range(256)]).astype(np.uint8)
result = cv2.LUT(img, table)
cv2.imwrite("cv_gamma__preview.png", result if "result" in dir() else img)
print("已生成 cv_gamma__preview.png")
