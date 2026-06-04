import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


def send_budget_alert_email(to_email: str, username: str, alerts: list, month: int, year: int):
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_user or not smtp_password:
        return

    triggered = [a for a in alerts if a["status"] in ("warning", "exceeded")]
    if not triggered:
        return

    month_name = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ][month - 1]

    rows = ""
    for a in triggered:
        emoji = "🚨" if a["status"] == "exceeded" else "⚠️"
        label = "EXCEEDED" if a["status"] == "exceeded" else "WARNING"
        color = "#ef4444" if a["status"] == "exceeded" else "#f59e0b"
        rows += f"""
        <tr>
            <td style="padding:10px;border-bottom:1px solid #2a2a45;">{emoji} {a['category']}</td>
            <td style="padding:10px;border-bottom:1px solid #2a2a45;">${a['spent']:.2f}</td>
            <td style="padding:10px;border-bottom:1px solid #2a2a45;">${a['budget_limit']:.2f}</td>
            <td style="padding:10px;border-bottom:1px solid #2a2a45;">{a['percentage_used']:.1f}%</td>
            <td style="padding:10px;border-bottom:1px solid #2a2a45;color:{color};font-weight:bold;">{label}</td>
        </tr>"""

    html = f"""
    <html>
    <body style="background:#0f0f1a;color:#e2e8f0;font-family:Inter,sans-serif;padding:32px;">
        <div style="max-width:560px;margin:0 auto;background:#1a1a2e;border:1px solid #2a2a45;border-radius:12px;padding:32px;">
            <h2 style="color:#4361ee;margin-top:0;">💸 Budget Alert — {month_name} {year}</h2>
            <p>Hi <strong>{username}</strong>,</p>
            <p>One or more of your budgets need attention this month:</p>
            <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                <thead>
                    <tr style="background:#0f0f1a;color:#6b7280;font-size:12px;text-transform:uppercase;">
                        <th style="padding:10px;text-align:left;">Category</th>
                        <th style="padding:10px;text-align:left;">Spent</th>
                        <th style="padding:10px;text-align:left;">Limit</th>
                        <th style="padding:10px;text-align:left;">Used</th>
                        <th style="padding:10px;text-align:left;">Status</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
            <p style="color:#6b7280;font-size:13px;margin-top:24px;">
                Log in to your <a href="http://localhost:8000" style="color:#4361ee;">Expense Tracker</a> to review and adjust your budgets.
            </p>
        </div>
    </body>
    </html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"⚠️ Budget Alert — {month_name} {year} | Expense Tracker"
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to_email, msg.as_string())
    except Exception as e:
        print(f"[Email] Failed to send budget alert: {e}")
