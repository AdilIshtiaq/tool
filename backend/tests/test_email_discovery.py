import httpx
import respx

from app.services.email_discovery import discover_email
from app.services.lead_enrichment import enrich_leads_missing_email


@respx.mock
def test_finds_mailto_link():
    respx.get("https://example-biz.com").mock(
        return_value=httpx.Response(200, text='<a href="mailto:hello@example-biz.com">Email us</a>')
    )
    assert discover_email("https://example-biz.com") == "hello@example-biz.com"


@respx.mock
def test_finds_plain_text_email_as_fallback():
    respx.get("https://example-biz.com").mock(
        return_value=httpx.Response(200, text="Contact us at info@example-biz.com for details.")
    )
    assert discover_email("https://example-biz.com") == "info@example-biz.com"


@respx.mock
def test_ignores_platform_and_tracking_emails():
    respx.get("https://example-biz.com").mock(
        return_value=httpx.Response(
            200,
            text='<a href="mailto:noreply@sentry.io">debug</a> real contact: sales@example-biz.com',
        )
    )
    assert discover_email("https://example-biz.com") == "sales@example-biz.com"


@respx.mock
def test_falls_back_to_contact_page():
    def responder(request):
        if request.url.path == "/contact":
            return httpx.Response(200, text="Email: team@example-biz.com")
        return httpx.Response(200, text="<p>Home</p>")

    respx.get(host="example-biz.com").mock(side_effect=responder)
    assert discover_email("https://example-biz.com") == "team@example-biz.com"


@respx.mock
def test_returns_none_when_nothing_found():
    def responder(request):
        if request.url.path == "":
            return httpx.Response(200, text="<p>No contact info</p>")
        return httpx.Response(404)

    respx.get(host="example-biz.com").mock(side_effect=responder)
    assert discover_email("https://example-biz.com") is None


def test_returns_none_for_empty_website():
    assert discover_email("") is None
    assert discover_email(None) is None


@respx.mock
def test_enrich_leads_missing_email_updates_lead(db_session, make_lead):
    lead_with_site = make_lead(website="https://example-biz.com", email=None)
    lead_without_site = make_lead(website=None, email=None, source_id="no-site")
    lead_already_has_email = make_lead(
        website="https://already-has-email.com", email="existing@x.com", source_id="has-email"
    )

    respx.get("https://example-biz.com").mock(
        return_value=httpx.Response(200, text='<a href="mailto:contact@example-biz.com">Us</a>')
    )

    result = enrich_leads_missing_email(db_session)
    assert result["checked"] == 1  # only the one with a website and no email
    assert result["found"] == 1

    db_session.refresh(lead_with_site)
    assert lead_with_site.email == "contact@example-biz.com"
    db_session.refresh(lead_without_site)
    assert lead_without_site.email is None
    db_session.refresh(lead_already_has_email)
    assert lead_already_has_email.email == "existing@x.com"
