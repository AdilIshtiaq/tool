import email
import imaplib
import logging
from email.header import decode_header
from email.utils import parseaddr

from sqlalchemy.orm import Session

from app.services.ai_reply_classifier import ReplyClassificationError
from app.services.reply_execution import classify_message, find_lead_by_email, record_inbound_message

logger = logging.getLogger("nexcraft.imap")


class IMAPFetchError(Exception):
    pass


def _decode(value: str | None) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    decoded = ""
    for text, charset in parts:
        if isinstance(text, bytes):
            decoded += text.decode(charset or "utf-8", errors="replace")
        else:
            decoded += text
    return decoded


def _extract_body(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and not part.get_filename():
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
        return ""
    payload = msg.get_payload(decode=True)
    if payload:
        charset = msg.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace")
    return ""


def fetch_and_process_replies(
    db: Session,
    imap_host: str,
    imap_port: int,
    imap_user: str,
    imap_password: str,
    auto_classify: bool = True,
) -> dict:
    if not imap_host or not imap_user or not imap_password:
        raise IMAPFetchError("IMAP is not configured (host/user/password missing).")

    fetched = 0
    matched = 0
    unmatched = 0
    classified = 0
    classification_errors = 0
    unmatched_senders: list[str] = []

    try:
        conn = imaplib.IMAP4_SSL(imap_host, imap_port)
    except (OSError, TimeoutError) as exc:
        raise IMAPFetchError(f"Could not connect to IMAP server: {exc}") from exc

    try:
        try:
            conn.login(imap_user, imap_password)
        except imaplib.IMAP4.error as exc:
            raise IMAPFetchError(f"IMAP authentication failed: {exc}") from exc

        conn.select("INBOX")
        status, data = conn.search(None, "UNSEEN")
        if status != "OK":
            raise IMAPFetchError("IMAP search for unseen messages failed.")

        message_ids = data[0].split()
        for msg_id in message_ids:
            status, msg_data = conn.fetch(msg_id, "(RFC822)")
            if status != "OK" or not msg_data or not msg_data[0]:
                continue

            fetched += 1
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            _, from_email = parseaddr(msg.get("From"))
            subject = _decode(msg.get("Subject")) or "(no subject)"
            body = _extract_body(msg)

            lead = find_lead_by_email(db, from_email) if from_email else None
            if not lead:
                unmatched += 1
                unmatched_senders.append(from_email or "(unknown)")
                continue

            matched += 1
            message = record_inbound_message(db, lead, from_email, subject, body)

            if auto_classify:
                try:
                    classify_message(db, message)
                    classified += 1
                except ReplyClassificationError as exc:
                    classification_errors += 1
                    logger.warning("Could not classify inbound message %s: %s", message.id, exc)
    finally:
        try:
            conn.logout()
        except Exception:
            pass

    return {
        "fetched": fetched,
        "matched": matched,
        "unmatched": unmatched,
        "unmatched_senders": unmatched_senders,
        "classified": classified,
        "classification_errors": classification_errors,
    }
