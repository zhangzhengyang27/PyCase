"""Gamma 校正（大字报）
OpenCV 图像处理示例。查找表法伽马亮度校正。
合成输入图像自包含，运行后在当前目录生成 cv_gamma__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
cv2.putText(img, "OPEN CV", (40, 210), cv2.FONT_HERSHEY_SIMPLEX, 2.6, 220, 12)
cv2.rectangle(img, (30, 30), (450, 330), 160, 5)

table = np.array([(i / 255.0) ** 1.2 * 255 for i in range(256)]).astype(np.uint8)
result = cv2.LUT(img, table)
cv2.imwrite("cv_gamma__preview.png", result if "result" in dir() else img)
print("已生成 cv_gamma__preview.png")
