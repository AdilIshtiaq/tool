from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Lead, LeadAnalysis, LeadQualification
from app.services.ai_analysis import AIAnalysisError
from app.services.analysis_execution import run_analysis
from app.services.qualification import run_qualification


def _latest_by_lead(rows, timestamp_field: str) -> dict:
    latest: dict = {}
    for row in sorted(rows, key=lambda r: getattr(r, timestamp_field), reverse=True):
        latest.setdefault(row.lead_id, row)
    return latest


def process_new_leads(db: Session, limit: int = 50) -> dict:
    """Runs the discovery -> qualification -> analysis pipeline automatically
    for every lead that hasn't gone through it yet. Stops there - sending
    still requires a human to approve the recommendation (via a Campaign),
    per the outreach safety rules."""
    all_leads = db.scalars(select(Lead).order_by(Lead.created_at.asc())).all()

    latest_qualification = _latest_by_lead(
        db.scalars(select(LeadQualification)).all(), "run_at"
    )
    latest_analysis = _latest_by_lead(db.scalars(select(LeadAnalysis)).all(), "created_at")

    never_qualified = [l for l in all_leads if l.id not in latest_qualification][:limit]

    qualified_count = 0
    not_qualified_count = 0
    needs_review_count = 0
    for lead in never_qualified:
        qualification = run_qualification(db, lead)
        latest_qualification[lead.id] = qualification
        if qualification.result == "qualified":
            qualified_count += 1
        elif qualification.result == "not_qualified":
            not_qualified_count += 1
        else:
            needs_review_count += 1

    ready_for_analysis = [
        lead
        for lead in all_leads
        if lead.id in latest_qualification
        and latest_qualification[lead.id].result == "qualified"
        and lead.id not in latest_analysis
    ][:limit]

    analyzed_count = 0
    analysis_errors: list[str] = []
    for lead in ready_for_analysis:
        try:
            run_analysis(db, lead)
            analyzed_count += 1
        except AIAnalysisError as exc:
            analysis_errors.append(f"{lead.business_name}: {exc}")

    return {
        "qualified": qualified_count,
        "not_qualified": not_qualified_count,
        "needs_review": needs_review_count,
        "analyzed": analyzed_count,
        "analysis_errors": analysis_errors,
    }
