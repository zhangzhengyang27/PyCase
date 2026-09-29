"""形态学梯度（棋盘场景）
OpenCV 图像处理示例。膨胀 − 腐蚀 = 边缘带。
合成输入图像自包含，运行后在当前目录生成 cv_gradient__preview.png。
"""
import cv2
import numpy as np

img = np.kron(np.indices((9, 12)).sum(0) % 2, np.uint8(255))[:360, :480].astype(np.uint8) * 0
img[::40, :] = 120; img[:, ::40] = 120
cv2.rectangle(img, (100, 100), (380, 260), 255, -1)

kernel = np.ones(({{k}}, {{k}}), np.uint8)
result = cv2.morphologyEx(img, cv2.MORPH_GRADIENT, kernel)
cv2.imwrite("cv_gradient__preview.png", result if "result" in dir() else img)
print("已生成 cv_gradient__preview.png")
