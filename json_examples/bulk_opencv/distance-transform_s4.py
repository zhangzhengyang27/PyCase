"""距离变换（棋盘场景）
OpenCV 图像处理示例。前景像素到边界的距离场。
合成输入图像自包含，运行后在当前目录生成 cv_distance-transform__preview.png。
"""
import cv2
import numpy as np

img = np.kron(np.indices((9, 12)).sum(0) % 2, np.uint8(255))[:360, :480].astype(np.uint8) * 0
img[::40, :] = 120; img[:, ::40] = 120
cv2.rectangle(img, (100, 100), (380, 260), 255, -1)

_, th = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)
result = cv2.normalize(cv2.distanceTransform(th, cv2.DIST_L2, 5), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
cv2.imwrite("cv_distance-transform__preview.png", result if "result" in dir() else img)
print("已生成 cv_distance-transform__preview.png")
