"""形态学闭运算（噪声场景）
OpenCV 图像处理示例。膨胀再腐蚀，补小黑洞。
合成输入图像自包含，运行后在当前目录生成 cv_morph-close__preview.png。
"""
import cv2
import numpy as np

rng = np.random.default_rng(13)
img = rng.integers(60, 200, (360, 480), dtype=np.uint8)
cv2.circle(img, (240, 180), 110, 255, -1)

kernel = np.ones((5, 5), np.uint8)
result = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)
cv2.imwrite("cv_morph-close__preview.png", result if "result" in dir() else img)
print("已生成 cv_morph-close__preview.png")
