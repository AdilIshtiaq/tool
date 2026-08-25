from sqlalchemy import select

from app.models import CRMStageHistory
from app.services.crm import record_stage_change


def test_stage_change_updates_lead_and_logs_history(db_session, make_lead):
    lead = make_lead(status="new")
    record_stage_change(db_session, lead, "qualified", reason="Test transition")
    db_session.commit()

    assert lead.status == "qualified"
    history = db_session.scalars(
        select(CRMStageHistory).where(CRMStageHistory.lead_id == lead.id)
    ).all()
    assert len(history) == 1
    assert history[0].old_stage == "new"
    assert history[0].new_stage == "qualified"
    assert history[0].reason == "Test transition"


def test_no_op_change_does_not_log(db_session, make_lead):
    lead = make_lead(status="qualified")
    record_stage_change(db_session, lead, "qualified", reason="Should be skipped")
    db_session.commit()

    history = db_session.scalars(
        select(CRMStageHistory).where(CRMStageHistory.lead_id == lead.id)
    ).all()
    assert len(history) == 0


def test_multiple_transitions_all_logged(db_session, make_lead):
    lead = make_lead(status="new")
    record_stage_change(db_session, lead, "qualified")
    record_stage_change(db_session, lead, "analyzed")
    record_stage_change(db_session, lead, "contacted")
    db_session.commit()

    history = db_session.scalars(
        select(CRMStageHistory)
        .where(CRMStageHistory.lead_id == lead.id)
        .order_by(CRMStageHistory.changed_at.asc())
    ).all()
    assert [h.new_stage for h in history] == ["qualified", "analyzed", "contacted"]
    assert [h.old_stage for h in history] == ["new", "qualified", "analyzed"]
