def test_create_call_requires_valid_lead(client):
    response = client.post(
        "/api/calls",
        json={"lead_id": "00000000-0000-0000-0000-000000000000", "reason_for_calling": "x"},
    )
    assert response.status_code == 404


def test_create_call_with_no_outcome_does_not_change_stage(client, make_lead):
    lead = make_lead(status="qualified")
    response = client.post("/api/calls", json={"lead_id": str(lead.id)})
    assert response.status_code == 200
    assert response.json()["outcome"] is None


def test_create_call_with_meeting_booked_updates_lead_stage(client, make_lead, db_session):
    lead = make_lead(status="qualified")
    response = client.post(
        "/api/calls",
        json={"lead_id": str(lead.id), "outcome": "meeting_booked"},
    )
    assert response.status_code == 200
    db_session.refresh(lead)
    assert lead.status == "meeting"


def test_update_call_outcome_later_also_updates_stage(client, make_lead, db_session):
    """Regression test — PATCH used to skip the stage-change side effect that POST applied."""
    lead = make_lead(status="qualified")
    call_id = client.post("/api/calls", json={"lead_id": str(lead.id)}).json()["id"]

    response = client.patch(f"/api/calls/{call_id}", json={"outcome": "not_interested"})
    assert response.status_code == 200

    db_session.refresh(lead)
    assert lead.status == "lost"


def test_invalid_outcome_rejected(client, make_lead):
    lead = make_lead()
    response = client.post(
        "/api/calls", json={"lead_id": str(lead.id), "outcome": "not_a_real_outcome"}
    )
    assert response.status_code == 422


def test_call_workspace_includes_lead_and_calls(client, make_lead):
    lead = make_lead(business_name="Workspace Test Biz")
    client.post("/api/calls", json={"lead_id": str(lead.id), "notes": "first call"})

    response = client.get(f"/api/leads/{lead.id}/call-workspace")
    assert response.status_code == 200
    body = response.json()
    assert body["lead"]["business_name"] == "Workspace Test Biz"
    assert len(body["calls"]) == 1
    assert body["latest_analysis"] is None
