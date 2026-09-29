"""透视变换（点阵圆环）
OpenCV 图像处理示例。四点透视矫正。
合成输入图像自包含，运行后在当前目录生成 cv_perspective__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
for r in range(40, 200, 24):
    cv2.circle(img, (240, 180), r, 200, 3)
for a in range(0, 360, 15):
    cv2.circle(img, (int(240 + 120 * np.cos(np.radians(a))), int(180 + 120 * np.sin(np.radians(a)))), 5, 255, -1)

h, w = img.shape[:2]
src = np.float32([[0, 0], [w - 1, 0], [0, h - 1], [w - 1, h - 1]])
dst = np.float32([[{{d}}, {{d}}], [w - 1 - {{d}}, {{d}} ], [{{d}}, h - 1 - {{d}}], [w - 1 - {{d}}, h - 1 - {{d}}]])
M = cv2.getPerspectiveTransform(src, dst)
result = cv2.warpPerspective(img, M, (w, h))
cv2.imwrite("cv_perspective__preview.png", result if "result" in dir() else img)
print("已生成 cv_perspective__preview.png")
