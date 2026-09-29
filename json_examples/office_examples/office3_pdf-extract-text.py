"""PDF 文本提取。"""
from pypdf import PdfReader
from pypdf import PdfWriter
import io

buf = io.BytesIO()
w = PdfWriter()
page = w.add_blank_page(width=595, height=842)
w.write(buf); buf.seek(0)
reader = PdfReader(buf)
for i, page in enumerate(reader.pages):
    text = page.extract_text() or ""
    print(f"第{i + 1}页文本长度: {len(text)}（空白页为 0）")
