from sqlalchemy.orm import Session

from app.models import CRMStageHistory, Lead

# The documented pipeline order (10_CRM_AND_TIMELINE_FINAL.md). Not enforced strictly —
# a lead can jump stages (e.g. a great reply skips straight to "meeting") — this is
# just the reference sequence used for display ordering.
PIPELINE_STAGES = [
    "new",
    "qualified",
    "not_qualified",
    "needs_review",
    "analyzed",
    "contacted",
    "interested",
    "follow_up",
    "meeting",
    "proposal",
    "won",
    "lost",
]


def record_stage_change(db: Session, lead: Lead, new_stage: str, reason: str | None = None) -> None:
    """Every important stage change should be logged — routes ALL lead.status writes through here."""
    old_stage = lead.status
    if old_stage == new_stage:
        return
    lead.status = new_stage
    db.add(
        CRMStageHistory(
            lead_id=lead.id,
            old_stage=old_stage,
            new_stage=new_stage,
            reason=reason,
        )
    )
