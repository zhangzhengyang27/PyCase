"""透视变换（竖条纹）
OpenCV 图像处理示例。四点透视矫正。
合成输入图像自包含，运行后在当前目录生成 cv_perspective__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
for x in range(0, 480, 24):
    cv2.rectangle(img, (x, 0), (x + 10, 360), 220, -1)
cv2.circle(img, (240, 180), 70, 90, -1)

h, w = img.shape[:2]
src = np.float32([[0, 0], [w - 1, 0], [0, h - 1], [w - 1, h - 1]])
dst = np.float32([[{{d}}, {{d}}], [w - 1 - {{d}}, {{d}} ], [{{d}}, h - 1 - {{d}}], [w - 1 - {{d}}, h - 1 - {{d}}]])
M = cv2.getPerspectiveTransform(src, dst)
result = cv2.warpPerspective(img, M, (w, h))
cv2.imwrite("cv_perspective__preview.png", result if "result" in dir() else img)
print("已生成 cv_perspective__preview.png")
