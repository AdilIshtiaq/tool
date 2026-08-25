import smtplib
import ssl
from email.mime.text import MIMEText
from email.utils import formataddr


class EmailSendError(Exception):
    pass


def send_email(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    from_name: str,
    to_email: str,
    subject: str,
    body: str,
) -> str:
    """Sends via SMTP and returns the provider's raw response. Does not assume delivery —
    only that the provider accepted the message for sending."""
    if not smtp_host or not smtp_user or not smtp_password:
        raise EmailSendError("SMTP is not configured (host/user/password missing).")

    message = MIMEText(body, "plain")
    message["Subject"] = subject
    message["From"] = formataddr((from_name, smtp_user))
    message["To"] = to_email

    context = ssl.create_default_context()

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=20) as server:
                server.login(smtp_user, smtp_password)
                refused = server.sendmail(smtp_user, [to_email], message.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
                server.starttls(context=context)
                server.login(smtp_user, smtp_password)
                refused = server.sendmail(smtp_user, [to_email], message.as_string())
    except smtplib.SMTPAuthenticationError as exc:
        raise EmailSendError(f"SMTP authentication failed: {exc}") from exc
    except smtplib.SMTPException as exc:
        raise EmailSendError(f"SMTP error: {exc}") from exc
    except (OSError, TimeoutError) as exc:
        raise EmailSendError(f"Could not connect to SMTP server: {exc}") from exc

    if refused:
        raise EmailSendError(f"Recipient refused by server: {refused}")

    return "Accepted by SMTP server for delivery"
