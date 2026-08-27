from app.services.crm import record_stage_change


def test_dashboard_stats_reflects_lead_counts(client, make_lead):
    make_lead(status="new")
    make_lead(status="qualified")
    make_lead(status="won")

    response = client.get("/api/dashboard/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["total_leads"] >= 3
    assert body["new_leads"] >= 1
    assert body["qualified"] >= 1
    assert body["won"] >= 1


def test_recent_activity_reflects_stage_changes(client, make_lead, db_session):
    lead = make_lead(business_name="Activity Test Biz", status="new")
    record_stage_change(db_session, lead, "qualified", reason="Passed qualification rules")
    db_session.commit()

    response = client.get("/api/dashboard/recent-activity")
    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 1
    entry = next(e for e in body if e["lead_id"] == str(lead.id))
    assert entry["business_name"] == "Activity Test Biz"
    assert entry["new_stage"] == "qualified"
    assert entry["old_stage"] == "new"


def test_recent_activity_respects_limit(client, make_lead, db_session):
    lead = make_lead(status="new")
    for stage in ["qualified", "contacted", "meeting"]:
        record_stage_change(db_session, lead, stage, reason="test")
    db_session.commit()

    response = client.get("/api/dashboard/recent-activity", params={"limit": 2})
    assert response.status_code == 200
    assert len(response.json()) == 2
