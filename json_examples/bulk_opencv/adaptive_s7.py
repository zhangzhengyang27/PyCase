"""自适应阈值（竖条纹）
OpenCV 图像处理示例。局部均值自适应阈值（光照不均友好）。
合成输入图像自包含，运行后在当前目录生成 cv_adaptive__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
for x in range(0, 480, 24):
    cv2.rectangle(img, (x, 0), (x + 10, 360), 220, -1)
cv2.circle(img, (240, 180), 70, 90, -1)

blur = cv2.medianBlur(img, 5)
result = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 6)
cv2.imwrite("cv_adaptive__preview.png", result if "result" in dir() else img)
print("已生成 cv_adaptive__preview.png")
