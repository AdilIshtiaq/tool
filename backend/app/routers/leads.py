import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AuditLog, Lead, LeadAnalysis, LeadQualification, Message, ServiceRecommendation
from app.schemas import (
    EnrichEmailsResponse,
    InboundMessageCreate,
    LeadAnalysisOut,
    LeadListResponse,
    LeadOut,
    LeadQualificationOut,
    LeadSearchRequest,
    LeadSearchResponse,
    LeadUpdate,
    MessageOut,
    ProcessNewLeadsResponse,
    QualificationOverrideRequest,
    RecommendationDecisionRequest,
    ServiceRecommendationOut,
    StageChangeRequest,
    TimelineEvent,
)
from app.services.ai_analysis import AIAnalysisError
from app.services.analysis_execution import run_analysis
from app.services.crm import record_stage_change
from app.services.lead_enrichment import enrich_leads_missing_email
from app.services.lead_pipeline import process_new_leads
from app.services.qualification import run_qualification
from app.services.reply_execution import record_inbound_message
from app.services.search_execution import execute_lead_search
from app.services.timeline import build_timeline

router = APIRouter(prefix="/api/leads", tags=["leads"])


def _analysis_to_out(analysis: LeadAnalysis) -> LeadAnalysisOut:
    # Built field-by-field rather than LeadAnalysisOut.model_validate(analysis):
    # the ORM's ServiceRecommendation has no flat recommended_service_name
    # attribute (only a relationship), so from_attributes validation of the
    # nested recommendation fails before the manual rebuild below ever runs.
    out = LeadAnalysisOut(
        id=analysis.id,
        lead_id=analysis.lead_id,
        summary=analysis.summary,
        opportunities=analysis.opportunities,
        score=analysis.score,
        confidence=analysis.confidence,
        evidence=analysis.evidence,
        missing_information=analysis.missing_information,
        next_action=analysis.next_action,
        needs_review=analysis.needs_review,
        created_at=analysis.created_at,
    )
    if analysis.recommendation:
        rec = analysis.recommendation
        out.recommendation = ServiceRecommendationOut(
            id=rec.id,
            lead_id=rec.lead_id,
            analysis_id=rec.analysis_id,
            recommended_service_id=rec.recommended_service_id,
            recommended_service_name=rec.recommended_service.name,
            secondary_service_ids=rec.secondary_service_ids,
            reasoning=rec.reasoning,
            human_decision=rec.human_decision,
            decision_reason=rec.decision_reason,
            decided_at=rec.decided_at,
            created_at=rec.created_at,
        )
    return out


@router.post("/search", response_model=LeadSearchResponse)
def search_leads(payload: LeadSearchRequest, db: Session = Depends(get_db)):
    run, leads = execute_lead_search(db, payload.model_dump(), mode="manual")
    return LeadSearchResponse(run=run, leads=leads)


@router.post("/enrich-emails", response_model=EnrichEmailsResponse)
def enrich_emails(limit: int = 50, db: Session = Depends(get_db)):
    """Best-effort email discovery from each lead's own website - Google
    Places never provides emails. Safe to call repeatedly/on a schedule;
    only ever looks at leads still missing an email."""
    result = enrich_leads_missing_email(db, limit=limit)
    return EnrichEmailsResponse(**result)


@router.post("/process-new", response_model=ProcessNewLeadsResponse)
def process_new_leads_endpoint(limit: int = 50, db: Session = Depends(get_db)):
    """Runs qualification then AI analysis automatically for every lead that
    hasn't gone through the pipeline yet. Safe to call repeatedly - only acts
    on leads still missing a qualification or analysis. Does not send
    anything and does not touch approval; that stays a human decision."""
    result = process_new_leads(db, limit=limit)
    return ProcessNewLeadsResponse(**result)


