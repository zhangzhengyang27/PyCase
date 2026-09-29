"""缩放金字塔（点阵圆环）
OpenCV 图像处理示例。逐级缩小的高斯金字塔。
合成输入图像自包含，运行后在当前目录生成 cv_resize-pyramid__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
for r in range(40, 200, 24):
    cv2.circle(img, (240, 180), r, 200, 3)
for a in range(0, 360, 15):
    cv2.circle(img, (int(240 + 120 * np.cos(np.radians(a))), int(180 + 120 * np.sin(np.radians(a)))), 5, 255, -1)

levels = [img]
for _ in range(3):
    levels.append(cv2.pyrDown(levels[-1]))
result = np.hstack([cv2.resize(l, (img.shape[1] // 4, img.shape[0] // 4)) for l in levels])
cv2.imwrite("cv_resize-pyramid__preview.png", result if "result" in dir() else img)
print("已生成 cv_resize-pyramid__preview.png")
