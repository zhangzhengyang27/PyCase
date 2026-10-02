"""轮廓筛选（大字报）
OpenCV 图像处理示例。按面积过滤轮廓并标注质心。
合成输入图像自包含，运行后在当前目录生成 cv_contours-area__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
cv2.putText(img, "OPEN CV", (40, 210), cv2.FONT_HERSHEY_SIMPLEX, 2.6, 220, 12)
cv2.rectangle(img, (30, 30), (450, 330), 160, 5)

_, th = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)
contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
result = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
for c in contours:
    area = cv2.contourArea(c)
    if area < 120:
        continue
    M = cv2.moments(c)
    if M["m00"]:
        cv2.drawContours(result, [c], -1, (80, 220, 120), 2)
        cv2.circle(result, (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])), 3, (60, 90, 255), -1)
cv2.imwrite("cv_contours-area__preview.png", result if "result" in dir() else img)
print("已生成 cv_contours-area__preview.png")
