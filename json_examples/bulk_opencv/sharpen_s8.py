"""锐化滤波（大字报）
OpenCV 图像处理示例。拉普拉斯混合锐化。
合成输入图像自包含，运行后在当前目录生成 cv_sharpen__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
cv2.putText(img, "OPEN CV", (40, 210), cv2.FONT_HERSHEY_SIMPLEX, 2.6, 220, 12)
cv2.rectangle(img, (30, 30), (450, 330), 160, 5)

blur = cv2.GaussianBlur(img, (0, 0), 3)
result = cv2.addWeighted(img, {{w1}}, blur, -{{w2}}, 0)
cv2.imwrite("cv_sharpen__preview.png", result if "result" in dir() else img)
print("已生成 cv_sharpen__preview.png")
