"""锐化滤波（棋盘场景）
OpenCV 图像处理示例。拉普拉斯混合锐化。
合成输入图像自包含，运行后在当前目录生成 cv_sharpen__preview.png。
"""
import cv2
import numpy as np

img = np.kron(np.indices((9, 12)).sum(0) % 2, np.uint8(255))[:360, :480].astype(np.uint8) * 0
img[::40, :] = 120; img[:, ::40] = 120
cv2.rectangle(img, (100, 100), (380, 260), 255, -1)

blur = cv2.GaussianBlur(img, (0, 0), 3)
result = cv2.addWeighted(img, {{w1}}, blur, -{{w2}}, 0)
cv2.imwrite("cv_sharpen__preview.png", result if "result" in dir() else img)
print("已生成 cv_sharpen__preview.png")
