"""直方图均衡
OpenCV 图像处理：对比度增强。
示例用 numpy 程序化生成图像，自包含无需素材文件；运行后弹出结果窗口，按任意键退出。
"""
import cv2
import numpy as np


# 低对比度图像
img = np.zeros((300, 480), dtype=np.uint8)
cv2.circle(img, (150, 150), 90, 110, -1)
cv2.rectangle(img, (280, 80), (420, 230), 150, -1)
img = (img * 0.35 + 60).astype(np.uint8)

equalized = cv2.equalizeHist(img)

hist_before = cv2.calcHist([img], [0], None, [256], [0, 256])
hist_after = cv2.calcHist([equalized], [0], None, [256], [0, 256])
print("原图标准差: %.1f -> 均衡后: %.1f" % (img.std(), equalized.std()))

cv2.imshow("before", img)
cv2.imshow("after", equalized)
cv2.waitKey(0)
cv2.destroyAllWindows()
