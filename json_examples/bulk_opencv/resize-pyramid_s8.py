"""缩放金字塔（大字报）
OpenCV 图像处理示例。逐级缩小的高斯金字塔。
合成输入图像自包含，运行后在当前目录生成 cv_resize-pyramid__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
cv2.putText(img, "OPEN CV", (40, 210), cv2.FONT_HERSHEY_SIMPLEX, 2.6, 220, 12)
cv2.rectangle(img, (30, 30), (450, 330), 160, 5)

levels = [img]
for _ in range(3):
    levels.append(cv2.pyrDown(levels[-1]))
result = np.hstack([cv2.resize(l, (img.shape[1] // 4, img.shape[0] // 4)) for l in levels])
cv2.imwrite("cv_resize-pyramid__preview.png", result if "result" in dir() else img)
print("已生成 cv_resize-pyramid__preview.png")
