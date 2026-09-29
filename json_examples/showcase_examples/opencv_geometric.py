"""几何变换
OpenCV 图像处理：warpAffine 变换矩阵。
示例用 numpy 程序化生成图像，自包含无需素材文件；运行后弹出结果窗口，按任意键退出。
"""
import cv2
import numpy as np


img = np.zeros((360, 480, 3), dtype=np.uint8)
cv2.putText(img, "CV", (120, 240), cv2.FONT_HERSHEY_SIMPLEX, 5, (180, 220, 255), 14)

rows, cols = img.shape[:2]
M_shift = np.float32([[1, 0, 60], [0, 1, 30]])
shifted = cv2.warpAffine(img, M_shift, (cols, rows))

M_rot = cv2.getRotationMatrix2D((cols / 2, rows / 2), 30, 0.8)
rotated = cv2.warpAffine(img, M_rot, (cols, rows))

resized = cv2.resize(img, None, fx=0.6, fy=0.6, interpolation=cv2.INTER_AREA)

cv2.imshow("shifted", shifted)
cv2.imshow("rotated", rotated)
cv2.imshow("resized", resized)
cv2.waitKey(0)
cv2.destroyAllWindows()
