from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AnalysisRule, AuditLog, Lead, LeadAnalysis, Service, ServiceRecommendation
from app.services.ai_analysis import AIAnalysisError, analyze_lead
from app.services.crm import record_stage_change

# Below this confidence, the result is routed to Needs Review per the blueprint's review policy.
CONFIDENCE_REVIEW_THRESHOLD = 0.6
# High-impact (large opportunity) recommendations also require manual approval before acting on them.
HIGH_IMPACT_SCORE_THRESHOLD = 80.0

ALLOWED_LEAD_FIELDS = [
    "business_name",
    "category",
    "address",
    "city",
    "country",
    "website",
    "rating",
    "review_count",
]


def _lead_info(lead: Lead) -> dict:
    info = {}
    for field in ALLOWED_LEAD_FIELDS:
        value = getattr(lead, field)
        info[field] = float(value) if field == "rating" and value is not None else value
    return info


def run_analysis(db: Session, lead: Lead) -> tuple[LeadAnalysis, ServiceRecommendation]:
    settings = get_settings()

    rules = db.scalars(
        select(AnalysisRule).where(AnalysisRule.enabled.is_(True))
    ).all()
    services = db.scalars(select(Service).where(Service.enabled.is_(True))).all()
    catalog = [{"id": str(s.id), "name": s.name, "description": s.description} for s in services]

    result = analyze_lead(
        openai_api_key=settings.openai_api_key,
        anthropic_api_key=settings.anthropic_api_key,
        gemini_api_key=settings.gemini_api_key,
        lead_info=_lead_info(lead),
        analysis_rules=[r.description for r in rules],
        service_catalog=catalog,
    )

    needs_review = (
        result["confidence"] < CONFIDENCE_REVIEW_THRESHOLD
        or result["score"] >= HIGH_IMPACT_SCORE_THRESHOLD
    )

    analysis = LeadAnalysis(
        lead_id=lead.id,
        summary=result["summary"],
        opportunities=result["opportunities"],
        score=result["score"],
        confidence=result["confidence"],
        evidence=result["evidence"],
        missing_information=result["missing_information"],
        next_action=result["next_action"],
        needs_review=needs_review,
    )
    db.add(analysis)
    db.flush()

    name_to_service = {s.name: s for s in services}
    recommended = name_to_service[result["recommended_service"]]
    secondary_ids = [
        str(name_to_service[name].id)
        for name in result["secondary_services"]
        if name in name_to_service and name != recommended.name
    ]

    recommendation = ServiceRecommendation(
        lead_id=lead.id,
        analysis_id=analysis.id,
        recommended_service_id=recommended.id,
        secondary_service_ids=secondary_ids,
        reasoning=result["reasoning"],
    )
    db.add(recommendation)

    db.add(
        AuditLog(
            action="ai_analysis_decision",
            entity_type="lead",
            entity_id=str(lead.id),
            detail={
                "score": result["score"],
                "confidence": result["confidence"],
                "recommended_service": result["recommended_service"],
                "needs_review": needs_review,
            },
        )
    )

    record_stage_change(db, lead, "analyzed", reason="AI analysis completed")
    db.commit()
    db.refresh(analysis)
    db.refresh(recommendation)
    return analysis, recommendation
