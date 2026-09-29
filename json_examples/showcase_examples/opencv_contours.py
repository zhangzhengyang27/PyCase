"""轮廓检测
OpenCV 图像处理：面积过滤 + 质心标注。
示例用 numpy 程序化生成图像，自包含无需素材文件；运行后弹出结果窗口，按任意键退出。
"""
import cv2
import numpy as np


img = np.zeros((360, 480), dtype=np.uint8)
cv2.circle(img, (110, 110), 62, 255, -1)
cv2.rectangle(img, (260, 60), (380, 180), 255, -1)
cv2.ellipse(img, (150, 280), (70, 34), 20, 0, 360, 255, -1)
cv2.circle(img, (360, 280), 18, 255, -1)

contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
result = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
for c in contours:
    area = cv2.contourArea(c)
    if area < 800:  # 过滤小噪声
        continue
    M = cv2.moments(c)
    cx, cy = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
    cv2.drawContours(result, [c], -1, (80, 220, 120), 3)
    cv2.circle(result, (cx, cy), 4, (60, 90, 255), -1)
    cv2.putText(result, f"{int(area)}", (cx - 24, cy - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    print("轮廓面积:", int(area))

cv2.imshow("contours", result)
cv2.waitKey(0)
cv2.destroyAllWindows()
