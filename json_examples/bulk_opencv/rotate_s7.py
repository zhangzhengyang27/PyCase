"""仿射旋转（竖条纹）
OpenCV 图像处理示例。以中心旋转并缩放。
合成输入图像自包含，运行后在当前目录生成 cv_rotate__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
for x in range(0, 480, 24):
    cv2.rectangle(img, (x, 0), (x + 10, 360), 220, -1)
cv2.circle(img, (240, 180), 70, 90, -1)

h, w = img.shape[:2]
M = cv2.getRotationMatrix2D((w / 2, h / 2), 30, 1.1)
result = cv2.warpAffine(img, M, (w, h))
cv2.imwrite("cv_rotate__preview.png", result if "result" in dir() else img)
print("已生成 cv_rotate__preview.png")
