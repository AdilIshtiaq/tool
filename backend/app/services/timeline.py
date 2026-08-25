from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Call,
    CRMStageHistory,
    Lead,
    LeadAnalysis,
    LeadQualification,
    Message,
    ServiceRecommendation,
    Task,
)


def build_timeline(db: Session, lead: Lead) -> list[dict]:
    events: list[dict] = [
        {
            "type": "lead_discovered",
            "timestamp": lead.first_seen,
            "summary": f"Lead discovered via {lead.source}",
            "detail": {"source": lead.source, "source_id": lead.source_id},
        }
    ]

    for q in db.scalars(select(LeadQualification).where(LeadQualification.lead_id == lead.id)):
        summary = f"Qualification: {q.result} (score {q.score})"
        if q.is_override:
            summary = f"Qualification manually overridden to {q.result}"
        events.append(
            {
                "type": "qualification",
                "timestamp": q.run_at,
                "summary": summary,
                "detail": {"result": q.result, "score": float(q.score), "is_override": q.is_override},
            }
        )

    for a in db.scalars(select(LeadAnalysis).where(LeadAnalysis.lead_id == lead.id)):
        events.append(
            {
                "type": "ai_analysis",
                "timestamp": a.created_at,
                "summary": f"AI analysis: score {a.score}, confidence {round(float(a.confidence) * 100)}%",
                "detail": {"score": float(a.score), "confidence": float(a.confidence)},
            }
        )

    for r in db.scalars(select(ServiceRecommendation).where(ServiceRecommendation.lead_id == lead.id)):
        events.append(
            {
                "type": "recommendation",
                "timestamp": r.created_at,
                "summary": f"Recommended: {r.recommended_service.name}"
                + (f" ({r.human_decision})" if r.human_decision else ""),
                "detail": {"service": r.recommended_service.name, "human_decision": r.human_decision},
            }
        )

    for m in db.scalars(select(Message).where(Message.lead_id == lead.id)):
        if m.direction == "outbound":
            summary = f"Email sent: {m.subject} ({m.status})"
        else:
            summary = f"Reply received: {m.subject}" + (f" — {m.category}" if m.category else "")
        events.append(
            {
                "type": "email" if m.direction == "outbound" else "reply",
                "timestamp": m.created_at,
                "summary": summary,
                "detail": {"status": m.status, "category": m.category},
            }
        )

    for c in db.scalars(select(Call).where(Call.lead_id == lead.id)):
        summary = "Call logged" + (f": {c.outcome}" if c.outcome else " (outcome pending)")
        events.append(
            {
                "type": "call",
                "timestamp": c.created_at,
                "summary": summary,
                "detail": {"outcome": c.outcome},
            }
        )

    for t in db.scalars(select(Task).where(Task.lead_id == lead.id)):
        events.append(
            {
                "type": "task",
                "timestamp": t.created_at,
                "summary": f"Task: {t.title} ({t.status})",
                "detail": {"status": t.status, "priority": t.priority},
            }
        )

    for s in db.scalars(select(CRMStageHistory).where(CRMStageHistory.lead_id == lead.id)):
        events.append(
            {
                "type": "stage_change",
                "timestamp": s.changed_at,
                "summary": f"Stage changed: {s.old_stage or '(none)'} → {s.new_stage}",
                "detail": {"old_stage": s.old_stage, "new_stage": s.new_stage, "reason": s.reason},
            }
        )

    events.sort(key=lambda e: e["timestamp"], reverse=True)
    return events
