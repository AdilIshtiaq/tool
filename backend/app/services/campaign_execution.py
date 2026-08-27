from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Campaign, Lead, Message, ServiceRecommendation, Template
from app.services.ai_email import AIEmailError, generate_email_draft
from app.services.outreach_execution import (
    OutreachValidationError,
    get_latest_recommendation,
    send_outreach,
)
from app.services.schedule import is_due, is_valid_schedule


def get_approved_leads_for_campaign(db: Session) -> list[Lead]:
    """Leads whose most recent service recommendation was human-approved."""
    all_recs = db.scalars(
        select(ServiceRecommendation).order_by(
            ServiceRecommendation.lead_id, ServiceRecommendation.created_at.desc()
        )
    ).all()

    latest_by_lead: dict = {}
    for rec in all_recs:
        latest_by_lead.setdefault(rec.lead_id, rec)

    approved_lead_ids = [
        lead_id for lead_id, rec in latest_by_lead.items() if rec.human_decision == "approved"
    ]
    if not approved_lead_ids:
        return []
    return db.scalars(select(Lead).where(Lead.id.in_(approved_lead_ids))).all()


def _sent_today_count(db: Session, campaign_id) -> int:
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        db.scalar(
            select(func.count()).select_from(Message).where(
                Message.campaign_id == campaign_id,
                Message.status == "accepted_by_provider",
                Message.sent_at >= today_start,
            )
        )
        or 0
    )


def _lead_info(lead: Lead) -> dict:
    return {
        "business_name": lead.business_name,
        "category": lead.category,
        "city": lead.city,
        "country": lead.country,
        "website": lead.website,
    }


def run_campaign(db: Session, campaign: Campaign) -> dict:
    """Sends an AI-drafted email to every eligible approved lead, up to the
    daily limit. Each draft is generated from that lead's own analysis
    (recommended service + reasoning) - the campaign's template is used only
    as a style/format reference for the AI, not sent verbatim, so every
    email is actually personalized rather than one canned message with a
    name swapped in. Eligibility (valid email, not suppressed, not already
    sent) is enforced per-lead by send_outreach()'s existing validation."""
    template = db.get(Template, campaign.template_id) if campaign.template_id else None
    if not template:
        campaign.last_run_at = datetime.now(timezone.utc)
        db.commit()
        return {"sent": 0, "skipped": 0, "reasons": ["Campaign has no template configured."]}

    settings = get_settings()

    remaining = None
    if campaign.daily_limit is not None:
        remaining = max(campaign.daily_limit - _sent_today_count(db, campaign.id), 0)
        if remaining == 0:
            campaign.last_run_at = datetime.now(timezone.utc)
            db.commit()
            return {"sent": 0, "skipped": 0, "reasons": ["Daily limit already reached for today."]}

    sent = 0
    skipped_reasons: list[str] = []
    for lead in get_approved_leads_for_campaign(db):
        if remaining is not None and sent >= remaining:
            break

        recommendation = get_latest_recommendation(db, lead.id)
        if not recommendation:
            skipped_reasons.append(f"{lead.business_name}: no recommendation found")
            continue

        try:
            draft = generate_email_draft(
                openai_api_key=settings.openai_api_key,
                anthropic_api_key=settings.anthropic_api_key,
                gemini_api_key=settings.gemini_api_key,
                lead_info=_lead_info(lead),
                recommended_service=recommendation.recommended_service.name,
                reasoning=recommendation.reasoning,
                existing_template={"subject": template.subject, "body": template.body},
            )
        except AIEmailError as exc:
            skipped_reasons.append(f"{lead.business_name}: AI draft failed - {exc}")
            continue

        try:
            send_outreach(
                db,
                lead,
                subject=draft["subject"],
                body=draft["body"],
                template_id=template.id,
                campaign_id=campaign.id,
            )
            sent += 1
        except OutreachValidationError as exc:
            skipped_reasons.append(f"{lead.business_name}: {exc}")

    campaign.last_run_at = datetime.now(timezone.utc)
    db.commit()
    return {"sent": sent, "skipped": len(skipped_reasons), "reasons": skipped_reasons}


def run_due_campaigns(db: Session) -> tuple[int, list[tuple[Campaign, dict]]]:
    """Called by n8n's schedule trigger. Executes only campaigns whose own
    configured schedule says they are due — same pattern as
    run_due_search_configurations()."""
    now = datetime.now(timezone.utc)
    enabled = db.scalars(select(Campaign).where(Campaign.is_enabled.is_(True))).all()

    executed: list[tuple[Campaign, dict]] = []
    for campaign in enabled:
        if not campaign.schedule or not is_valid_schedule(campaign.schedule):
            continue
        if not is_due(campaign.schedule, campaign.last_run_at, now):
            continue
        result = run_campaign(db, campaign)
        executed.append((campaign, result))

    return len(enabled), executed
