import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Lead
from app.services.email_discovery import discover_email

logger = logging.getLogger("nexcraft.enrichment")


def enrich_leads_missing_email(db: Session, limit: int = 50) -> dict:
    """Best-effort: tries to find an email on each lead's own website.
    Leads without a website can't be enriched this way at all."""
    leads = db.scalars(
        select(Lead)
        .where(Lead.email.is_(None), Lead.website.isnot(None))
        .limit(limit)
    ).all()

    found = 0
    checked = 0
    for lead in leads:
        checked += 1
        try:
            email = discover_email(lead.website)
        except Exception:
            logger.exception("Email discovery failed for lead %s", lead.id)
            continue
        if email:
            lead.email = email
            found += 1

    db.commit()
    return {"checked": checked, "found": found}
