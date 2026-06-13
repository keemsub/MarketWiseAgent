"""
이메일 전송 모듈
"""
import os
import smtplib
from email.message import EmailMessage
from config.settings import (
    GMAIL_EMAIL,
    GMAIL_PASSWORD,
    GMAIL_SMTP_SERVER,
    GMAIL_SMTP_PORT,
    GMAIL_RECIPIENT
)


def send_to_email(message_text: str, subject: str = None) -> bool:
    """Send an email with the provided plain text body and subject."""
    if not GMAIL_EMAIL or not GMAIL_PASSWORD:
        print("⚠️ Gmail 설정이 누락되었습니다. .env 파일에 GMAIL_EMAIL과 GMAIL_PASSWORD를 설정해주세요.")
        return False

    recipient = GMAIL_RECIPIENT or GMAIL_EMAIL
    subject = subject or "미국 증시 뉴스 분석 보고서"

    email_message = EmailMessage()
    email_message["Subject"] = subject
    email_message["From"] = GMAIL_EMAIL
    email_message["To"] = recipient
    email_message.set_content(message_text)

    try:
        with smtplib.SMTP(GMAIL_SMTP_SERVER, GMAIL_SMTP_PORT, timeout=20) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(GMAIL_EMAIL, GMAIL_PASSWORD)
            smtp.send_message(email_message)

        print("✅ 이메일 전송 성공!")
        return True
    except Exception as e:
        print(f"❌ 이메일 전송 실패: {e}")
        return False
