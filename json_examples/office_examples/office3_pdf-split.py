"""PDF 拆分：每页一个文件。"""
import io
from pypdf import PdfReader, PdfWriter

buf = io.BytesIO()
w = PdfWriter()
for _ in range(3):
    w.add_blank_page(width=595, height=842)
w.write(buf)
buf.seek(0)

reader = PdfReader(buf)
for i, page in enumerate(reader.pages):
    out = PdfWriter()
    out.add_page(page)
    with open(f"第{i + 1}页.pdf", "wb") as f:
        out.write(f)
print(f"已拆分为 {len(reader.pages)} 个单页 PDF")
