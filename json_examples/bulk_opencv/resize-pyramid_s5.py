"""缩放金字塔（混合场景）
OpenCV 图像处理示例。逐级缩小的高斯金字塔。
合成输入图像自包含，运行后在当前目录生成 cv_resize-pyramid__preview.png。
"""
import cv2
import numpy as np

rng = np.random.default_rng(15)
img = rng.integers(40, 120, (360, 480), dtype=np.uint8)
cv2.ellipse(img, (240, 180), (180, 90), 25, 0, 360, 230, -1)
cv2.rectangle(img, (60, 60), (160, 160), 255, 4)

levels = [img]
for _ in range(3):
    levels.append(cv2.pyrDown(levels[-1]))
result = np.hstack([cv2.resize(l, (img.shape[1] // 4, img.shape[0] // 4)) for l in levels])
cv2.imwrite("cv_resize-pyramid__preview.png", result if "result" in dir() else img)
print("已生成 cv_resize-pyramid__preview.png")
