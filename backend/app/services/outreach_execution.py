import re
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AuditLog, Lead, Message, ServiceRecommendation, SuppressedEmail
from app.services.crm import record_stage_change
from app.services.email_sender import EmailSendError, send_email
from app.services.personalization import build_personalization_context, personalize

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class OutreachValidationError(Exception):
    pass


def get_latest_recommendation(db: Session, lead_id) -> ServiceRecommendation | None:
    return db.scalar(
        select(ServiceRecommendation)
        .where(ServiceRecommendation.lead_id == lead_id)
        .order_by(ServiceRecommendation.created_at.desc())
        .limit(1)
    )


def build_preview(db: Session, lead: Lead, subject: str, body: str) -> dict:
    recommendation = get_latest_recommendation(db, lead.id)
    context = build_personalization_context(lead, recommendation)
    return {
        "to_email": lead.email,
        "subject": personalize(subject, context),
        "body": personalize(body, context),
    }


def validate_can_send(db: Session, lead: Lead, is_test: bool) -> None:
    if not lead.email:
        raise OutreachValidationError("This lead has no email address.")
    if not EMAIL_REGEX.match(lead.email):
        raise OutreachValidationError(f"'{lead.email}' is not a valid email address.")

    suppressed = db.scalar(
        select(SuppressedEmail).where(SuppressedEmail.email == lead.email.lower())
    )
    if suppressed:
        raise OutreachValidationError(
            f"'{lead.email}' is suppressed ({suppressed.reason}) and cannot receive outreach."
        )

    if not is_test:
        already_sent = db.scalar(
            select(Message).where(
                Message.lead_id == lead.id,
                Message.to_email == lead.email,
                Message.status == "accepted_by_provider",
            )
        )
        if already_sent:
            raise OutreachValidationError(
                "An email has already been sent to this lead. Duplicate sends are blocked."
            )


def send_outreach(
    db: Session,
    lead: Lead,
    subject: str,
    body: str,
    template_id=None,
    campaign_id=None,
    is_test: bool = False,
    test_email_override: str | None = None,
) -> Message:
    settings = get_settings()
    validate_can_send(db, lead, is_test)

    recommendation = get_latest_recommendation(db, lead.id)
    context = build_personalization_context(lead, recommendation)
    final_subject = personalize(subject, context)
    final_body = personalize(body, context)
    to_email = test_email_override if is_test and test_email_override else lead.email

    message = Message(
        lead_id=lead.id,
        template_id=template_id,
        campaign_id=campaign_id,
        direction="outbound",
        to_email=to_email,
        subject=final_subject,
        body=final_body,
        status="sending",
        is_test=is_test,
    )
    db.add(message)
    db.flush()

    try:
        provider_response = send_email(
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            smtp_user=settings.smtp_user,
            smtp_password=settings.smtp_password,
            from_name=settings.smtp_from_name,
            to_email=to_email,
            subject=final_subject,
            body=final_body,
        )
        message.status = "accepted_by_provider"
        message.provider_response = provider_response
        message.sent_at = datetime.utcnow()
    except EmailSendError as exc:
        message.status = "failed"
        message.provider_response = str(exc)

    if is_test:
        action = "outreach_test_send"
    elif campaign_id:
        action = "outreach_campaign_send"
    else:
        action = "outreach_send"

    db.add(
        AuditLog(
            action=action,
            entity_type="lead",
            entity_id=str(lead.id),
            detail={"message_id": str(message.id), "status": message.status, "to": to_email},
        )
    )

    if not is_test and message.status == "accepted_by_provider":
        record_stage_change(db, lead, "contacted", reason="Outreach email sent")

    db.commit()
    db.refresh(message)
    return message
