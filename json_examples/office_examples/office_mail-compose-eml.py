"""邮件构造：生成 .eml 文件（不实际发送）。"""
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from pathlib import Path

msg = MIMEMultipart()
msg["From"] = "report-bot@example.com"
msg["To"] = "boss@example.com"
msg["Subject"] = "【自动】运营日报 2026-09-23"
msg["Date"] = formatdate(localtime=True)
msg.attach(MIMEText("各位好，\n\n今日数据请见附件（演示正文）。\n\n-- 自动报表机器人", "plain", "utf-8"))
Path("日报邮件.eml").write_bytes(msg.as_bytes())
print("已生成 日报邮件.eml（可用邮件客户端打开预览）")
