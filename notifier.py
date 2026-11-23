import os
import smtplib
from email.mime.text import MIMEText
from typing import List
from scrapers.models import JobPosting

def send_tmobile_sms(phone_digits: str, message: str, gmail_user: str, gmail_password: str) -> bool:
    """Send SMS via T-Mobile email-to-SMS gateway: [10-digits]@tmomail.net"""
    recipient = f"{phone_digits.strip()}@tmomail.net"
    msg = MIMEText(message, "plain", "utf-8")
    msg["From"] = gmail_user
    msg["To"] = recipient
    msg["Subject"] = ""  # Keep subject empty so SMS doesn't waste characters

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, [recipient], msg.as_string())
        print(f"[Notifier] SMS successfully sent to {recipient}")
        return True
    except Exception as e:
        print(f"[Notifier] Failed to send SMS via SMTP: {e}")
        return False

def format_sms_message(job: JobPosting) -> str:
    """Format a clean, concise SMS suitable for a phone screen."""
    return (
        f"🏥 {job.hospital}\n"
        f"💼 {job.title}\n"
        f"📍 {job.location}\n"
        f"⭐ New Grad: {'Yes' if job.is_new_grad_friendly else 'Check reqs'}\n"
        f"🔗 {job.url}"
    )

def notify_new_jobs(new_jobs: List[JobPosting], dry_run: bool = False):
    """Notify about new jobs. In dry-run or if credentials missing, logs to console."""
    phone = os.getenv("TMOBILE_NUMBER")
    user = os.getenv("GMAIL_USER")
    pw = os.getenv("GMAIL_APP_PASSWORD")

    if not new_jobs:
        print("[Notifier] No new jobs to notify.")
        return

    # Cap texts at 3 per run so we don't overwhelm her phone if a scraper imports 15 at once
    notifiable = [j for j in new_jobs if j.is_new_grad_friendly][:3]

    for job in notifiable:
        text = format_sms_message(job)
        if dry_run or not (phone and user and pw):
            print("\n--- [SMS PREVIEW (Dry-Run / Credentials not set)] ---")
            print(f"To: {phone or '[Phone not configured]'}@tmomail.net")
            print(text)
            print("----------------------------------------------------\n")
        else:
            send_tmobile_sms(phone, text, user, pw)
