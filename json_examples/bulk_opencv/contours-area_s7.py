"""轮廓筛选（竖条纹）
OpenCV 图像处理示例。按面积过滤轮廓并标注质心。
合成输入图像自包含，运行后在当前目录生成 cv_contours-area__preview.png。
"""
import cv2
import numpy as np

img = np.zeros((360, 480), dtype=np.uint8)
for x in range(0, 480, 24):
    cv2.rectangle(img, (x, 0), (x + 10, 360), 220, -1)
cv2.circle(img, (240, 180), 70, 90, -1)

_, th = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)
contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
result = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
for c in contours:
    area = cv2.contourArea(c)
    if area < {{min_area}}:
        continue
    M = cv2.moments(c)
    if M["m00"]:
        cv2.drawContours(result, [c], -1, (80, 220, 120), 2)
        cv2.circle(result, (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])), 3, (60, 90, 255), -1)
cv2.imwrite("cv_contours-area__preview.png", result if "result" in dir() else img)
print("已生成 cv_contours-area__preview.png")
