import httpx
import pytest
import respx

from app.services.ai_analysis import AIAnalysisError, analyze_lead
from app.services.google_places import GooglePlacesClient, GooglePlacesError

PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


class TestGooglePlacesErrorHandling:
    def test_missing_api_key_raises_without_network_call(self):
        client = GooglePlacesClient(api_key="")
        with pytest.raises(GooglePlacesError, match="not configured"):
            client.text_search(business_type="hotels", location="Lahore")

    @respx.mock
    def test_auth_failure_raises_clear_error(self):
        respx.post(PLACES_URL).mock(return_value=httpx.Response(401))
        client = GooglePlacesClient(api_key="bad-key")
        with pytest.raises(GooglePlacesError, match="authentication failed"):
            client.text_search(business_type="hotels", location="Lahore")

    @respx.mock
    def test_rate_limit_raises_clear_error(self):
        respx.post(PLACES_URL).mock(return_value=httpx.Response(429))
        client = GooglePlacesClient(api_key="key")
        with pytest.raises(GooglePlacesError, match="rate limit"):
            client.text_search(business_type="hotels", location="Lahore")

    @respx.mock
    def test_server_error_raises_clear_error(self):
        respx.post(PLACES_URL).mock(return_value=httpx.Response(500))
        client = GooglePlacesClient(api_key="key")
        with pytest.raises(GooglePlacesError, match="server error"):
            client.text_search(business_type="hotels", location="Lahore")

    @respx.mock
    def test_timeout_raises_clear_error(self):
        respx.post(PLACES_URL).mock(side_effect=httpx.TimeoutException("timed out"))
        client = GooglePlacesClient(api_key="key")
        with pytest.raises(GooglePlacesError, match="timed out"):
            client.text_search(business_type="hotels", location="Lahore")

    @respx.mock
    def test_successful_response_returns_places(self):
        respx.post(PLACES_URL).mock(
            return_value=httpx.Response(200, json={"places": [{"id": "abc"}]})
        )
        client = GooglePlacesClient(api_key="key")
        places = client.text_search(business_type="hotels", location="Lahore")
        assert places == [{"id": "abc"}]

    @respx.mock
    def test_paginates_past_the_20_result_page_cap(self, monkeypatch):
        import app.services.google_places as google_places_module

        monkeypatch.setattr(google_places_module.time, "sleep", lambda _seconds: None)

        page_one = [{"id": f"page1-{i}"} for i in range(20)]
        page_two = [{"id": f"page2-{i}"} for i in range(20)]
        page_three = [{"id": f"page3-{i}"} for i in range(10)]

        call_count = {"n": 0}

        def responder(request):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return httpx.Response(200, json={"places": page_one, "nextPageToken": "tok1"})
            if call_count["n"] == 2:
                return httpx.Response(200, json={"places": page_two, "nextPageToken": "tok2"})
            return httpx.Response(200, json={"places": page_three})

        respx.post(PLACES_URL).mock(side_effect=responder)

        client = GooglePlacesClient(api_key="key")
        places = client.text_search(business_type="hotels", location="Lahore", max_results=50)

        assert len(places) == 50
        assert call_count["n"] == 3

    @respx.mock
    def test_stops_when_google_runs_out_of_results(self, monkeypatch):
        """Google's own cap is often well under 100 - fewer results than
        requested is a normal outcome, not a bug, once nextPageToken is absent."""
        import app.services.google_places as google_places_module

        monkeypatch.setattr(google_places_module.time, "sleep", lambda _seconds: None)

        respx.post(PLACES_URL).mock(
            return_value=httpx.Response(200, json={"places": [{"id": "only-one"}]})
        )
        client = GooglePlacesClient(api_key="key")
        places = client.text_search(business_type="hotels", location="Lahore", max_results=100)
        assert places == [{"id": "only-one"}]


