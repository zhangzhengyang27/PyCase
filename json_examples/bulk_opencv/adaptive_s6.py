"""自适应阈值（点阵圆环）
OpenCV 图像处理示例。局部均值自适应阈值（光照不均友好）。
合成输入图像自包含，运行后在当前目录生成 cv_adaptive__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
for r in range(40, 200, 24):
    cv2.circle(img, (240, 180), r, 200, 3)
for a in range(0, 360, 15):
    cv2.circle(img, (int(240 + 120 * np.cos(np.radians(a))), int(180 + 120 * np.sin(np.radians(a)))), 5, 255, -1)

blur = cv2.medianBlur(img, 5)
result = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 6)
cv2.imwrite("cv_adaptive__preview.png", result if "result" in dir() else img)
print("已生成 cv_adaptive__preview.png")
