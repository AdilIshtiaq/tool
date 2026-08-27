import json

import httpx
import respx

from app.models import QualificationRule, Service
from app.services.lead_pipeline import process_new_leads

OPENAI_URL = "https://api.openai.com/v1/chat/completions"


def _rule(field, operator, expected_value=None, **kwargs):
    kwargs.setdefault("enabled", True)
    kwargs.setdefault("priority", 0)
    return QualificationRule(
        name="test rule", field=field, operator=operator, expected_value=expected_value, **kwargs
    )


def _ai_response(recommended_service):
    return {
        "summary": "x",
        "opportunities": [],
        "score": 50,
        "confidence": 0.8,
        "evidence": [],
        "missing_information": [],
        "next_action": "x",
        "recommended_service": recommended_service,
        "secondary_services": [],
        "reasoning": "x",
    }


@respx.mock
def test_qualifies_then_analyzes_only_qualified_leads(db_session, make_lead, monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("OPENAI_API_KEY", "fake-key")
    get_settings.cache_clear()

    db_session.add(_rule("website", "exists", priority=1))
    service = Service(name="SEO", enabled=True)
    db_session.add(service)
    db_session.commit()

    qualifying_lead = make_lead(business_name="Has Website", website="https://x.com")
    failing_lead = make_lead(business_name="No Website", website=None, source_id="no-site")

    respx.post(OPENAI_URL).mock(
        return_value=httpx.Response(
            200, json={"choices": [{"message": {"content": json.dumps(_ai_response("SEO"))}}]}
        )
    )

    result = process_new_leads(db_session)

    assert result["qualified"] == 1
    assert result["not_qualified"] == 1
    assert result["analyzed"] == 1

    db_session.refresh(qualifying_lead)
    db_session.refresh(failing_lead)
    assert qualifying_lead.status == "analyzed"
    assert failing_lead.status == "not_qualified"
    get_settings.cache_clear()


def test_never_reprocesses_already_qualified_leads(db_session, make_lead):
    db_session.add(_rule("website", "exists", priority=1))
    db_session.commit()

    make_lead(website="https://x.com")

    first = process_new_leads(db_session)
    assert first["qualified"] == 1

    second = process_new_leads(db_session)
    assert second["qualified"] == 0
    assert second["not_qualified"] == 0
    assert second["needs_review"] == 0


@respx.mock
def test_never_reanalyzes_already_analyzed_leads(db_session, make_lead, monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("OPENAI_API_KEY", "fake-key")
    get_settings.cache_clear()

    db_session.add(_rule("website", "exists", priority=1))
    service = Service(name="SEO", enabled=True)
    db_session.add(service)
    db_session.commit()
    make_lead(website="https://x.com")

    respx.post(OPENAI_URL).mock(
        return_value=httpx.Response(
            200, json={"choices": [{"message": {"content": json.dumps(_ai_response("SEO"))}}]}
        )
    )

    first = process_new_leads(db_session)
    assert first["analyzed"] == 1

    second = process_new_leads(db_session)
    assert second["analyzed"] == 0
    get_settings.cache_clear()


def test_endpoint_returns_pipeline_summary(client, make_lead, db_session):
    db_session.add(_rule("website", "exists", priority=1))
    db_session.commit()
    make_lead(website=None)

    response = client.post("/api/leads/process-new")
    assert response.status_code == 200
    body = response.json()
    assert body["not_qualified"] == 1
    assert body["analyzed"] == 0