class TestAIAnalysisErrorHandling:
    def test_missing_api_key_raises_without_network_call(self):
        with pytest.raises(AIAnalysisError, match="No AI provider is configured"):
            analyze_lead(
                openai_api_key="",
                anthropic_api_key="",
                gemini_api_key="",
                lead_info={},
                analysis_rules=[],
                service_catalog=[{"name": "SEO"}],
            )

    def test_empty_catalog_raises_before_network_call(self):
        with pytest.raises(AIAnalysisError, match="No enabled services"):
            analyze_lead(
                openai_api_key="key",
                anthropic_api_key="",
                gemini_api_key="",
                lead_info={},
                analysis_rules=[],
                service_catalog=[],
            )

    @respx.mock
    def test_auth_failure_with_no_fallback_configured_raises(self):
        respx.post(OPENAI_URL).mock(return_value=httpx.Response(401))
        with pytest.raises(AIAnalysisError, match="authentication failed"):
            analyze_lead(
                openai_api_key="bad",
                anthropic_api_key="",
                gemini_api_key="",
                lead_info={},
                analysis_rules=[],
                service_catalog=[{"name": "SEO"}],
            )

    @respx.mock
    def test_insufficient_quota_gives_actionable_message(self):
        respx.post(OPENAI_URL).mock(
            return_value=httpx.Response(429, json={"error": {"type": "insufficient_quota"}})
        )
        with pytest.raises(AIAnalysisError, match="no credits remaining"):
            analyze_lead(
                openai_api_key="key",
                anthropic_api_key="",
                gemini_api_key="",
                lead_info={},
                analysis_rules=[],
                service_catalog=[{"name": "SEO"}],
            )

    @respx.mock
    def test_recommended_service_not_in_catalog_is_rejected(self):
        """The AI must never invent a service outside the enabled catalog."""
        respx.post(OPENAI_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": '{"summary":"x","opportunities":[],"score":50,'
                                '"confidence":0.8,"evidence":[],"missing_information":[],'
                                '"next_action":"x","recommended_service":"Made Up Service",'
                                '"secondary_services":[],"reasoning":"x"}'
                            }
                        }
                    ]
                },
            )
        )
        with pytest.raises(AIAnalysisError, match="not in the enabled service catalog"):
            analyze_lead(
                openai_api_key="key",
                anthropic_api_key="",
                gemini_api_key="",
                lead_info={},
                analysis_rules=[],
                service_catalog=[{"name": "SEO"}],
            )

    @respx.mock
    def test_valid_recommendation_within_catalog_succeeds(self):
        respx.post(OPENAI_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": '{"summary":"x","opportunities":[],"score":50,'
                                '"confidence":0.8,"evidence":[],"missing_information":[],'
                                '"next_action":"x","recommended_service":"SEO",'
                                '"secondary_services":[],"reasoning":"x"}'
                            }
                        }
                    ]
                },
            )
        )
        result = analyze_lead(
            openai_api_key="key",
            anthropic_api_key="",
            gemini_api_key="",
            lead_info={},
            analysis_rules=[],
            service_catalog=[{"name": "SEO"}],
        )
        assert result["recommended_service"] == "SEO"

    @respx.mock
    def test_falls_back_to_anthropic_when_openai_out_of_credits(self):
        """The actual scenario this was built for: OpenAI has no credits, Anthropic picks up the request."""
        respx.post(OPENAI_URL).mock(
            return_value=httpx.Response(429, json={"error": {"type": "insufficient_quota"}})
        )
        respx.post(ANTHROPIC_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "content": [
                        {
                            "type": "tool_use",
                            "input": {
                                "summary": "x",
                                "opportunities": [],
                                "score": 50,
                                "confidence": 0.8,
                                "evidence": [],
                                "missing_information": [],
                                "next_action": "x",
                                "recommended_service": "SEO",
                                "secondary_services": [],
                                "reasoning": "x",
                            },
                        }
                    ]
                },
            )
        )
        result = analyze_lead(
            openai_api_key="out-of-credits-key",
            anthropic_api_key="working-key",
            gemini_api_key="",
            lead_info={},
            analysis_rules=[],
            service_catalog=[{"name": "SEO"}],
        )
        assert result["recommended_service"] == "SEO"

    @respx.mock
    def test_both_providers_failing_raises_with_both_reasons(self):
        respx.post(OPENAI_URL).mock(return_value=httpx.Response(401))
        respx.post(ANTHROPIC_URL).mock(return_value=httpx.Response(401))
        with pytest.raises(AIAnalysisError, match="openai.*anthropic|anthropic.*openai"):
            analyze_lead(
                openai_api_key="bad",
                anthropic_api_key="also-bad",
                gemini_api_key="",
                lead_info={},
                analysis_rules=[],
                service_catalog=[{"name": "SEO"}],
            )
