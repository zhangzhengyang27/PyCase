"""颜色空间
OpenCV 图像处理：HSV 阈值分割红色区域。
示例用 numpy 程序化生成图像，自包含无需素材文件；运行后弹出结果窗口，按任意键退出。
"""
import cv2
import numpy as np


canvas = np.zeros((320, 480, 3), dtype=np.uint8)
cv2.circle(canvas, (120, 160), 70, (60, 60, 230), -1)     # 红色圆
cv2.rectangle(canvas, (260, 90), (420, 230), (90, 200, 90), -1)  # 绿色方块

hsv = cv2.cvtColor(canvas, cv2.COLOR_BGR2HSV)
gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)

# HSV 中红色的两段阈值
mask1 = cv2.inRange(hsv, (0, 120, 120), (8, 255, 255))
mask2 = cv2.inRange(hsv, (170, 120, 120), (180, 255, 255))
red_mask = cv2.bitwise_or(mask1, mask2)
red_only = cv2.bitwise_and(canvas, canvas, mask=red_mask)

cv2.imshow("original", canvas)
cv2.imshow("gray", gray)
cv2.imshow("red_mask", red_mask)
cv2.imshow("red_only", red_only)
cv2.waitKey(0)
cv2.destroyAllWindows()
