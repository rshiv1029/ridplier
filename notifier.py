import os
import smtplib
import time
from email.mime.text import MIMEText
from typing import List
from scrapers.models import JobPosting

DEFAULT_DASHBOARD_URL = "https://rshiv1029.github.io/ridplier/"

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

def format_batch_summary(remaining_jobs: List[JobPosting], dashboard_url: str) -> str:
    """Format an informative summary message when more jobs dropped than the cap."""
    md_count = sum(1 for j in remaining_jobs if j.hub == "MD")
    nyc_count = sum(1 for j in remaining_jobs if j.hub == "NYC")

    breakdown = []
    if md_count > 0:
        breakdown.append(f"{md_count} in MD")
    if nyc_count > 0:
        breakdown.append(f"{nyc_count} in NYC")
    breakdown_str = f" ({', '.join(breakdown)})" if breakdown else ""

    return (
        f"🩺 Plus {len(remaining_jobs)} more new PA jobs dropped{breakdown_str}!\n"
        f"View & apply to all of them on Ridplier:\n"
        f"🔗 {dashboard_url}"
    )

def notify_new_jobs(new_jobs: List[JobPosting], dry_run: bool = False):
    """
    Smart SMS notification:
    - If 1 to 3 new jobs: sends individual direct-apply text cards.
    - If > 3 new jobs: sends top 2 direct cards + 1 smart summary text with the dashboard link.
    Never sends more than 3 texts per run.
    """
    phone = os.getenv("TMOBILE_NUMBER")
    user = os.getenv("GMAIL_USER")
    pw = os.getenv("GMAIL_APP_PASSWORD")
    dashboard_url = os.getenv("DASHBOARD_URL", DEFAULT_DASHBOARD_URL)

    if not new_jobs:
        print("[Notifier] No new jobs to notify.")
        return

    notifiable = [j for j in new_jobs if j.is_new_grad_friendly]
    if not notifiable:
        print("[Notifier] No new-grad eligible jobs to notify.")
        return

    messages_to_send = []

    if len(notifiable) <= 3:
        for job in notifiable:
            messages_to_send.append(format_sms_message(job))
    else:
        # Send top 2 individual job cards
        for job in notifiable[:2]:
            messages_to_send.append(format_sms_message(job))
        # 3rd text is a smart breakdown with the website link
        messages_to_send.append(format_batch_summary(notifiable[2:], dashboard_url))

    for idx, text in enumerate(messages_to_send):
        if dry_run or not (phone and user and pw):
            print(f"\n--- [SMS PREVIEW {idx+1}/{len(messages_to_send)} (Dry-Run / Credentials not set)] ---")
            print(f"To: {phone or '[Phone not configured]'}@tmomail.net")
            print(text)
            print("--------------------------------------------------------------------------------\n")
        else:
            send_tmobile_sms(phone, text, user, pw)
            time.sleep(2)  # brief pause so carrier SMS delivery preserves chronological order
