import time

import httpx

PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

# Google's Text Search (New) caps a single page at 20 results. Getting more
# requires paginating with nextPageToken - Google requires a short delay
# before a token becomes usable.
MAX_PAGE_SIZE = 20
PAGE_TOKEN_DELAY_SECONDS = 2.0

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

    def _post(self, body: dict) -> dict:
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
        return response.json()

    def text_search(
        self,
        business_type: str,
        location: str,
        radius_meters: int | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        max_results: int = 20,
    ) -> list[dict]:
        """Paginates with nextPageToken since a single page caps at 20 results.
        Google's own result cap for Text Search is well below most max_results
        values requested here (often ~60), so fewer than max_results coming
        back is expected, not a bug — it's the source running out of matches."""
        if not self.api_key:
            raise GooglePlacesError("Google Places API key is not configured.")

        query = f"{business_type} in {location}" if location else business_type
        base_body: dict = {"textQuery": query}
        if latitude is not None and longitude is not None:
            base_body["locationBias"] = {
                "circle": {
                    "center": {"latitude": latitude, "longitude": longitude},
                    "radius": float(radius_meters or 5000),
                }
            }

        places: list[dict] = []
        page_token: str | None = None
        while len(places) < max_results:
            body = dict(base_body)
            body["maxResultCount"] = min(max_results - len(places), MAX_PAGE_SIZE)
            if page_token:
                body["pageToken"] = page_token
                time.sleep(PAGE_TOKEN_DELAY_SECONDS)

            data = self._post(body)
            places.extend(data.get("places", []))

            page_token = data.get("nextPageToken")
            if not page_token:
                break

        return places[:max_results]
