from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Campaign, Lead, Message, ServiceRecommendation, Template
from app.services.outreach_execution import OutreachValidationError, send_outreach
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


def run_campaign(db: Session, campaign: Campaign) -> dict:
    """Sends the campaign's template to every eligible approved lead, up to the
    daily limit. Eligibility (valid email, not suppressed, not already sent)
    is enforced per-lead by send_outreach()'s existing validation."""
    template = db.get(Template, campaign.template_id) if campaign.template_id else None
    if not template:
        campaign.last_run_at = datetime.now(timezone.utc)
        db.commit()
        return {"sent": 0, "skipped": 0, "reasons": ["Campaign has no template configured."]}

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
        try:
            send_outreach(
                db,
                lead,
                subject=template.subject,
                body=template.body,
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
