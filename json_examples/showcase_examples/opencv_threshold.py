"""阈值分割
OpenCV 图像处理：Otsu 与自适应阈值。
示例用 numpy 程序化生成图像，自包含无需素材文件；运行后弹出结果窗口，按任意键退出。
"""
import cv2
import numpy as np


# 合成光照不均的渐变背景 + 字符
img = np.zeros((300, 480), dtype=np.uint8)
grad = np.linspace(40, 200, 480, dtype=np.uint8)[None, :]
img[:] = grad
cv2.putText(img, "THRESHOLD", (30, 180), cv2.FONT_HERSHEY_SIMPLEX, 2.2, 255, 10)
noise = np.random.randint(0, 12, img.shape, dtype=np.uint8)
img = cv2.add(img, noise)

_, otsu = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
adaptive = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY, 25, 8)

cv2.imshow("original", img)
cv2.imshow("otsu", otsu)
cv2.imshow("adaptive", adaptive)
cv2.waitKey(0)
cv2.destroyAllWindows()
