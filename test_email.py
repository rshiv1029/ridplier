#!/usr/bin/env python3
"""
Quick utility to test Direct Email Alert delivery to your inbox.
Usage:
  python test_email.py
"""
import getpass
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def test_email():
    print("=" * 60)
    print("📧 Ridplier Direct Email Live Test")
    print("=" * 60)

    recipient = os.getenv("ALERT_EMAIL")
    if not recipient:
        recipient = input("Enter recipient email address (e.g. hername@gmail.com): ").strip()

    gmail_user = os.getenv("GMAIL_USER")
    if not gmail_user:
        gmail_user = input("Enter your sender Gmail address (e.g. you@gmail.com): ").strip()

    gmail_pass = os.getenv("GMAIL_APP_PASSWORD")
    if not gmail_pass:
        gmail_pass = getpass.getpass("Enter your 16-char Google App Password: ").strip()

    gmail_pass = gmail_pass.replace(" ", "")

    msg = MIMEMultipart("alternative")
    msg["From"] = f"Ridplier PA Alerts <{gmail_user}>"
    msg["To"] = recipient
    msg["Subject"] = "🏥 New PA Job: Adventist HealthCare - Orthopedic Surgery (Rockville, MD)"

    html_content = """
    <div style="background-color: #0f172a; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, sans-serif; color: #ffffff;">
      <div style="max-width: 500px; margin: 0 auto; background-color: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155;">
        <div style="color: #38bdf8; font-weight: 700; text-transform: uppercase; font-size: 13px; margin-bottom: 6px;">
          Adventist HealthCare (Shady Grove / Rockville)
        </div>
        <h2 style="margin: 0 0 10px; color: #ffffff; font-size: 20px;">
          Physician Assistant (PA) - Orthopedic Surgery
        </h2>
        <p style="color: #94a3b8; font-size: 14px; margin: 0 0 16px;">
          📍 Rockville, MD (10 mins from Germantown) | 💼 Full-Time
        </p>
        <div style="background: rgba(16, 185, 129, 0.2); color: #34d399; display: inline-block; padding: 6px 12px; border-radius: 6px; font-weight: 600; font-size: 13px; margin-bottom: 20px;">
          ⭐ New Grad Friendly
        </div>
        <div>
          <a href="https://adventisthealthcare.wd1.myworkdayjobs.com/en-US/AdventistHealthCareCareers/job/Rockville-MD/Physician-Assistant--PA---Rotating-Shift--Orthopedic-Surgery_R-043546" 
             style="background-color: #38bdf8; color: #0f172a; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: 700; display: inline-block;">
            Apply on Hospital Site &rarr;
          </a>
        </div>
      </div>
    </div>
    """
    msg.attach(MIMEText("Physician Assistant - Orthopedic Surgery in Rockville, MD", "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    print(f"\n[Connecting] Sending test email alert to {recipient}...")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, [recipient], msg.as_string())
        print("\n" + "=" * 60)
        print("🎉 SUCCESS! Direct email alert sent successfully.")
        print(f"Check the inbox/notification banner on {recipient}!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Failed to send email: {e}")

if __name__ == "__main__":
    test_email()
