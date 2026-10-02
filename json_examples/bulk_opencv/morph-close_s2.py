"""形态学闭运算（渐变场景）
OpenCV 图像处理示例。膨胀再腐蚀，补小黑洞。
合成输入图像自包含，运行后在当前目录生成 cv_morph-close__preview.png。
"""
import cv2
import numpy as np

img = np.tile(np.linspace(30, 220, 480, dtype=np.uint8), (360, 1))
cv2.putText(img, "CV", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 4, 255, 12)

kernel = np.ones((5, 5), np.uint8)
result = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)
cv2.imwrite("cv_morph-close__preview.png", result if "result" in dir() else img)
print("已生成 cv_morph-close__preview.png")
