"""Shared multi-provider AI calling with automatic failover.

Every AI feature in this app (analysis, email drafting, call scripts, reply
classification) needs the same thing: send a system+user prompt, get back JSON
that matches a schema, and don't invent facts. Historically each feature had
its own hardcoded OpenAI-only client. This module gives them one shared entry
point that tries each configured provider in order and automatically falls
through to the next one if a provider fails (out of credits, down, rate
limited, etc.) — so adding a new provider later is a matter of adding one
function here, not touching every feature.
"""

import json

import httpx

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = "gpt-4o-mini"

ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-3-5-haiku-20241022"
ANTHROPIC_VERSION = "2023-06-01"

REQUEST_TIMEOUT = 60.0


class AIProviderError(Exception):
    """Raised by a single provider attempt. Callers of call_structured never see
    this directly — it's caught internally to decide whether to try the next
    provider."""


class AllProvidersFailedError(Exception):
    """Every configured provider failed (or none are configured). Carries the
    per-provider failure reasons so the caller can show something useful."""

    def __init__(self, attempts: list[tuple[str, str]]):
        self.attempts = attempts
        if not attempts:
            message = (
                "No AI provider is configured. Add OPENAI_API_KEY and/or "
                "ANTHROPIC_API_KEY to backend/.env."
            )
        else:
            details = "; ".join(f"{name}: {reason}" for name, reason in attempts)
            message = f"All configured AI providers failed. {details}"
        super().__init__(message)


def _call_openai(api_key: str, system_prompt: str, user_prompt: str, schema_name: str, json_schema: dict) -> dict:
    body = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": schema_name, "strict": True, "schema": json_schema},
        },
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        response = httpx.post(OPENAI_CHAT_URL, json=body, headers=headers, timeout=REQUEST_TIMEOUT)
    except httpx.TimeoutException as exc:
        raise AIProviderError("request timed out") from exc
    except httpx.RequestError as exc:
        raise AIProviderError(f"request failed: {exc}") from exc

    if response.status_code in (401, 403):
        raise AIProviderError("authentication failed — check the API key")
    if response.status_code == 429:
        try:
            error_body = response.json().get("error", {})
        except json.JSONDecodeError:
            error_body = {}
        if error_body.get("type") == "insufficient_quota":
            raise AIProviderError("account has no credits remaining")
        raise AIProviderError("rate limit exceeded")
    if response.status_code >= 500:
        raise AIProviderError("server error")
    if response.status_code != 200:
        raise AIProviderError(f"unexpected status {response.status_code}: {response.text}")

    data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        raise AIProviderError(f"returned unparseable output: {exc}") from exc


def _call_anthropic(api_key: str, system_prompt: str, user_prompt: str, schema_name: str, json_schema: dict) -> dict:
    body = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 4096,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
        "tools": [
            {
                "name": schema_name,
                "description": "Return the result in this exact structure.",
                "input_schema": json_schema,
            }
        ],
        "tool_choice": {"type": "tool", "name": schema_name},
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }

    try:
        response = httpx.post(ANTHROPIC_MESSAGES_URL, json=body, headers=headers, timeout=REQUEST_TIMEOUT)
    except httpx.TimeoutException as exc:
        raise AIProviderError("request timed out") from exc
    except httpx.RequestError as exc:
        raise AIProviderError(f"request failed: {exc}") from exc

    if response.status_code in (401, 403):
        raise AIProviderError("authentication failed — check the API key")
    if response.status_code == 429:
        raise AIProviderError("rate limit exceeded")
    if response.status_code == 400:
        try:
            message = response.json().get("error", {}).get("message", "")
        except json.JSONDecodeError:
            message = ""
        if "credit balance" in message.lower():
            raise AIProviderError("account has no credits remaining")
        raise AIProviderError(f"bad request: {message or response.text}")
    if response.status_code >= 500:
        raise AIProviderError("server error")
    if response.status_code != 200:
        raise AIProviderError(f"unexpected status {response.status_code}: {response.text}")

    data = response.json()
    try:
        tool_use = next(block for block in data["content"] if block.get("type") == "tool_use")
        return tool_use["input"]
    except (KeyError, StopIteration) as exc:
        raise AIProviderError(f"returned unparseable output: {exc}") from exc


# Registry of providers, tried in this order. Adding a new provider later is
# one entry here plus a _call_<provider> function above — no changes needed
# in any of the AI feature modules that call call_structured().
_PROVIDERS = [
    ("openai", lambda key: bool(key), _call_openai),
    ("anthropic", lambda key: bool(key), _call_anthropic),
]


def call_structured(
    system_prompt: str,
    user_prompt: str,
    schema_name: str,
    json_schema: dict,
    api_keys: dict[str, str],
) -> dict:
    """Tries each configured provider in order, falling through to the next one
    on any failure (auth, quota, rate limit, server error, timeout, unparseable
    output). Raises AllProvidersFailedError only if every provider fails."""
    attempts: list[tuple[str, str]] = []

    for name, has_key, call_fn in _PROVIDERS:
        key = api_keys.get(name, "")
        if not has_key(key):
            continue
        try:
            return call_fn(key, system_prompt, user_prompt, schema_name, json_schema)
        except AIProviderError as exc:
            attempts.append((name, str(exc)))
            continue

    raise AllProvidersFailedError(attempts)
