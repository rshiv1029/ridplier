import os
import smtplib
import time
from email.mime.text import MIMEText
from typing import List
from scrapers.models import JobPosting

DEFAULT_DASHBOARD_URL = "https://rshiv1029.github.io/ridplier/"

def send_tmobile_sms(phone_digits: str, message: str, gmail_user: str, gmail_password: str) -> bool:
    """Send SMS via T-Mobile email-to-SMS gateway: [10-digits]@tmomail.net with fallback to STARTTLS"""
    recipient = f"{phone_digits.strip()}@tmomail.net"
    msg = MIMEText(message, "plain", "utf-8")
    msg["From"] = gmail_user
    msg["To"] = recipient
    msg["Subject"] = "Ridplier PA Job Alert"  # Non-empty subject prevents carrier spam filtering

    # Try Port 465 (SSL) first, then Port 587 (STARTTLS)
    for port, use_ssl in [(465, True), (587, False)]:
        try:
            print(f"[Notifier] Connecting to smtp.gmail.com:{port} ({'SSL' if use_ssl else 'STARTTLS'})...")
            if use_ssl:
                server = smtplib.SMTP_SSL("smtp.gmail.com", port, timeout=15)
            else:
                server = smtplib.SMTP("smtp.gmail.com", port, timeout=15)
                server.starttls()

            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, [recipient], msg.as_string())
            server.quit()
            print(f"[Notifier] ✅ SMS successfully delivered to gateway: {recipient}")
            return True
        except Exception as e:
            print(f"[Notifier] Attempt on port {port} failed: {e}")

    print(f"[Notifier] ❌ All SMTP attempts failed for {recipient}")
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
    Smart SMS notification (Max 2 texts to avoid T-Mobile carrier rate-limiting):
    - 1 job: Sends 1 direct-apply card.
    - 2 jobs: Sends 2 direct-apply cards.
    - 3+ jobs: Sends Card #1, then Card #2 with a summary footer & dashboard link attached.
    """
    phone = os.getenv("TMOBILE_NUMBER")
    user = os.getenv("GMAIL_USER")
    pw = os.getenv("GMAIL_APP_PASSWORD")
    dashboard_url = os.getenv("DASHBOARD_URL", DEFAULT_DASHBOARD_URL)

    # Diagnostic logging (safely masked)
    phone_preview = f"{phone[:3]}***" if phone else "not set"
    user_preview = f"{user[:3]}***" if user else "not set"
    pw_len = len(pw) if pw else 0
    print(f"[Notifier Diagnostic] TMOBILE_NUMBER: {phone_preview}")
    print(f"[Notifier Diagnostic] GMAIL_USER: {user_preview}")
    print(f"[Notifier Diagnostic] GMAIL_APP_PASSWORD: {pw_len} chars")

    if not new_jobs:
        print("[Notifier] No new jobs to notify.")
        return

    notifiable = [j for j in new_jobs if j.is_new_grad_friendly]
    if not notifiable:
        print("[Notifier] No new-grad eligible jobs to notify.")
        return

    if not (phone and user and pw):
        print("⚠️ [Notifier Warning] Credentials missing! TMOBILE_NUMBER, GMAIL_USER, or GMAIL_APP_PASSWORD not passed.")

    messages_to_send = []

    if len(notifiable) <= 2:
        for job in notifiable:
            messages_to_send.append(format_sms_message(job))
    else:
        # 1st text: Top job card
        messages_to_send.append(format_sms_message(notifiable[0]))

        # 2nd text: 2nd job card + summary footer with dashboard link
        remaining = notifiable[2:]
        summary_footer = format_batch_summary(remaining, dashboard_url)
        card_with_footer = f"{format_sms_message(notifiable[1])}\n\n{summary_footer}"
        messages_to_send.append(card_with_footer)

    for idx, text in enumerate(messages_to_send):
        if dry_run or not (phone and user and pw):
            print(f"\n--- [SMS PREVIEW {idx+1}/{len(messages_to_send)} (Dry-Run / Credentials not set)] ---")
            print(f"To: {phone or '[Phone not configured]'}@tmomail.net")
            print(text)
            print("--------------------------------------------------------------------------------\n")
        else:
            send_tmobile_sms(phone, text, user, pw)
            if idx < len(messages_to_send) - 1:
                time.sleep(5)  # 5s pause ensures T-Mobile's gateway delivers both in order without throttling
