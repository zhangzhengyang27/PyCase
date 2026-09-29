"""图片转 PDF：Pillow 多页保存。"""
from PIL import Image

pages = []
for color in ("#e74c3c", "#2ecc71", "#3498db"):
    pages.append(Image.new("RGB", (595, 842), color))
pages[0].save("图片合集.pdf", save_all=True, append_images=pages[1:])
print("已生成 图片合集.pdf（3 页）")
