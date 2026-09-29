"""轮廓筛选（棋盘场景）
OpenCV 图像处理示例。按面积过滤轮廓并标注质心。
合成输入图像自包含，运行后在当前目录生成 cv_contours-area__preview.png。
"""
import cv2
import numpy as np

img = np.kron(np.indices((9, 12)).sum(0) % 2, np.uint8(255))[:360, :480].astype(np.uint8) * 0
img[::40, :] = 120; img[:, ::40] = 120
cv2.rectangle(img, (100, 100), (380, 260), 255, -1)

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
