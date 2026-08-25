import httpx
import respx

PLACES_URL = "https://places.googleapis.com/v1/places:searchText"

MOCK_PLACE = {
    "id": "mock-place-1",
    "displayName": {"text": "Mock Hotel"},
    "formattedAddress": "1 Mock St, Lahore, Pakistan",
    "addressComponents": [
        {"longText": "Lahore", "types": ["locality"]},
        {"longText": "Pakistan", "types": ["country"]},
    ],
    "location": {"latitude": 31.5, "longitude": 74.3},
    "types": ["hotel"],
    "nationalPhoneNumber": "0300 0000000",
    "websiteUri": "https://mockhotel.com",
    "rating": 4.5,
    "userRatingCount": 200,
    "googleMapsUri": "https://maps.google.com/?cid=1",
}


def test_search_without_api_key_fails_honestly(client, monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "")
    get_settings.cache_clear()

    response = client.post(
        "/api/leads/search",
        json={"business_type": "hotels", "location": "Lahore"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["run"]["status"] == "failed"
    assert "not configured" in body["run"]["error_message"]
    assert body["leads"] == []
    get_settings.cache_clear()


@respx.mock
def test_manual_search_creates_lead(client, monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "fake-key")
    get_settings.cache_clear()

    respx.post(PLACES_URL).mock(return_value=httpx.Response(200, json={"places": [MOCK_PLACE]}))

    response = client.post(
        "/api/leads/search",
        json={"business_type": "hotels", "location": "Lahore", "max_results": 5},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["run"]["status"] == "completed"
    assert body["run"]["new_leads_count"] == 1
    assert len(body["leads"]) == 1
    assert body["leads"][0]["business_name"] == "Mock Hotel"
    get_settings.cache_clear()


@respx.mock
def test_repeated_search_deduplicates(client, monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "fake-key")
    get_settings.cache_clear()

    respx.post(PLACES_URL).mock(return_value=httpx.Response(200, json={"places": [MOCK_PLACE]}))

    payload = {"business_type": "hotels", "location": "Lahore", "max_results": 5}
    first = client.post("/api/leads/search", json=payload).json()
    second = client.post("/api/leads/search", json=payload).json()

    assert first["run"]["new_leads_count"] == 1
    assert second["run"]["new_leads_count"] == 0
    assert second["run"]["duplicate_count"] == 1
    get_settings.cache_clear()


def test_search_requires_business_type_and_location(client):
    response = client.post("/api/leads/search", json={"business_type": "", "location": "Lahore"})
    assert response.status_code == 422


def test_get_nonexistent_lead_returns_404(client):
    response = client.get("/api/leads/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_list_leads_returns_created_leads(client, make_lead):
    make_lead(business_name="Alpha Cafe")
    make_lead(business_name="Beta Diner")

    response = client.get("/api/leads")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 2
    names = {lead["business_name"] for lead in body["items"]}
    assert {"Alpha Cafe", "Beta Diner"}.issubset(names)
