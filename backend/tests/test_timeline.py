import time

from app.models import LeadQualification, Task
from app.services.crm import record_stage_change
from app.services.timeline import build_timeline


def test_timeline_includes_lead_discovered_event(db_session, make_lead):
    lead = make_lead()
    events = build_timeline(db_session, lead)
    types = [e["type"] for e in events]
    assert "lead_discovered" in types


def test_timeline_includes_stage_changes_sorted_newest_first(db_session, make_lead):
    lead = make_lead(status="new")
    record_stage_change(db_session, lead, "qualified")
    db_session.commit()
    time.sleep(0.01)  # guarantee a distinct timestamp from the first transition
    record_stage_change(db_session, lead, "analyzed")
    db_session.commit()

    events = build_timeline(db_session, lead)
    stage_events = [e for e in events if e["type"] == "stage_change"]
    assert len(stage_events) == 2
    # newest first
    assert stage_events[0]["detail"]["new_stage"] == "analyzed"
    assert stage_events[1]["detail"]["new_stage"] == "qualified"


def test_timeline_includes_qualification_and_task_events(db_session, make_lead):
    lead = make_lead()
    db_session.add(
        LeadQualification(
            lead_id=lead.id,
            result="qualified",
            score=100.0,
            passed_rules=[],
            failed_rules=[],
        )
    )
    db_session.add(Task(lead_id=lead.id, title="Follow up", status="pending"))
    db_session.commit()

    events = build_timeline(db_session, lead)
    types = {e["type"] for e in events}
    assert "qualification" in types
    assert "task" in types


def test_timeline_is_sorted_descending_overall(db_session, make_lead):
    lead = make_lead()
    record_stage_change(db_session, lead, "qualified")
    db_session.commit()

    events = build_timeline(db_session, lead)
    timestamps = [e["timestamp"] for e in events]
    assert timestamps == sorted(timestamps, reverse=True)
