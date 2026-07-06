"""
Quick mail test - run: python test_mail.py
"""
import os
from dotenv import load_dotenv

load_dotenv()

import smtplib
from email.mime.text import MIMEText

server   = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
port     = int(os.environ.get("MAIL_PORT", 587))
username = os.environ.get("MAIL_USERNAME", "").strip()
password = os.environ.get("MAIL_PASSWORD", "").strip().replace(" ", "")
sender   = os.environ.get("MAIL_DEFAULT_SENDER", username)

print(f"Server   : {server}:{port}")
print(f"Username : {username}")
print(f"Password : {'*' * len(password)} ({len(password)} chars)")
print(f"Sender   : {sender}")

try:
    msg = MIMEText("Yeh ek test mail hai Placement Portal se.")
    msg["Subject"] = "Test Mail - Placement Portal"
    msg["From"]    = sender
    msg["To"]      = username  # apne aap ko hi bhej raha hai

    with smtplib.SMTP(server, port) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(msg)

    print("\n Mail sent successfully! Inbox check karo.")
except Exception as e:
    print(f"\nFAILED: {e}")
    print("\nPossible reasons:")
    print("  1. App Password galat hai - Google Account > Security > 2FA > App Passwords")
    print("  2. Less secure app access off hai")
    print("  3. 2-Factor Authentication enable nahi")