@router.get("", response_model=LeadListResponse)
def list_leads(
    page: int = 1,
    page_size: int = 25,
    search: str | None = None,
    status_filter: str | None = None,
    source: str | None = None,
    db: Session = Depends(get_db),
):
    query = select(Lead)
    count_query = select(func.count()).select_from(Lead)

    if search:
        like = f"%{search}%"
        query = query.where(Lead.business_name.ilike(like))
        count_query = count_query.where(Lead.business_name.ilike(like))
    if status_filter:
        query = query.where(Lead.status == status_filter)
        count_query = count_query.where(Lead.status == status_filter)
    if source:
        query = query.where(Lead.source == source)
        count_query = count_query.where(Lead.source == source)

    total = db.scalar(count_query) or 0

    query = (
        query.order_by(Lead.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = db.scalars(query).all()

    return LeadListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: uuid.UUID, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.patch("/{lead_id}", response_model=LeadOut)
def update_lead(lead_id: uuid.UUID, payload: LeadUpdate, db: Session = Depends(get_db)):
    """Manual correction of contact fields the source didn't provide (e.g. email). Never
    touches source-derived facts like business_name/address per the raw-data-is-truth rule."""
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    updates = payload.model_dump(exclude_unset=True)
    new_status = updates.pop("status", None)
    for key, value in updates.items():
        setattr(lead, key, value)
    if updates:
        db.add(
            AuditLog(
                action="lead_manual_correction",
                entity_type="lead",
                entity_id=str(lead_id),
                detail={"fields": list(updates.keys())},
            )
        )
    if new_status is not None:
        record_stage_change(db, lead, new_status, reason="Manual correction")
    db.commit()
    db.refresh(lead)
    return lead


@router.post("/{lead_id}/qualify", response_model=LeadQualificationOut)
def qualify_lead(lead_id: uuid.UUID, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return run_qualification(db, lead)


@router.get("/{lead_id}/qualification", response_model=list[LeadQualificationOut])
def get_lead_qualification(lead_id: uuid.UUID, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return db.scalars(
        select(LeadQualification)
        .where(LeadQualification.lead_id == lead_id)
        .order_by(LeadQualification.run_at.desc())
    ).all()


@router.patch("/{lead_id}/qualification", response_model=LeadQualificationOut)
def override_qualification(
    lead_id: uuid.UUID, payload: QualificationOverrideRequest, db: Session = Depends(get_db)
):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    latest = db.scalar(
        select(LeadQualification)
        .where(LeadQualification.lead_id == lead_id)
        .order_by(LeadQualification.run_at.desc())
        .limit(1)
    )

    override = LeadQualification(
        lead_id=lead_id,
        result=payload.result,
        score=latest.score if latest else 0.0,
        passed_rules=latest.passed_rules if latest else [],
        failed_rules=latest.failed_rules if latest else [],
        run_at=datetime.utcnow(),
        is_override=True,
        previous_result=latest.result if latest else None,
        override_reason=payload.reason,
        overridden_by=payload.overridden_by,
    )
    db.add(override)
    db.add(
        AuditLog(
            action="qualification_override",
            entity_type="lead",
            entity_id=str(lead_id),
            detail={
                "previous_result": latest.result if latest else None,
                "new_result": payload.result,
                "reason": payload.reason,
                "overridden_by": payload.overridden_by,
            },
        )
    )
    record_stage_change(
        db, lead, payload.result, reason=f"Manual qualification override: {payload.reason}"
    )
    db.commit()
    db.refresh(override)
    return override


@router.post("/{lead_id}/analyze", response_model=LeadAnalysisOut)
def analyze_lead_endpoint(lead_id: uuid.UUID, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    try:
        analysis, _recommendation = run_analysis(db, lead)
    except AIAnalysisError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return _analysis_to_out(analysis)


@router.get("/{lead_id}/analysis", response_model=list[LeadAnalysisOut])
def get_lead_analysis(lead_id: uuid.UUID, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    analyses = db.scalars(
        select(LeadAnalysis)
        .where(LeadAnalysis.lead_id == lead_id)
        .order_by(LeadAnalysis.created_at.desc())
    ).all()
    return [_analysis_to_out(a) for a in analyses]


@router.post(
    "/{lead_id}/recommendation/{recommendation_id}/decision",
    response_model=ServiceRecommendationOut,
)
def decide_recommendation(
    lead_id: uuid.UUID,
    recommendation_id: uuid.UUID,
    payload: RecommendationDecisionRequest,
    db: Session = Depends(get_db),
):
    recommendation = db.get(ServiceRecommendation, recommendation_id)
    if not recommendation or recommendation.lead_id != lead_id:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    recommendation.human_decision = payload.decision
    recommendation.decision_reason = payload.reason
    recommendation.decided_at = datetime.utcnow()

    db.add(
        AuditLog(
            action="recommendation_decision",
            entity_type="service_recommendation",
            entity_id=str(recommendation.id),
            detail={"decision": payload.decision, "reason": payload.reason},
        )
    )

    db.commit()
    db.refresh(recommendation)

    return ServiceRecommendationOut(
        id=recommendation.id,
        lead_id=recommendation.lead_id,
        analysis_id=recommendation.analysis_id,
        recommended_service_id=recommendation.recommended_service_id,
        recommended_service_name=recommendation.recommended_service.name,
        secondary_service_ids=recommendation.secondary_service_ids,
        reasoning=recommendation.reasoning,
        human_decision=recommendation.human_decision,
        decision_reason=recommendation.decision_reason,
        decided_at=recommendation.decided_at,
        created_at=recommendation.created_at,
    )


@router.get("/{lead_id}/messages", response_model=list[MessageOut])
def get_lead_messages(lead_id: uuid.UUID, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return db.scalars(
        select(Message).where(Message.lead_id == lead_id).order_by(Message.created_at.desc())
    ).all()


@router.post("/{lead_id}/replies", response_model=MessageOut)
def record_reply(lead_id: uuid.UUID, payload: InboundMessageCreate, db: Session = Depends(get_db)):
    """Records an inbound reply. In production this is called by the n8n IMAP workflow
    (Workflow G); exposed here too so a reply can be logged manually until IMAP is configured."""
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return record_inbound_message(db, lead, payload.from_email, payload.subject, payload.body)


@router.get("/{lead_id}/timeline", response_model=list[TimelineEvent])
def get_lead_timeline(lead_id: uuid.UUID, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return build_timeline(db, lead)


@router.patch("/{lead_id}/stage", response_model=LeadOut)
def change_lead_stage(lead_id: uuid.UUID, payload: StageChangeRequest, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    record_stage_change(db, lead, payload.new_stage, reason=payload.reason or "Manual stage change")
    db.commit()
    db.refresh(lead)
    return lead
