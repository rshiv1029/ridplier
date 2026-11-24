import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List
from scrapers.models import JobPosting

DEFAULT_DASHBOARD_URL = "https://rshiv1029.github.io/ridplier/"

def format_email_html(jobs: List[JobPosting], dashboard_url: str) -> str:
    """Generate a clean, mobile-optimized HTML email card for iPhone Mail / Gmail."""
    cards_html = ""
    for j in jobs:
        prob = j.probability or "moderate"
        if prob == "high":
            badge_bg = "rgba(16, 185, 129, 0.15)"
            badge_color = "#34d399"
            badge_border = "rgba(16, 185, 129, 0.4)"
            badge_label = "🟢 High Chance (New Grad Welcome)"
        elif prob == "lower":
            badge_bg = "rgba(249, 115, 22, 0.15)"
            badge_color = "#fb923c"
            badge_border = "rgba(249, 115, 22, 0.4)"
            badge_label = "🟠 Lower Chance (2+ Yrs Preferred)"
        else:
            badge_bg = "rgba(245, 158, 11, 0.15)"
            badge_color = "#fbbf24"
            badge_border = "rgba(245, 158, 11, 0.4)"
            badge_label = "🟡 Moderate Chance (1 Yr / Standard)"

        cards_html += f"""
        <div style="background-color: #1e293b; border-radius: 10px; padding: 18px; margin-bottom: 16px; border: 1px solid #334155;">
          <div style="color: #38bdf8; font-size: 13px; font-weight: 600; text-transform: uppercase; margin-bottom: 4px;">
            {j.hospital}
          </div>
          <div style="color: #ffffff; font-size: 18px; font-weight: 700; margin-bottom: 8px;">
            {j.title}
          </div>
          <div style="color: #94a3b8; font-size: 14px; margin-bottom: 12px;">
            📍 {j.location} &nbsp;|&nbsp; 📅 {j.posted_date} &nbsp;|&nbsp; 💼 Full-Time
          </div>
          <div style="background-color: {badge_bg}; color: {badge_color}; border: 1px solid {badge_border}; font-size: 13px; font-weight: 700; padding: 6px 12px; border-radius: 6px; display: inline-block; margin-bottom: 10px;">
            {badge_label}
          </div>
          <div style="color: #cbd5e1; font-size: 13px; margin-bottom: 16px; background-color: rgba(0,0,0,0.25); padding: 8px 12px; border-radius: 6px;">
            💡 <strong>Match Signal:</strong> {j.match_reason}
          </div>
          <div>
            <a href="{j.url}" style="background-color: #38bdf8; color: #0f172a; text-decoration: none; padding: 10px 20px; border-radius: 6px; font-weight: 700; font-size: 14px; display: inline-block;">
              Apply on Hospital Site &rarr;
            </a>
          </div>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
    <body style="margin: 0; padding: 20px; background-color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
      <div style="max-width: 600px; margin: 0 auto;">
        <div style="text-align: center; margin-bottom: 24px;">
          <h1 style="color: #38bdf8; margin: 0 0 6px; font-size: 24px;">🩺 Ridplier PA Alert</h1>
          <p style="color: #94a3b8; margin: 0; font-size: 14px;">Fresh new-grad friendly hospital jobs just posted</p>
        </div>

        {cards_html}

        <div style="text-align: center; margin-top: 24px; padding-top: 20px; border-top: 1px solid #334155;">
          <p style="color: #94a3b8; font-size: 14px; margin-bottom: 12px;">Want to browse all active jobs?</p>
          <a href="{dashboard_url}" style="color: #38bdf8; font-weight: 600; text-decoration: underline; font-size: 15px;">
            Open Your Ridplier Live Dashboard &rarr;
          </a>
        </div>
      </div>
    </body>
    </html>
    """

def format_email_plain(jobs: List[JobPosting], dashboard_url: str) -> str:
    """Plain-text fallback for email clients."""
    out = [f"🩺 Ridplier: {len(jobs)} New PA Job(s) Found!\n"]
    for j in jobs:
        out.append(
            f"🏥 {j.hospital}\n"
            f"💼 {j.title}\n"
            f"📍 {j.location} (Full-Time)\n"
            f"⭐ {j.match_reason}\n"
            f"🔗 Apply: {j.url}\n"
            f"{'-' * 40}\n"
        )
    out.append(f"View all open listings on Ridplier:\n{dashboard_url}")
    return "\n".join(out)

def send_email_alert(recipient: str, jobs: List[JobPosting], dashboard_url: str, gmail_user: str, gmail_password: str) -> bool:
    """Send rich HTML email alert directly to her inbox."""
    msg = MIMEMultipart("alternative")
    msg["From"] = f"Ridplier PA Alerts <{gmail_user}>"
    msg["To"] = recipient

    if len(jobs) == 1:
        msg["Subject"] = f"🏥 New PA Job: {jobs[0].hospital} - {jobs[0].title}"
    else:
        msg["Subject"] = f"🩺 {len(jobs)} New PA Jobs Posted ({jobs[0].hospital} & more)"

    plain_part = MIMEText(format_email_plain(jobs, dashboard_url), "plain", "utf-8")
    html_part = MIMEText(format_email_html(jobs, dashboard_url), "html", "utf-8")

    msg.attach(plain_part)
    msg.attach(html_part)

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
            print(f"[Notifier] ✅ Email alert successfully delivered to {recipient}!")
            return True
        except Exception as e:
            print(f"[Notifier] Port {port} error: {e}")

    print(f"[Notifier] ❌ All email attempts failed for {recipient}")
    return False

def notify_new_jobs(new_jobs: List[JobPosting], dry_run: bool = False):
    """Notify about new jobs via Email (primary) or T-Mobile SMS."""
    # Check for direct email recipient first (ALERT_EMAIL)
    alert_email = os.getenv("ALERT_EMAIL")
    phone = os.getenv("TMOBILE_NUMBER")
    user = os.getenv("GMAIL_USER")
    pw = os.getenv("GMAIL_APP_PASSWORD")
    dashboard_url = os.getenv("DASHBOARD_URL", DEFAULT_DASHBOARD_URL)

    # Determine recipient: ALERT_EMAIL takes priority; fallback to TMOBILE_NUMBER
    recipient = alert_email or (f"{phone.strip()}@tmomail.net" if phone else None)

    # Diagnostic logging (safely masked)
    recip_preview = f"{recipient[:3]}***@{recipient.split('@')[-1]}" if recipient and "@" in recipient else "not set"
    user_preview = f"{user[:3]}***" if user else "not set"
    pw_len = len(pw) if pw else 0
    print(f"[Notifier Diagnostic] Recipient: {recip_preview}")
    print(f"[Notifier Diagnostic] Sender: {user_preview}")
    print(f"[Notifier Diagnostic] Password: {pw_len} chars")

    if not new_jobs:
        print("[Notifier] No new jobs to notify.")
        return

    notifiable = [j for j in new_jobs if j.is_new_grad_friendly]
    if not notifiable:
        print("[Notifier] No new-grad eligible jobs to notify.")
        return

    if not (recipient and user and pw):
        print("⚠️ [Notifier Warning] Missing credentials or recipient! (ALERT_EMAIL or TMOBILE_NUMBER required)")
        dry_run = True

    if dry_run or not (recipient and user and pw):
        print(f"\n--- [EMAIL ALERT PREVIEW (To: {recipient})] ---")
        print(format_email_plain(notifiable, dashboard_url))
        print("------------------------------------------------\n")
    else:
        # Include all new eligible postings in the email digest
        send_email_alert(recipient, notifiable, dashboard_url, user, pw)
