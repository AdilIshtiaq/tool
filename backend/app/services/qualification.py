from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Lead, LeadQualification, QualificationRule
from app.services.crm import record_stage_change

# Fields a rule may check, and the operators valid for each.
FIELD_OPERATORS: dict[str, list[str]] = {
    "business_name": ["equals", "not_equals", "contains", "not_contains", "exists", "not_exists"],
    "category": ["equals", "not_equals", "contains", "not_contains", "in", "not_in", "exists", "not_exists"],
    "city": ["equals", "not_equals", "contains", "not_contains", "in", "not_in", "exists", "not_exists"],
    "country": ["equals", "not_equals", "contains", "not_contains", "in", "not_in", "exists", "not_exists"],
    "phone": ["exists", "not_exists"],
    "email": ["exists", "not_exists"],
    "website": ["exists", "not_exists"],
    "rating": ["equals", "greater_than", "less_than", "exists", "not_exists"],
    "review_count": ["equals", "greater_than", "less_than", "exists", "not_exists"],
}


def is_valid_field_operator(field: str, operator: str) -> bool:
    return field in FIELD_OPERATORS and operator in FIELD_OPERATORS[field]


def _get_field_value(lead: Lead, field: str):
    return getattr(lead, field, None)


def evaluate_rule(lead: Lead, rule: QualificationRule) -> bool:
    value = _get_field_value(lead, rule.field)
    expected = rule.expected_value

    if rule.operator == "exists":
        return value is not None and str(value).strip() != ""
    if rule.operator == "not_exists":
        return value is None or str(value).strip() == ""

    # Every other operator is meaningless against a missing value.
    if value is None or str(value).strip() == "":
        return False

    if rule.operator == "equals":
        return str(value).strip().lower() == str(expected).strip().lower()
    if rule.operator == "not_equals":
        return str(value).strip().lower() != str(expected).strip().lower()
    if rule.operator == "contains":
        return str(expected).strip().lower() in str(value).lower()
    if rule.operator == "not_contains":
        return str(expected).strip().lower() not in str(value).lower()
    if rule.operator == "in":
        options = [o.strip().lower() for o in str(expected).split(",")]
        return str(value).strip().lower() in options
    if rule.operator == "not_in":
        options = [o.strip().lower() for o in str(expected).split(",")]
        return str(value).strip().lower() not in options
    if rule.operator == "greater_than":
        try:
            return float(value) > float(expected)
        except (TypeError, ValueError):
            return False
    if rule.operator == "less_than":
        try:
            return float(value) < float(expected)
        except (TypeError, ValueError):
            return False

    raise ValueError(f"Unknown operator: {rule.operator}")


def run_qualification(db: Session, lead: Lead) -> LeadQualification:
    rules = db.scalars(
        select(QualificationRule)
        .where(QualificationRule.enabled.is_(True))
        .order_by(QualificationRule.priority.asc())
    ).all()

    passed: list[dict] = []
    failed: list[dict] = []

    for rule in rules:
        outcome = evaluate_rule(lead, rule)
        entry = {"id": str(rule.id), "name": rule.name}
        (passed if outcome else failed).append(entry)

    total = len(rules)
    score = round((len(passed) / total) * 100, 2) if total > 0 else 0.0

    if total == 0:
        result = "needs_review"
    elif len(failed) == 0:
        result = "qualified"
    elif len(passed) == 0:
        result = "not_qualified"
    else:
        result = "needs_review"

    qualification = LeadQualification(
        lead_id=lead.id,
        result=result,
        score=score,
        passed_rules=passed,
        failed_rules=failed,
        run_at=datetime.utcnow(),
    )
    db.add(qualification)

    record_stage_change(db, lead, result, reason="Qualification rules run")
    db.commit()
    db.refresh(qualification)
    return qualification
