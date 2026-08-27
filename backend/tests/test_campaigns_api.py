import json
from datetime import datetime, timedelta, timezone

import httpx
import respx

from app.models import LeadAnalysis, Service, ServiceRecommendation, Template

OPENAI_URL = "https://api.openai.com/v1/chat/completions"


def _mock_ai_draft(subject="AI subject", body="AI body"):
    respx.post(OPENAI_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": json.dumps({"subject": subject, "body": body})}}
                ]
            },
        )
    )


def _enable_ai(monkeypatch):
    """Isolates from whatever real keys happen to be in backend/.env - these
    tests go through get_settings(), unlike the service-level tests that
    call analyze_lead()/generate_email_draft() directly with explicit keys."""
    from app.config import get_settings

    monkeypatch.setenv("OPENAI_API_KEY", "fake-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    get_settings.cache_clear()


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


@respx.mock
def test_run_campaign_sends_to_approved_leads(client, make_lead, db_session, monkeypatch):
    _enable_ai(monkeypatch)
    _mock_ai_draft(subject="noticed something specific", body="a genuinely personalized email")

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
    sent = next(m for m in messages if m["lead_id"] == str(lead.id))
    assert sent["subject"] == "noticed something specific"
    assert sent["body"].startswith("a genuinely personalized email")
    assert "Adil Ishtiaq" in sent["body"]


@respx.mock
def test_run_campaign_skips_lead_when_ai_draft_fails_no_fallback(client, make_lead, db_session, monkeypatch):
    """Sending the raw template when AI fails would silently defeat the
    whole point of AI-personalized outreach - a skip is the correct outcome."""
    _enable_ai(monkeypatch)
    respx.post(OPENAI_URL).mock(return_value=httpx.Response(401))

    _make_approved_lead(db_session, make_lead)
    template = _make_template(db_session)

    campaign = client.post(
        "/api/campaigns", json={"name": "Test Campaign", "template_id": str(template.id)}
    ).json()

    response = client.post(f"/api/campaigns/{campaign['id']}/run")
    body = response.json()
    assert body["sent_count"] == 0
    assert body["skipped_count"] == 1
    assert "AI draft failed" in body["skipped_reasons"][0]


def test_run_campaign_skips_leads_without_approval(client, make_lead, db_session):
    make_lead(business_name="Not approved", email="notapproved@example.com")
    template = _make_template(db_session)

    campaign = client.post(
        "/api/campaigns", json={"name": "Test Campaign", "template_id": str(template.id)}
    ).json()

    response = client.post(f"/api/campaigns/{campaign['id']}/run")
    assert response.status_code == 200
    assert response.json()["sent_count"] == 0


@respx.mock
def test_run_campaign_respects_daily_limit(client, make_lead, db_session, monkeypatch):
    _enable_ai(monkeypatch)
    _mock_ai_draft()

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


@respx.mock
def test_run_campaign_does_not_resend_to_same_lead(client, make_lead, db_session, monkeypatch):
    _enable_ai(monkeypatch)
    _mock_ai_draft()

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


@respx.mock
def test_run_due_only_executes_due_campaigns(client, make_lead, db_session, monkeypatch):
    _enable_ai(monkeypatch)
    _mock_ai_draft()

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
