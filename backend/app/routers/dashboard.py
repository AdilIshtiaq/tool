from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Lead, Message, SearchConfiguration, Task
from app.schemas import DashboardStatsOut

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _count_by_status(db: Session, status: str) -> int:
    return db.scalar(select(func.count()).select_from(Lead).where(Lead.status == status)) or 0


@router.get("/stats", response_model=DashboardStatsOut)
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_leads = db.scalar(select(func.count()).select_from(Lead)) or 0

    replies = db.scalar(
        select(func.count()).select_from(Message).where(Message.direction == "inbound")
    ) or 0

    due_tasks = db.scalar(
        select(func.count())
        .select_from(Task)
        .where(Task.status != "done", Task.due_date.isnot(None), Task.due_date <= datetime.utcnow())
    ) or 0

    active_automation_runs = db.scalar(
        select(func.count()).select_from(SearchConfiguration).where(SearchConfiguration.is_enabled.is_(True))
    ) or 0

    return DashboardStatsOut(
        total_leads=total_leads,
        new_leads=_count_by_status(db, "new"),
        qualified=_count_by_status(db, "qualified"),
        needs_review=_count_by_status(db, "needs_review"),
        contacted=_count_by_status(db, "contacted"),
        replies=replies,
        meetings=_count_by_status(db, "meeting"),
        won=_count_by_status(db, "won"),
        lost=_count_by_status(db, "lost"),
        due_tasks=due_tasks,
        active_automation_runs=active_automation_runs,
    )
