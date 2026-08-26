from datetime import datetime, timedelta, timezone

from app.models import LeadAnalysis, Service, ServiceRecommendation, Template


def _make_approved_lead(db_session, make_lead, email="owner@example.com", business_name="Approved Biz"):
    lead = make_lead(business_name=business_name, email=email)
    service = Service(name=f"Service for {business_name}", enabled=True)
    db_session.add(service)
    db_session.flush()

    analysis = LeadAnalysis(
        lead_id=lead.id,
        summary="x",
        opportunities=[],
        score=50,
        confidence=0.8,
        evidence=[],
        missing_information=[],
        next_action="x",
    )
    db_session.add(analysis)
    db_session.flush()

    recommendation = ServiceRecommendation(
        lead_id=lead.id,
        analysis_id=analysis.id,
        recommended_service_id=service.id,
        reasoning="x",
        human_decision="approved",
        decided_at=datetime.now(timezone.utc),
    )
    db_session.add(recommendation)
    db_session.commit()
    return lead


def _make_template(db_session):
    template = Template(name="Intro", subject="Hi {{business_name}}", body="Body for {{business_name}}")
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template


def test_create_campaign_requires_template(client):
    response = client.post("/api/campaigns", json={"name": "No template"})
    assert response.status_code == 422


def test_run_campaign_sends_to_approved_leads(client, make_lead, db_session):
    lead = _make_approved_lead(db_session, make_lead)
    template = _make_template(db_session)

    campaign = client.post(
        "/api/campaigns", json={"name": "Test Campaign", "template_id": str(template.id)}
    ).json()

    response = client.post(f"/api/campaigns/{campaign['id']}/run")
    assert response.status_code == 200
    body = response.json()
    assert body["sent_count"] == 1
    assert body["skipped_count"] == 0

    messages = client.get("/api/messages", params={"direction": "outbound"}).json()
    assert any(m["lead_id"] == str(lead.id) for m in messages)


def test_run_campaign_skips_leads_without_approval(client, make_lead, db_session):
    make_lead(business_name="Not approved", email="notapproved@example.com")
    template = _make_template(db_session)

    campaign = client.post(
        "/api/campaigns", json={"name": "Test Campaign", "template_id": str(template.id)}
    ).json()

    response = client.post(f"/api/campaigns/{campaign['id']}/run")
    assert response.status_code == 200
    assert response.json()["sent_count"] == 0


def test_run_campaign_respects_daily_limit(client, make_lead, db_session):
    _make_approved_lead(db_session, make_lead, email="one@example.com", business_name="Biz One")
    _make_approved_lead(db_session, make_lead, email="two@example.com", business_name="Biz Two")
    template = _make_template(db_session)

    campaign = client.post(
        "/api/campaigns",
        json={"name": "Limited Campaign", "template_id": str(template.id), "daily_limit": 1},
    ).json()

    response = client.post(f"/api/campaigns/{campaign['id']}/run")
    assert response.json()["sent_count"] == 1

    # Second run today should send nothing more — limit already reached.
    response2 = client.post(f"/api/campaigns/{campaign['id']}/run")
    assert response2.json()["sent_count"] == 0
    assert "limit" in response2.json()["skipped_reasons"][0].lower()


def test_run_campaign_does_not_resend_to_same_lead(client, make_lead, db_session):
    _make_approved_lead(db_session, make_lead)
    template = _make_template(db_session)

    campaign = client.post(
        "/api/campaigns", json={"name": "Test Campaign", "template_id": str(template.id)}
    ).json()

    first = client.post(f"/api/campaigns/{campaign['id']}/run").json()
    assert first["sent_count"] == 1

    second = client.post(f"/api/campaigns/{campaign['id']}/run").json()
    assert second["sent_count"] == 0
    assert second["skipped_count"] == 1


def test_enable_disable_campaign(client, db_session):
    template = _make_template(db_session)
    campaign = client.post(
        "/api/campaigns", json={"name": "Schedulable", "template_id": str(template.id)}
    ).json()

    response = client.post(f"/api/campaigns/{campaign['id']}/enable", json={"schedule": "hourly"})
    assert response.status_code == 200
    assert response.json()["is_enabled"] is True
    assert response.json()["schedule"] == "hourly"

    response = client.post(f"/api/campaigns/{campaign['id']}/disable")
    assert response.json()["is_enabled"] is False


def test_enable_campaign_rejects_invalid_schedule(client, db_session):
    template = _make_template(db_session)
    campaign = client.post(
        "/api/campaigns", json={"name": "Schedulable", "template_id": str(template.id)}
    ).json()

    response = client.post(
        f"/api/campaigns/{campaign['id']}/enable", json={"schedule": "every_5_minutes"}
    )
    assert response.status_code == 422


def test_run_due_only_executes_due_campaigns(client, make_lead, db_session):
    lead = _make_approved_lead(db_session, make_lead)
    template = _make_template(db_session)

    campaign = client.post(
        "/api/campaigns", json={"name": "Due Campaign", "template_id": str(template.id)}
    ).json()
    client.post(f"/api/campaigns/{campaign['id']}/enable", json={"schedule": "hourly"})

    response = client.post("/api/campaigns/run-due")
    assert response.status_code == 200
    body = response.json()
    assert body["checked"] == 1
    assert len(body["executed"]) == 1
    assert body["executed"][0]["sent_count"] == 1

    # Immediately due again should be skipped — last run was seconds ago, well inside the hourly interval.
    response2 = client.post("/api/campaigns/run-due")
    assert response2.json()["executed"] == []
