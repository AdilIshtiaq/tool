import httpx
import respx

PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
MOCK_PLACE = {
    "id": "config-test-place",
    "displayName": {"text": "Config Test Cafe"},
    "formattedAddress": "1 St, Lahore, Pakistan",
    "addressComponents": [],
    "location": {"latitude": 31.5, "longitude": 74.3},
    "types": ["cafe"],
    "rating": 4.0,
    "userRatingCount": 10,
}


def _enable_key(monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "fake-key")
    get_settings.cache_clear()


def test_create_and_list_search_configuration(client):
    response = client.post(
        "/api/search-configurations",
        json={"name": "Hotels in Lahore", "business_type": "hotels", "location": "Lahore"},
    )
    assert response.status_code == 200
    config_id = response.json()["id"]
    assert response.json()["is_enabled"] is False

    listed = client.get("/api/search-configurations").json()
    assert any(c["id"] == config_id for c in listed)


def test_enable_requires_valid_schedule(client):
    config_id = client.post(
        "/api/search-configurations",
        json={"name": "Test", "business_type": "hotels", "location": "Lahore"},
    ).json()["id"]

    bad = client.post(f"/api/search-configurations/{config_id}/enable", json={"schedule": "weekly"})
    assert bad.status_code == 422

    good = client.post(f"/api/search-configurations/{config_id}/enable", json={"schedule": "hourly"})
    assert good.status_code == 200
    assert good.json()["is_enabled"] is True
    assert good.json()["schedule"] == "hourly"


def test_disable_automation(client):
    config_id = client.post(
        "/api/search-configurations",
        json={"name": "Test", "business_type": "hotels", "location": "Lahore"},
    ).json()["id"]
    client.post(f"/api/search-configurations/{config_id}/enable", json={"schedule": "daily"})

    response = client.post(f"/api/search-configurations/{config_id}/disable")
    assert response.status_code == 200
    assert response.json()["is_enabled"] is False


@respx.mock
def test_run_due_executes_never_run_enabled_config(client, monkeypatch):
    _enable_key(monkeypatch)
    respx.post(PLACES_URL).mock(return_value=httpx.Response(200, json={"places": [MOCK_PLACE]}))

    config_id = client.post(
        "/api/search-configurations",
        json={"name": "Never run yet", "business_type": "cafes", "location": "Lahore"},
    ).json()["id"]
    client.post(f"/api/search-configurations/{config_id}/enable", json={"schedule": "daily"})

    response = client.post("/api/search-configurations/run-due")
    assert response.status_code == 200
    body = response.json()
    assert body["checked"] == 1
    assert len(body["executed"]) == 1
    assert body["executed"][0]["run"]["status"] == "completed"


def test_run_due_skips_disabled_configs(client):
    client.post(
        "/api/search-configurations",
        json={"name": "Disabled config", "business_type": "cafes", "location": "Lahore"},
    )
    response = client.post("/api/search-configurations/run-due")
    assert response.status_code == 200
    assert response.json()["checked"] == 0


@respx.mock
def test_run_due_skips_recently_run_config(client, monkeypatch):
    _enable_key(monkeypatch)
    respx.post(PLACES_URL).mock(return_value=httpx.Response(200, json={"places": [MOCK_PLACE]}))

    config_id = client.post(
        "/api/search-configurations",
        json={"name": "Recently run", "business_type": "cafes", "location": "Lahore"},
    ).json()["id"]
    client.post(f"/api/search-configurations/{config_id}/enable", json={"schedule": "hourly"})

    # First run-due executes it (never run before).
    first = client.post("/api/search-configurations/run-due").json()
    assert len(first["executed"]) == 1

    # Second run-due immediately after should skip it (not due yet under "hourly").
    second = client.post("/api/search-configurations/run-due").json()
    assert len(second["executed"]) == 0
    assert second["checked"] == 1
