"""缩放金字塔（几何场景）
OpenCV 图像处理示例。逐级缩小的高斯金字塔。
合成输入图像自包含，运行后在当前目录生成 cv_resize-pyramid__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
cv2.rectangle(img, (60, 60), (200, 200), 200, -1)
cv2.circle(img, (340, 140), 80, 140, -1)
cv2.line(img, (40, 300), (440, 320), 220, 6)

levels = [img]
for _ in range(3):
    levels.append(cv2.pyrDown(levels[-1]))
result = np.hstack([cv2.resize(l, (img.shape[1] // 4, img.shape[0] // 4)) for l in levels])
cv2.imwrite("cv_resize-pyramid__preview.png", result if "result" in dir() else img)
print("已生成 cv_resize-pyramid__preview.png")
