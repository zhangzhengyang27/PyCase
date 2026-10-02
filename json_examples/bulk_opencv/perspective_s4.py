"""透视变换（棋盘场景）
OpenCV 图像处理示例。四点透视矫正。
合成输入图像自包含，运行后在当前目录生成 cv_perspective__preview.png。
"""
import cv2
import numpy as np

img = np.kron(np.indices((9, 12)).sum(0) % 2, np.uint8(255))[:360, :480].astype(np.uint8) * 0
img[::40, :] = 120; img[:, ::40] = 120
cv2.rectangle(img, (100, 100), (380, 260), 255, -1)

h, w = img.shape[:2]
src = np.float32([[0, 0], [w - 1, 0], [0, h - 1], [w - 1, h - 1]])
dst = np.float32([[60, 60], [w - 1 - 60, 60 ], [60, h - 1 - 60], [w - 1 - 60, h - 1 - 60]])
M = cv2.getPerspectiveTransform(src, dst)
result = cv2.warpPerspective(img, M, (w, h))
cv2.imwrite("cv_perspective__preview.png", result if "result" in dir() else img)
print("已生成 cv_perspective__preview.png")
