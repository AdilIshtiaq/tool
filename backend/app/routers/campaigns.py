import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Campaign
from app.schemas import (
    CampaignCreate,
    CampaignOut,
    CampaignRunDueResponse,
    CampaignRunResult,
    CampaignUpdate,
    EnableAutomationRequest,
)
from app.services.campaign_execution import run_campaign, run_due_campaigns
from app.services.schedule import SCHEDULE_INTERVALS, is_valid_schedule

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


def _get_campaign_or_404(db: Session, campaign_id: uuid.UUID) -> Campaign:
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


def _to_run_result(campaign: Campaign, result: dict) -> CampaignRunResult:
    return CampaignRunResult(
        campaign_id=campaign.id,
        campaign_name=campaign.name,
        sent_count=result["sent"],
        skipped_count=result["skipped"],
        skipped_reasons=result["reasons"],
    )


@router.post("", response_model=CampaignOut)
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db)):
    campaign = Campaign(**payload.model_dump())
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.get("", response_model=list[CampaignOut])
def list_campaigns(db: Session = Depends(get_db)):
    return db.scalars(select(Campaign).order_by(Campaign.created_at.desc())).all()


@router.patch("/{campaign_id}", response_model=CampaignOut)
def update_campaign(campaign_id: uuid.UUID, payload: CampaignUpdate, db: Session = Depends(get_db)):
    campaign = _get_campaign_or_404(db, campaign_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(campaign, field, value)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.post("/{campaign_id}/enable", response_model=CampaignOut)
def enable_campaign(
    campaign_id: uuid.UUID, payload: EnableAutomationRequest, db: Session = Depends(get_db)
):
    campaign = _get_campaign_or_404(db, campaign_id)
    if not campaign.template_id:
        raise HTTPException(
            status_code=422, detail="Set a template on this campaign before enabling automatic sending."
        )
    if not is_valid_schedule(payload.schedule):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid schedule. Supported: {', '.join(SCHEDULE_INTERVALS)}",
        )
    campaign.is_enabled = True
    campaign.schedule = payload.schedule
    db.commit()
    db.refresh(campaign)
    return campaign


@router.post("/{campaign_id}/disable", response_model=CampaignOut)
def disable_campaign(campaign_id: uuid.UUID, db: Session = Depends(get_db)):
    campaign = _get_campaign_or_404(db, campaign_id)
    campaign.is_enabled = False
    db.commit()
    db.refresh(campaign)
    return campaign


@router.post("/{campaign_id}/run", response_model=CampaignRunResult)
def run_campaign_now(campaign_id: uuid.UUID, db: Session = Depends(get_db)):
    campaign = _get_campaign_or_404(db, campaign_id)
    result = run_campaign(db, campaign)
    return _to_run_result(campaign, result)


@router.post("/run-due", response_model=CampaignRunDueResponse)
def run_due_campaigns_endpoint(db: Session = Depends(get_db)):
    """Called by n8n's schedule trigger — same pattern as
    /api/search-configurations/run-due. Add a Schedule Trigger workflow in n8n
    pointing here (e.g. every 15 minutes); each campaign's own configured
    schedule decides whether it actually sends anything on a given tick."""
    checked, executed = run_due_campaigns(db)
    return CampaignRunDueResponse(
        checked=checked,
        executed=[_to_run_result(campaign, result) for campaign, result in executed],
    )
