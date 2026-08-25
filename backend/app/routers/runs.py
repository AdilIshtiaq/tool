import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import LeadSearchRun
from app.schemas import LeadSearchResponse, LeadSearchRunOut
from app.services.search_execution import execute_lead_search

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.get("", response_model=list[LeadSearchRunOut])
def list_runs(limit: int = 50, db: Session = Depends(get_db)):
    runs = db.scalars(
        select(LeadSearchRun).order_by(LeadSearchRun.created_at.desc()).limit(limit)
    ).all()
    return runs


@router.get("/{run_id}", response_model=LeadSearchRunOut)
def get_run(run_id: uuid.UUID, db: Session = Depends(get_db)):
    run = db.get(LeadSearchRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.post("/{run_id}/retry", response_model=LeadSearchResponse)
def retry_run(run_id: uuid.UUID, db: Session = Depends(get_db)):
    original = db.get(LeadSearchRun, run_id)
    if not original:
        raise HTTPException(status_code=404, detail="Run not found")
    if original.status != "failed":
        raise HTTPException(status_code=400, detail="Only failed runs can be retried")

    run, leads = execute_lead_search(
        db,
        original.search_config,
        mode=original.mode,
        search_configuration_id=original.search_configuration_id,
    )
    return LeadSearchResponse(run=run, leads=leads)
