from app.services.leads import normalize_google_place, normalize_phone, normalize_website


def test_normalize_phone_strips_non_digits():
    assert normalize_phone("(042) 111-111-124") == "042111111124"


def test_normalize_phone_handles_none():
    assert normalize_phone(None) is None


def test_normalize_phone_empty_after_strip_is_none():
    assert normalize_phone("---") is None


def test_normalize_website_strips_protocol_and_www():
    assert normalize_website("https://www.Example.com/") == "example.com"


def test_normalize_website_handles_none():
    assert normalize_website(None) is None


def test_normalize_google_place_extracts_city_and_country():
    place = {
        "id": "place123",
        "displayName": {"text": "Test Cafe"},
        "formattedAddress": "123 Main St, Lahore, Pakistan",
        "addressComponents": [
            {"longText": "Lahore", "types": ["locality"]},
            {"longText": "Pakistan", "types": ["country"]},
        ],
        "location": {"latitude": 31.5, "longitude": 74.3},
        "types": ["cafe"],
        "nationalPhoneNumber": "0300 1234567",
        "websiteUri": "https://testcafe.com",
        "rating": 4.2,
        "userRatingCount": 50,
        "googleMapsUri": "https://maps.google.com/?cid=1",
    }
    normalized = normalize_google_place(place)
    assert normalized["business_name"] == "Test Cafe"
    assert normalized["city"] == "Lahore"
    assert normalized["country"] == "Pakistan"
    assert normalized["category"] == "Cafe"
    assert normalized["normalized_phone"] == "03001234567"
    assert normalized["normalized_website"] == "testcafe.com"
    assert normalized["source_id"] == "place123"
