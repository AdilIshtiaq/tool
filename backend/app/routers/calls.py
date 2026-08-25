import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import AuditLog, Call, Lead, LeadAnalysis
from app.schemas import (
    CallCreate,
    CallOut,
    CallScriptOut,
    CallUpdate,
    CallWorkspaceOut,
)
from app.services.ai_call_script import AICallScriptError, format_script_text, generate_call_script
from app.services.crm import record_stage_change

router = APIRouter(tags=["calls"])


def _latest_analysis(db: Session, lead_id) -> LeadAnalysis | None:
    return db.scalar(
        select(LeadAnalysis)
        .where(LeadAnalysis.lead_id == lead_id)
        .order_by(LeadAnalysis.created_at.desc())
        .limit(1)
    )


OUTCOME_TO_LEAD_STATUS = {
    "meeting_booked": "meeting",
    "interested": "interested",
    "follow_up": "follow_up",
    "not_interested": "lost",
}


def _apply_outcome_to_lead(db: Session, lead: Lead, outcome: str | None) -> None:
    if outcome and outcome in OUTCOME_TO_LEAD_STATUS:
        record_stage_change(db, lead, OUTCOME_TO_LEAD_STATUS[outcome], reason=f"Call outcome: {outcome}")


@router.get("/api/leads/{lead_id}/call-workspace", response_model=CallWorkspaceOut)
def get_call_workspace(lead_id: uuid.UUID, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    analysis = _latest_analysis(db, lead_id)
    calls = db.scalars(
        select(Call).where(Call.lead_id == lead_id).order_by(Call.created_at.desc())
    ).all()

    analysis_out = None
    if analysis:
        from app.routers.leads import _analysis_to_out

        analysis_out = _analysis_to_out(analysis)

    return CallWorkspaceOut(lead=lead, latest_analysis=analysis_out, calls=calls)


@router.post("/api/leads/{lead_id}/call-script", response_model=CallScriptOut)
def generate_script_for_lead(lead_id: uuid.UUID, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    settings = get_settings()
    analysis = _latest_analysis(db, lead_id)

    lead_info = {
        "business_name": lead.business_name,
        "category": lead.category,
        "city": lead.city,
        "country": lead.country,
        "website": lead.website,
        "rating": float(lead.rating) if lead.rating is not None else None,
    }

    recommendation = analysis.recommendation if analysis else None

    try:
        script = generate_call_script(
            openai_api_key=settings.openai_api_key,
            anthropic_api_key=settings.anthropic_api_key,
            lead_info=lead_info,
            analysis_summary=analysis.summary if analysis else None,
            recommended_service=(
                recommendation.recommended_service.name if recommendation else None
            ),
            reasoning=recommendation.reasoning if recommendation else None,
        )
    except AICallScriptError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return CallScriptOut(**script, full_text=format_script_text(script))


@router.post("/api/calls", response_model=CallOut)
def create_call(payload: CallCreate, db: Session = Depends(get_db)):
    lead = db.get(Lead, payload.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    call = Call(**payload.model_dump())
    db.add(call)
    db.flush()

    db.add(
        AuditLog(
            action="call_logged",
            entity_type="lead",
            entity_id=str(payload.lead_id),
            detail={"call_id": str(call.id), "outcome": call.outcome},
        )
    )

    _apply_outcome_to_lead(db, lead, payload.outcome)

    db.commit()
    db.refresh(call)
    return call


@router.patch("/api/calls/{call_id}", response_model=CallOut)
def update_call(call_id: uuid.UUID, payload: CallUpdate, db: Session = Depends(get_db)):
    call = db.get(Call, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(call, key, value)

    if "outcome" in updates:
        _apply_outcome_to_lead(db, call.lead, updates["outcome"])

    db.commit()
    db.refresh(call)
    return call
