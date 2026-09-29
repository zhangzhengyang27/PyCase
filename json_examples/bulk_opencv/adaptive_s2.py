"""自适应阈值（渐变场景）
OpenCV 图像处理示例。局部均值自适应阈值（光照不均友好）。
合成输入图像自包含，运行后在当前目录生成 cv_adaptive__preview.png。
"""
import cv2
import numpy as np

img = np.tile(np.linspace(30, 220, 480, dtype=np.uint8), (360, 1))
cv2.putText(img, "CV", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 4, 255, 12)

blur = cv2.medianBlur(img, 5)
result = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 6)
cv2.imwrite("cv_adaptive__preview.png", result if "result" in dir() else img)
print("已生成 cv_adaptive__preview.png")
