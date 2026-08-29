"""
Email sending for verification and password reset.

If SMTP isn't configured (smtp_username is blank), emails are printed to
the backend console instead of sent - the verification/reset flow works
end to end with zero setup this way, which matters for actually being able
to test and use this feature immediately. Fill in real SMTP settings in
.env whenever you want real delivery; nothing else about the flow changes.

Uses Python's built-in smtplib rather than a third-party email service SDK,
so there's no extra dependency and no vendor lock-in - any SMTP provider
(Gmail, SendGrid's SMTP relay, Mailgun's SMTP relay, etc.) works the same way.
"""

import smtplib
from email.mime.text import MIMEText

from app.config import get_settings

settings = get_settings()


def send_email(to: str, subject: str, body: str) -> None:
    if not settings.smtp_username:
        print(f"\n--- DEV MODE: email not sent (no SMTP configured) ---")
        print(f"To: {to}\nSubject: {subject}\n\n{body}")
        print("--- end email ---\n")
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from or settings.smtp_username
    msg["To"] = to

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)


def send_verification_email(to: str, token: str) -> None:
    link = f"{settings.frontend_url}/verify-email?token={token}"
    send_email(
        to=to,
        subject="Verify your CareerPilot AI email",
        body=(
            f"Welcome to CareerPilot AI!\n\n"
            f"Verify your email by opening this link:\n{link}\n\n"
            f"This link expires in 24 hours."
        ),
    )


def send_password_reset_email(to: str, token: str) -> None:
    link = f"{settings.frontend_url}/reset-password?token={token}"
    send_email(
        to=to,
        subject="Reset your CareerPilot AI password",
        body=(
            f"Someone (hopefully you) requested a password reset.\n\n"
            f"Reset your password by opening this link:\n{link}\n\n"
            f"This link expires in 1 hour. If you didn't request this, "
            f"you can safely ignore this email."
        ),
    )
