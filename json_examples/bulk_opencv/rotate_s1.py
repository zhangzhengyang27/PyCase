"""仿射旋转（几何场景）
OpenCV 图像处理示例。以中心旋转并缩放。
合成输入图像自包含，运行后在当前目录生成 cv_rotate__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
cv2.rectangle(img, (60, 60), (200, 200), 200, -1)
cv2.circle(img, (340, 140), 80, 140, -1)
cv2.line(img, (40, 300), (440, 320), 220, 6)

h, w = img.shape[:2]
M = cv2.getRotationMatrix2D((w / 2, h / 2), {{angle}}, {{scale}})
result = cv2.warpAffine(img, M, (w, h))
cv2.imwrite("cv_rotate__preview.png", result if "result" in dir() else img)
print("已生成 cv_rotate__preview.png")
