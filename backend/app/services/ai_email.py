import json

from app.services.ai_provider import AllProvidersFailedError, call_structured

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "subject": {"type": "string"},
        "body": {"type": "string"},
    },
    "required": ["subject", "body"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """You are writing a short, professional cold outreach email on behalf of a web/marketing \
agency. Use ONLY the facts given to you about the recipient business and the recommended service.

Rules you must follow:
- Never invent client names, existing relationships, results, prices, or any technical fact not given to you.
- Do not claim to have already worked with the business or any other company.
- Do not mention specific prices or guarantees.
- Keep it short (under 150 words), personalized to the specific business, and end with a clear, low-pressure call to action.
- Do NOT include a sign-off, signature, or closing name (e.g. "Best, [Your Name]") - a real signature is
  added automatically after your text. End on the call to action itself.
- Write the body as plain text (no markdown), using \\n for line breaks.
"""


class AIEmailError(Exception):
    pass


def generate_email_draft(
    openai_api_key: str,
    anthropic_api_key: str,
    gemini_api_key: str,
    lead_info: dict,
    recommended_service: str,
    reasoning: str,
    existing_template: dict | None = None,
) -> dict:
    if not openai_api_key and not anthropic_api_key and not gemini_api_key:
        raise AIEmailError("No AI provider is configured (OpenAI, Anthropic, or Gemini API key required).")

    prompt_parts = [
        "## Recipient business (only approved facts — do not add anything else)",
        json.dumps(lead_info, indent=2),
        "",
        f"## Recommended service: {recommended_service}",
        f"## Why this service fits: {reasoning}",
    ]
    if existing_template:
        prompt_parts += [
            "",
            "## Personalize this existing template rather than writing from scratch",
            json.dumps(existing_template, indent=2),
        ]

    try:
        return call_structured(
            system_prompt=SYSTEM_PROMPT,
            user_prompt="\n".join(prompt_parts),
            schema_name="email_draft",
            json_schema=RESPONSE_SCHEMA,
            api_keys={
                "openai": openai_api_key,
                "anthropic": anthropic_api_key,
                "gemini": gemini_api_key,
            },
        )
    except AllProvidersFailedError as exc:
        raise AIEmailError(str(exc)) from exc
