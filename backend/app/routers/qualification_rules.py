import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import QualificationRule
from app.schemas import (
    QualificationRuleCreate,
    QualificationRuleOut,
    QualificationRuleUpdate,
)
from app.services.qualification import FIELD_OPERATORS, is_valid_field_operator

router = APIRouter(prefix="/api/qualification-rules", tags=["qualification-rules"])


@router.get("/fields")
def list_available_fields():
    """Fields and operators the rule builder UI can offer."""
    return FIELD_OPERATORS


@router.post("", response_model=QualificationRuleOut)
def create_rule(payload: QualificationRuleCreate, db: Session = Depends(get_db)):
    if not is_valid_field_operator(payload.field, payload.operator):
        raise HTTPException(
            status_code=422,
            detail=f"Operator '{payload.operator}' is not valid for field '{payload.field}'",
        )
    rule = QualificationRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("", response_model=list[QualificationRuleOut])
def list_rules(db: Session = Depends(get_db)):
    return db.scalars(
        select(QualificationRule).order_by(QualificationRule.priority.asc())
    ).all()


@router.patch("/{rule_id}", response_model=QualificationRuleOut)
def update_rule(
    rule_id: uuid.UUID, payload: QualificationRuleUpdate, db: Session = Depends(get_db)
):
    rule = db.get(QualificationRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    updates = payload.model_dump(exclude_unset=True)
    field = updates.get("field", rule.field)
    operator = updates.get("operator", rule.operator)
    if "field" in updates or "operator" in updates:
        if not is_valid_field_operator(field, operator):
            raise HTTPException(
                status_code=422,
                detail=f"Operator '{operator}' is not valid for field '{field}'",
            )

    for key, value in updates.items():
        setattr(rule, key, value)

    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=204)
def delete_rule(rule_id: uuid.UUID, db: Session = Depends(get_db)):
    rule = db.get(QualificationRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
