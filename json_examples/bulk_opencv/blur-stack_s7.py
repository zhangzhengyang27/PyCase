"""模糊对比（竖条纹）
OpenCV 图像处理示例。均值/高斯/中值三种模糊并排。
合成输入图像自包含，运行后在当前目录生成 cv_blur-stack__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
for x in range(0, 480, 24):
    cv2.rectangle(img, (x, 0), (x + 10, 360), 220, -1)
cv2.circle(img, (240, 180), 70, 90, -1)

a = cv2.blur(img, ({{k}}, {{k}}))
b = cv2.GaussianBlur(img, ({{k}}, {{k}}), 0)
c = cv2.medianBlur(img, {{k}})
result = np.hstack([a, b, c])
cv2.imwrite("cv_blur-stack__preview.png", result if "result" in dir() else img)
print("已生成 cv_blur-stack__preview.png")
