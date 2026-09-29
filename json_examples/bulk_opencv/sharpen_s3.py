"""锐化滤波（噪声场景）
OpenCV 图像处理示例。拉普拉斯混合锐化。
合成输入图像自包含，运行后在当前目录生成 cv_sharpen__preview.png。
"""
import cv2
import numpy as np

rng = np.random.default_rng(13)
img = rng.integers(60, 200, (360, 480), dtype=np.uint8)
cv2.circle(img, (240, 180), 110, 255, -1)

blur = cv2.GaussianBlur(img, (0, 0), 3)
result = cv2.addWeighted(img, {{w1}}, blur, -{{w2}}, 0)
cv2.imwrite("cv_sharpen__preview.png", result if "result" in dir() else img)
print("已生成 cv_sharpen__preview.png")
