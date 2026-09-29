"""距离变换（渐变场景）
OpenCV 图像处理示例。前景像素到边界的距离场。
合成输入图像自包含，运行后在当前目录生成 cv_distance-transform__preview.png。
"""
import cv2
import numpy as np

img = np.tile(np.linspace(30, 220, 480, dtype=np.uint8), (360, 1))
cv2.putText(img, "CV", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 4, 255, 12)

_, th = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)
result = cv2.normalize(cv2.distanceTransform(th, cv2.DIST_L2, 5), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
cv2.imwrite("cv_distance-transform__preview.png", result if "result" in dir() else img)
print("已生成 cv_distance-transform__preview.png")
