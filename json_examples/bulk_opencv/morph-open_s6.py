"""形态学开运算（点阵圆环）
OpenCV 图像处理示例。腐蚀再膨胀，去小白噪点。
合成输入图像自包含，运行后在当前目录生成 cv_morph-open__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
for r in range(40, 200, 24):
    cv2.circle(img, (240, 180), r, 200, 3)
for a in range(0, 360, 15):
    cv2.circle(img, (int(240 + 120 * np.cos(np.radians(a))), int(180 + 120 * np.sin(np.radians(a)))), 5, 255, -1)

kernel = np.ones(({{k}}, {{k}}), np.uint8)
result = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
cv2.imwrite("cv_morph-open__preview.png", result if "result" in dir() else img)
print("已生成 cv_morph-open__preview.png")
