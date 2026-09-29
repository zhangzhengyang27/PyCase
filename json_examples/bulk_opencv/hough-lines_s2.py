"""霍夫直线（渐变场景）
OpenCV 图像处理示例。概率霍夫变换检测线段。
合成输入图像自包含，运行后在当前目录生成 cv_hough-lines__preview.png。
"""
import cv2
import numpy as np

img = np.tile(np.linspace(30, 220, 480, dtype=np.uint8), (360, 1))
cv2.putText(img, "CV", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 4, 255, 12)

edges = cv2.Canny(img, 80, 160)
lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 60, minLineLength=30, maxLineGap=8)
result = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
if lines is not None:
    for l in lines[:40]:
        cv2.line(result, tuple(l[0][:2]), tuple(l[0][2:]), (90, 200, 255), 1)
cv2.imwrite("cv_hough-lines__preview.png", result if "result" in dir() else img)
print("已生成 cv_hough-lines__preview.png")
