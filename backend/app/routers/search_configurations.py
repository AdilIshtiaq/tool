import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import LeadSearchRun, SearchConfiguration
from app.schemas import (
    EnableAutomationRequest,
    RunDueResponse,
    RunDueResult,
    SearchConfigurationCreate,
    SearchConfigurationOut,
    SearchConfigurationRunResponse,
    SearchConfigurationUpdate,
)
from app.services.schedule import SCHEDULE_INTERVALS, is_due, is_valid_schedule
from app.services.search_execution import execute_lead_search

logger = logging.getLogger("nexcraft.automation")
router = APIRouter(prefix="/api/search-configurations", tags=["search-configurations"])


def _to_out(db: Session, config: SearchConfiguration) -> SearchConfigurationOut:
    last_run = db.scalar(
        select(LeadSearchRun)
        .where(LeadSearchRun.search_configuration_id == config.id)
        .order_by(LeadSearchRun.created_at.desc())
        .limit(1)
    )
    out = SearchConfigurationOut.model_validate(config)
    out.last_run = last_run
    return out


@router.post("", response_model=SearchConfigurationOut)
def create_search_configuration(
    payload: SearchConfigurationCreate, db: Session = Depends(get_db)
):
    config = SearchConfiguration(**payload.model_dump())
    db.add(config)
    db.commit()
    db.refresh(config)
    return _to_out(db, config)


@router.get("", response_model=list[SearchConfigurationOut])
def list_search_configurations(db: Session = Depends(get_db)):
    configs = db.scalars(
        select(SearchConfiguration).order_by(SearchConfiguration.created_at.desc())
    ).all()
    return [_to_out(db, config) for config in configs]


@router.patch("/{config_id}", response_model=SearchConfigurationOut)
def update_search_configuration(
    config_id: uuid.UUID,
    payload: SearchConfigurationUpdate,
    db: Session = Depends(get_db),
):
    config = db.get(SearchConfiguration, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Search configuration not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(config, field, value)

    db.commit()
    db.refresh(config)
    return _to_out(db, config)


@router.post("/{config_id}/run", response_model=SearchConfigurationRunResponse)
def run_search_configuration(config_id: uuid.UUID, db: Session = Depends(get_db)):
    config = db.get(SearchConfiguration, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Search configuration not found")

    run, leads = execute_lead_search(
        db, config.to_search_params(), mode="semi_auto", search_configuration_id=config.id
    )
    return SearchConfigurationRunResponse(
        search_configuration=_to_out(db, config), run=run, leads=leads
    )


@router.post("/{config_id}/enable", response_model=SearchConfigurationOut)
def enable_automation(
    config_id: uuid.UUID,
    payload: EnableAutomationRequest,
    db: Session = Depends(get_db),
):
    config = db.get(SearchConfiguration, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Search configuration not found")
    if not is_valid_schedule(payload.schedule):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid schedule. Supported: {', '.join(SCHEDULE_INTERVALS)}",
        )

    config.is_enabled = True
    config.schedule = payload.schedule
    db.commit()
    db.refresh(config)
    return _to_out(db, config)


@router.post("/{config_id}/disable", response_model=SearchConfigurationOut)
def disable_automation(config_id: uuid.UUID, db: Session = Depends(get_db)):
    config = db.get(SearchConfiguration, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Search configuration not found")

    config.is_enabled = False
    db.commit()
    db.refresh(config)
    return _to_out(db, config)


@router.post("/run-due", response_model=RunDueResponse)
def run_due_search_configurations(db: Session = Depends(get_db)):
    """Called by n8n's schedule trigger. Executes only configs whose own configured
    schedule says they are due — the trigger interval itself is just a heartbeat,
    never the actual interval respected (that stays configurable per saved search)."""
    now = datetime.now(timezone.utc)
    enabled_configs = db.scalars(
        select(SearchConfiguration).where(SearchConfiguration.is_enabled.is_(True))
    ).all()

    executed: list[RunDueResult] = []

    for config in enabled_configs:
        if not config.schedule or not is_valid_schedule(config.schedule):
            logger.warning(
                "Search configuration %s is enabled but has no valid schedule; skipping",
                config.id,
            )
            continue

        last_completed_run = db.scalar(
            select(LeadSearchRun)
            .where(
                LeadSearchRun.search_configuration_id == config.id,
                LeadSearchRun.status == "completed",
            )
            .order_by(LeadSearchRun.completed_at.desc())
            .limit(1)
        )
        last_completed_at = last_completed_run.completed_at if last_completed_run else None

        if not is_due(config.schedule, last_completed_at, now):
            continue

        run, _leads = execute_lead_search(
            db, config.to_search_params(), mode="auto", search_configuration_id=config.id
        )
        executed.append(
            RunDueResult(
                search_configuration_id=config.id,
                search_configuration_name=config.name,
                run=run,
            )
        )

    return RunDueResponse(checked=len(enabled_configs), executed=executed)
