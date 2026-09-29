"""仿射旋转（棋盘场景）
OpenCV 图像处理示例。以中心旋转并缩放。
合成输入图像自包含，运行后在当前目录生成 cv_rotate__preview.png。
"""
import cv2
import numpy as np

img = np.kron(np.indices((9, 12)).sum(0) % 2, np.uint8(255))[:360, :480].astype(np.uint8) * 0
img[::40, :] = 120; img[:, ::40] = 120
cv2.rectangle(img, (100, 100), (380, 260), 255, -1)

h, w = img.shape[:2]
M = cv2.getRotationMatrix2D((w / 2, h / 2), {{angle}}, {{scale}})
result = cv2.warpAffine(img, M, (w, h))
cv2.imwrite("cv_rotate__preview.png", result if "result" in dir() else img)
print("已生成 cv_rotate__preview.png")
