import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AnalysisRule
from app.schemas import AnalysisRuleCreate, AnalysisRuleOut, AnalysisRuleUpdate

router = APIRouter(prefix="/api/analysis-rules", tags=["analysis-rules"])


@router.get("", response_model=list[AnalysisRuleOut])
def list_analysis_rules(db: Session = Depends(get_db)):
    return db.scalars(select(AnalysisRule).order_by(AnalysisRule.created_at.asc())).all()


@router.post("", response_model=AnalysisRuleOut)
def create_analysis_rule(payload: AnalysisRuleCreate, db: Session = Depends(get_db)):
    rule = AnalysisRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.patch("/{rule_id}", response_model=AnalysisRuleOut)
def update_analysis_rule(
    rule_id: uuid.UUID, payload: AnalysisRuleUpdate, db: Session = Depends(get_db)
):
    rule = db.get(AnalysisRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=204)
def delete_analysis_rule(rule_id: uuid.UUID, db: Session = Depends(get_db)):
    rule = db.get(AnalysisRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
