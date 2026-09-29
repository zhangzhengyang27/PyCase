"""仿射旋转（大字报）
OpenCV 图像处理示例。以中心旋转并缩放。
合成输入图像自包含，运行后在当前目录生成 cv_rotate__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
cv2.putText(img, "OPEN CV", (40, 210), cv2.FONT_HERSHEY_SIMPLEX, 2.6, 220, 12)
cv2.rectangle(img, (30, 30), (450, 330), 160, 5)

h, w = img.shape[:2]
M = cv2.getRotationMatrix2D((w / 2, h / 2), {{angle}}, {{scale}})
result = cv2.warpAffine(img, M, (w, h))
cv2.imwrite("cv_rotate__preview.png", result if "result" in dir() else img)
print("已生成 cv_rotate__preview.png")
