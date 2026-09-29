"""距离变换（点阵圆环）
OpenCV 图像处理示例。前景像素到边界的距离场。
合成输入图像自包含，运行后在当前目录生成 cv_distance-transform__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
for r in range(40, 200, 24):
    cv2.circle(img, (240, 180), r, 200, 3)
for a in range(0, 360, 15):
    cv2.circle(img, (int(240 + 120 * np.cos(np.radians(a))), int(180 + 120 * np.sin(np.radians(a)))), 5, 255, -1)

_, th = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)
result = cv2.normalize(cv2.distanceTransform(th, cv2.DIST_L2, 5), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
cv2.imwrite("cv_distance-transform__preview.png", result if "result" in dir() else img)
print("已生成 cv_distance-transform__preview.png")
