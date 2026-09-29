"""批量函件：模板替换生成多份 Word。"""
from docx import Document

template = "尊敬的 {name}：\n\n    您在本系统的账号 {account} 已通过审核。\n\n运营团队"
members = [{"name": "张三", "account": "zs001"}, {"name": "李四", "account": "ls002"},
           {"name": "王五", "account": "ww003"}]
for m in members:
    doc = Document()
    doc.add_paragraph(template.format(**m))
    doc.save(f"函件_{m['account']}.docx")
print(f"已生成 {len(members)} 份函件")
