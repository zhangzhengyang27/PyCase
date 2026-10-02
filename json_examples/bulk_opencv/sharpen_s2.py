"""锐化滤波（渐变场景）
OpenCV 图像处理示例。拉普拉斯混合锐化。
合成输入图像自包含，运行后在当前目录生成 cv_sharpen__preview.png。
"""
import cv2
import numpy as np

img = np.tile(np.linspace(30, 220, 480, dtype=np.uint8), (360, 1))
cv2.putText(img, "CV", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 4, 255, 12)

blur = cv2.GaussianBlur(img, (0, 0), 3)
result = cv2.addWeighted(img, 1.5, blur, -0.5, 0)
cv2.imwrite("cv_sharpen__preview.png", result if "result" in dir() else img)
print("已生成 cv_sharpen__preview.png")
