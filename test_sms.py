#!/usr/bin/env python3
"""
Quick utility to test T-Mobile SMS delivery to your phone.
Usage:
  python test_sms.py
  (Prompts interactively for phone number, Gmail address, and App Password)
"""
import getpass
import os
import smtplib
from email.mime.text import MIMEText

def test_sms():
    print("=" * 60)
    print("📱 Ridplier T-Mobile SMS Live Test")
    print("=" * 60)

    # 1. Gather credentials (from env, or interactive prompt)
    phone = os.getenv("TMOBILE_NUMBER")
    if not phone:
        phone = input("Enter your 10-digit T-Mobile phone number (e.g. 2401234567): ").strip()
    phone = "".join(filter(str.isdigit, phone))
    if len(phone) != 10:
        print("❌ Error: Phone number must be exactly 10 digits.")
        return

    gmail_user = os.getenv("GMAIL_USER")
    if not gmail_user:
        gmail_user = input("Enter your Gmail address (e.g. you@gmail.com): ").strip()

    gmail_pass = os.getenv("GMAIL_APP_PASSWORD")
    if not gmail_pass:
        print("\nNote: Use a 16-character Google App Password (not your normal Gmail password).")
        print("Generate one at: https://myaccount.google.com/apppasswords")
        gmail_pass = getpass.getpass("Enter your 16-char Google App Password: ").strip()

    # Remove any spaces in app password
    gmail_pass = gmail_pass.replace(" ", "")

    recipient = f"{phone}@tmomail.net"

    # Sample real direct job alert from Adventist Shady Grove (Rockville, MD)
    message = (
        "🏥 Adventist HealthCare\n"
        "💼 Physician Assistant (PA) - Orthopedic Surgery\n"
        "📍 Rockville, MD (Shady Grove)\n"
        "⭐ New Grad: Yes\n"
        "🔗 https://adventisthealthcare.wd1.myworkdayjobs.com/en-US/AdventistHealthCareCareers/job/Rockville-MD/Physician-Assistant--PA---Rotating-Shift--Orthopedic-Surgery_R-043546"
    )

    msg = MIMEText(message, "plain", "utf-8")
    msg["From"] = gmail_user
    msg["To"] = recipient
    msg["Subject"] = ""

    print(f"\n[Connecting] Sending test SMS to {recipient} via Gmail SMTP...")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, [recipient], msg.as_string())
        
        print("\n" + "=" * 60)
        print("🎉 SUCCESS! Text message dispatched.")
        print(f"Check your T-Mobile phone ({phone}) in the next 10-30 seconds.")
        print("=" * 60)
    except smtplib.SMTPAuthenticationError:
        print("\n❌ Authentication Failed!")
        print("Make sure you are using a 16-character Google App Password with 2-Step Verification enabled.")
        print("Link: https://myaccount.google.com/apppasswords")
    except Exception as e:
        print(f"\n❌ Failed to send SMS: {e}")

if __name__ == "__main__":
    test_sms()
