"""Canny 边缘检测
OpenCV 图像处理：梯度与双阈值边缘提取。
示例用 numpy 程序化生成图像，自包含无需素材文件；运行后弹出结果窗口，按任意键退出。
"""
import cv2
import numpy as np


img = np.zeros((360, 480), dtype=np.uint8)
cv2.rectangle(img, (60, 60), (200, 200), 200, -1)
cv2.circle(img, (340, 140), 80, 140, -1)
cv2.line(img, (40, 300), (440, 320), 220, 6)
cv2.GaussianBlur(img, (5, 5), 0, dst=img)

sobel = cv2.Sobel(img, cv2.CV_64F, 1, 1, ksize=3)
sobel = np.clip(np.abs(sobel), 0, 255).astype(np.uint8)
canny = cv2.Canny(img, 60, 150)

cv2.imshow("original", img)
cv2.imshow("sobel", sobel)
cv2.imshow("canny", canny)
cv2.waitKey(0)
cv2.destroyAllWindows()
