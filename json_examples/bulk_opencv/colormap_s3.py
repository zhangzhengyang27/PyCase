"""伪彩色映射（噪声场景）
OpenCV 图像处理示例。灰度图套用 COLORMAP_JET。
合成输入图像自包含，运行后在当前目录生成 cv_colormap__preview.png。
"""
import cv2
import numpy as np

rng = np.random.default_rng(13)
img = rng.integers(60, 200, (360, 480), dtype=np.uint8)
cv2.circle(img, (240, 180), 110, 255, -1)

result = cv2.applyColorMap(img, cv2.COLORMAP_JET)
cv2.imwrite("cv_colormap__preview.png", result if "result" in dir() else img)
print("已生成 cv_colormap__preview.png")
