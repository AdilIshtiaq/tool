from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AuditLog, Lead, Message, SuppressedEmail
from app.services.ai_reply_classifier import ReplyClassificationError, classify_reply
from app.services.crm import record_stage_change

# Per Module 5's stop rules — these categories mean automated follow-up must stop.
STOP_CATEGORIES = {"Unsubscribe", "Negative", "Invalid"}

CRM_STAGE_BY_CATEGORY = {
    "Positive": "interested",
    "Interested": "interested",
    "Question": "interested",
    "Follow-up": "follow_up",
    "Neutral": "contacted",
    "Negative": "lost",
    "Unsubscribe": "lost",
    "Out of office": "contacted",
    "Invalid": "contacted",
}


def find_lead_by_email(db: Session, email: str) -> Lead | None:
    return db.scalar(select(Lead).where(Lead.email == email))


def record_inbound_message(db: Session, lead: Lead, from_email: str, subject: str, body: str) -> Message:
    message = Message(
        lead_id=lead.id,
        direction="inbound",
        from_email=from_email,
        to_email=None,
        subject=subject,
        body=body,
        status="received",
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def classify_message(db: Session, message: Message) -> Message:
    settings = get_settings()

    try:
        result = classify_reply(
            openai_api_key=settings.openai_api_key,
            anthropic_api_key=settings.anthropic_api_key,
            from_email=message.from_email or "",
            subject=message.subject,
            body=message.body,
        )
    except ReplyClassificationError:
        raise

    message.category = result["category"]
    message.classification_confidence = result["confidence"]
    message.classification_summary = result["summary"]
    message.suggested_action = result["suggested_action"]
    message.review_required = result["review_required"]

    lead = message.lead

    db.add(
        AuditLog(
            action="ai_reply_classification",
            entity_type="message",
            entity_id=str(message.id),
            detail={
                "category": result["category"],
                "confidence": result["confidence"],
                "review_required": result["review_required"],
            },
        )
    )
    if result["category"] in STOP_CATEGORIES:
        if lead.email and result["category"] in ("Unsubscribe", "Invalid"):
            existing = db.scalar(select(SuppressedEmail).where(SuppressedEmail.email == lead.email))
            if not existing:
                db.add(
                    SuppressedEmail(
                        email=lead.email,
                        reason=f"Reply classified as {result['category']}",
                    )
                )
        db.add(
            AuditLog(
                action="followup_stopped",
                entity_type="lead",
                entity_id=str(lead.id),
                detail={"reason": result["category"], "message_id": str(message.id)},
            )
        )

    new_stage = CRM_STAGE_BY_CATEGORY.get(result["category"])
    if new_stage:
        record_stage_change(db, lead, new_stage, reason=f"Reply classified as {result['category']}")

    db.commit()
    db.refresh(message)
    return message


def is_followup_stopped(db: Session, lead: Lead) -> tuple[bool, str | None]:
    """Per the stop-rules spec: unsubscribe, negative response, invalid email, user stop, conversion."""
    if lead.email:
        suppressed = db.scalar(select(SuppressedEmail).where(SuppressedEmail.email == lead.email))
        if suppressed:
            return True, f"Suppressed: {suppressed.reason}"

    if lead.status in ("won", "lost"):
        return True, f"Lead is already {lead.status}"

    last_stop_reply = db.scalar(
        select(Message)
        .where(
            Message.lead_id == lead.id,
            Message.direction == "inbound",
            Message.category.in_(STOP_CATEGORIES),
        )
        .order_by(Message.created_at.desc())
        .limit(1)
    )
    if last_stop_reply:
        return True, f"Reply classified as {last_stop_reply.category}"

    return False, None
