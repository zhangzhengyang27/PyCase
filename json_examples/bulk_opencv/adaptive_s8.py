"""自适应阈值（大字报）
OpenCV 图像处理示例。局部均值自适应阈值（光照不均友好）。
合成输入图像自包含，运行后在当前目录生成 cv_adaptive__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
cv2.putText(img, "OPEN CV", (40, 210), cv2.FONT_HERSHEY_SIMPLEX, 2.6, 220, 12)
cv2.rectangle(img, (30, 30), (450, 330), 160, 5)

blur = cv2.medianBlur(img, 5)
result = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 6)
cv2.imwrite("cv_adaptive__preview.png", result if "result" in dir() else img)
print("已生成 cv_adaptive__preview.png")
