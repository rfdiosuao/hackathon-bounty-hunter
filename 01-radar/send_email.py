#!/usr/bin/env python3
"""
黑客松雷达 - 邮件发送脚本
通过 SMTP 发送邮件（支持 QQ 邮箱等）
配置：config.json 中的 smtp 字段
"""

import json
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

WORK_DIR = Path(__file__).parent
CONFIG_FILE = WORK_DIR / "config.json"
HTML_FILE = WORK_DIR / "email_content.html"
TXT_FILE = WORK_DIR / "email_content.txt"


def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def send_email(subject: str, to_email: str, html_body: str, txt_body: str, smtp_config: dict) -> bool:
    """通过 SMTP 发送邮件"""
    smtp_server = smtp_config.get("server", "smtp.qq.com")
    smtp_port = smtp_config.get("port", 465)
    username = smtp_config.get("username", "")
    password = smtp_config.get("password", "")
    from_email = smtp_config.get("from_email", username)

    if not username or not password:
        print("错误：SMTP 未配置用户名或授权码", file=sys.stderr)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"黑客松雷达 <{from_email}>"
    msg["To"] = to_email

    msg.attach(MIMEText(txt_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
            server.starttls()
        server.login(username, password)
        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
        print(f"邮件发送成功 → {to_email}")
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}", file=sys.stderr)
        return False


def main():
    config = load_config()
    smtp_config = config.get("smtp", {})
    to_email = config.get("to_email", "rfdiosuao@qq.com")

    if not HTML_FILE.exists() or not TXT_FILE.exists():
        print("错误：邮件内容文件不存在，请先运行 generate_email.py", file=sys.stderr)
        sys.exit(1)

    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html_body = f.read()
    with open(TXT_FILE, "r", encoding="utf-8") as f:
        txt_body = f.read()

    subject = f"🚀 黑客松雷达 - 发现新比赛机会"

    success = send_email(subject, to_email, html_body, txt_body, smtp_config)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
