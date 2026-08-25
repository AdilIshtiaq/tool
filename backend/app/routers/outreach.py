from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import Lead
from app.schemas import (
    AIEmailDraftRequest,
    AIEmailDraftResponse,
    MessageOut,
    OutreachPreviewRequest,
    OutreachPreviewResponse,
    OutreachSendRequest,
)
from app.services.ai_email import AIEmailError, generate_email_draft
from app.services.outreach_execution import (
    OutreachValidationError,
    build_preview,
    get_latest_recommendation,
    send_outreach,
)

router = APIRouter(prefix="/api/outreach", tags=["outreach"])


def _get_lead_or_404(db: Session, lead_id) -> Lead:
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.post("/draft", response_model=AIEmailDraftResponse)
def draft_email(payload: AIEmailDraftRequest, db: Session = Depends(get_db)):
    lead = _get_lead_or_404(db, payload.lead_id)
    recommendation = get_latest_recommendation(db, lead.id)
    if not recommendation:
        raise HTTPException(
            status_code=422,
            detail="This lead has no service recommendation yet. Run AI Analysis first.",
        )

    settings = get_settings()
    lead_info = {
        "business_name": lead.business_name,
        "category": lead.category,
        "city": lead.city,
        "country": lead.country,
        "website": lead.website,
    }

    try:
        draft = generate_email_draft(
            openai_api_key=settings.openai_api_key,
            anthropic_api_key=settings.anthropic_api_key,
            lead_info=lead_info,
            recommended_service=recommendation.recommended_service.name,
            reasoning=recommendation.reasoning,
        )
    except AIEmailError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return AIEmailDraftResponse(**draft)


@router.post("/preview", response_model=OutreachPreviewResponse)
def preview_outreach(payload: OutreachPreviewRequest, db: Session = Depends(get_db)):
    lead = _get_lead_or_404(db, payload.lead_id)
    return build_preview(db, lead, payload.subject, payload.body)


@router.post("/send", response_model=MessageOut)
def send_outreach_endpoint(payload: OutreachSendRequest, db: Session = Depends(get_db)):
    lead = _get_lead_or_404(db, payload.lead_id)
    try:
        return send_outreach(
            db,
            lead,
            subject=payload.subject,
            body=payload.body,
            template_id=payload.template_id,
            is_test=payload.is_test,
            test_email_override=payload.test_email_override,
        )
    except OutreachValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
