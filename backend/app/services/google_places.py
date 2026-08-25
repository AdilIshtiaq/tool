import httpx

PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

FIELD_MASK = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.addressComponents",
        "places.location",
        "places.types",
        "places.nationalPhoneNumber",
        "places.internationalPhoneNumber",
        "places.websiteUri",
        "places.rating",
        "places.userRatingCount",
        "places.googleMapsUri",
    ]
)


class GooglePlacesError(Exception):
    pass


class GooglePlacesClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def text_search(
        self,
        business_type: str,
        location: str,
        radius_meters: int | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        max_results: int = 20,
    ) -> list[dict]:
        if not self.api_key:
            raise GooglePlacesError("Google Places API key is not configured.")

        query = f"{business_type} in {location}" if location else business_type
        body: dict = {
            "textQuery": query,
            "maxResultCount": min(max(max_results, 1), 20),
        }
        if latitude is not None and longitude is not None:
            body["locationBias"] = {
                "circle": {
                    "center": {"latitude": latitude, "longitude": longitude},
                    "radius": float(radius_meters or 5000),
                }
            }

        headers = {
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": FIELD_MASK,
            "Content-Type": "application/json",
        }

        try:
            response = httpx.post(
                PLACES_TEXT_SEARCH_URL, json=body, headers=headers, timeout=20.0
            )
        except httpx.TimeoutException as exc:
            raise GooglePlacesError("Google Places API request timed out.") from exc
        except httpx.RequestError as exc:
            raise GooglePlacesError(f"Google Places API request failed: {exc}") from exc

        if response.status_code == 401 or response.status_code == 403:
            raise GooglePlacesError(
                "Google Places API authentication failed. Check the configured API key."
            )
        if response.status_code == 429:
            raise GooglePlacesError("Google Places API rate limit exceeded.")
        if response.status_code >= 500:
            raise GooglePlacesError("Google Places API server error.")
        if response.status_code != 200:
            raise GooglePlacesError(
                f"Google Places API returned unexpected status {response.status_code}: {response.text}"
            )

        data = response.json()
        return data.get("places", [])
