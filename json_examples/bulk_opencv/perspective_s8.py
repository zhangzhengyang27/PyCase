"""透视变换（大字报）
OpenCV 图像处理示例。四点透视矫正。
合成输入图像自包含，运行后在当前目录生成 cv_perspective__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
cv2.putText(img, "OPEN CV", (40, 210), cv2.FONT_HERSHEY_SIMPLEX, 2.6, 220, 12)
cv2.rectangle(img, (30, 30), (450, 330), 160, 5)

h, w = img.shape[:2]
src = np.float32([[0, 0], [w - 1, 0], [0, h - 1], [w - 1, h - 1]])
dst = np.float32([[60, 60], [w - 1 - 60, 60 ], [60, h - 1 - 60], [w - 1 - 60, h - 1 - 60]])
M = cv2.getPerspectiveTransform(src, dst)
result = cv2.warpPerspective(img, M, (w, h))
cv2.imwrite("cv_perspective__preview.png", result if "result" in dir() else img)
print("已生成 cv_perspective__preview.png")
