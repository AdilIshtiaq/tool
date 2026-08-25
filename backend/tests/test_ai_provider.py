import httpx
import pytest
import respx

from app.services.ai_provider import AllProvidersFailedError, call_structured

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

SCHEMA = {
    "type": "object",
    "properties": {"answer": {"type": "string"}},
    "required": ["answer"],
    "additionalProperties": False,
}


def _openai_success(answer="hello"):
    return httpx.Response(
        200,
        json={"choices": [{"message": {"content": f'{{"answer":"{answer}"}}'}}]},
    )


def _anthropic_success(answer="hello"):
    return httpx.Response(
        200,
        json={"content": [{"type": "tool_use", "input": {"answer": answer}}]},
    )


def test_no_providers_configured_raises_with_helpful_message():
    with pytest.raises(AllProvidersFailedError, match="No AI provider is configured"):
        call_structured("sys", "user", "test_schema", SCHEMA, api_keys={"openai": "", "anthropic": ""})


@respx.mock
def test_uses_openai_when_only_openai_configured():
    respx.post(OPENAI_URL).mock(return_value=_openai_success("from-openai"))
    result = call_structured(
        "sys", "user", "test_schema", SCHEMA, api_keys={"openai": "key", "anthropic": ""}
    )
    assert result["answer"] == "from-openai"


@respx.mock
def test_uses_anthropic_when_only_anthropic_configured():
    respx.post(ANTHROPIC_URL).mock(return_value=_anthropic_success("from-anthropic"))
    result = call_structured(
        "sys", "user", "test_schema", SCHEMA, api_keys={"openai": "", "anthropic": "key"}
    )
    assert result["answer"] == "from-anthropic"


@respx.mock
def test_prefers_openai_when_both_configured_and_both_working():
    openai_route = respx.post(OPENAI_URL).mock(return_value=_openai_success("from-openai"))
    anthropic_route = respx.post(ANTHROPIC_URL).mock(return_value=_anthropic_success("from-anthropic"))

    result = call_structured(
        "sys", "user", "test_schema", SCHEMA, api_keys={"openai": "key", "anthropic": "key"}
    )

    assert result["answer"] == "from-openai"
    assert openai_route.called
    assert not anthropic_route.called


@respx.mock
def test_falls_back_to_anthropic_when_openai_fails():
    respx.post(OPENAI_URL).mock(return_value=httpx.Response(500))
    anthropic_route = respx.post(ANTHROPIC_URL).mock(return_value=_anthropic_success("from-anthropic"))

    result = call_structured(
        "sys", "user", "test_schema", SCHEMA, api_keys={"openai": "key", "anthropic": "key"}
    )

    assert result["answer"] == "from-anthropic"
    assert anthropic_route.called


@respx.mock
def test_openai_out_of_credits_falls_back_to_anthropic():
    respx.post(OPENAI_URL).mock(
        return_value=httpx.Response(429, json={"error": {"type": "insufficient_quota"}})
    )
    respx.post(ANTHROPIC_URL).mock(return_value=_anthropic_success("saved-by-anthropic"))

    result = call_structured(
        "sys", "user", "test_schema", SCHEMA, api_keys={"openai": "key", "anthropic": "key"}
    )
    assert result["answer"] == "saved-by-anthropic"


@respx.mock
def test_both_providers_failing_raises_with_all_reasons():
    respx.post(OPENAI_URL).mock(return_value=httpx.Response(401))
    respx.post(ANTHROPIC_URL).mock(return_value=httpx.Response(401))

    with pytest.raises(AllProvidersFailedError) as exc_info:
        call_structured(
            "sys", "user", "test_schema", SCHEMA, api_keys={"openai": "key", "anthropic": "key"}
        )

    names = [name for name, _ in exc_info.value.attempts]
    assert names == ["openai", "anthropic"]


@respx.mock
def test_anthropic_credit_balance_error_detected_from_400_message():
    respx.post(ANTHROPIC_URL).mock(
        return_value=httpx.Response(
            400, json={"error": {"message": "Your credit balance is too low."}}
        )
    )
    with pytest.raises(AllProvidersFailedError, match="no credits remaining"):
        call_structured(
            "sys", "user", "test_schema", SCHEMA, api_keys={"openai": "", "anthropic": "key"}
        )
