from app.services.ai_provider import AllProvidersFailedError, call_structured

CATEGORIES = [
    "Positive",
    "Interested",
    "Question",
    "Follow-up",
    "Neutral",
    "Negative",
    "Unsubscribe",
    "Out of office",
    "Invalid",
]

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": CATEGORIES},
        "confidence": {"type": "number"},
        "summary": {"type": "string"},
        "suggested_action": {"type": "string"},
        "review_required": {"type": "boolean"},
    },
    "required": ["category", "confidence", "summary", "suggested_action", "review_required"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = f"""You are classifying an email reply received by a sales team, from a business \
that was previously contacted about a service.

Classify into exactly one category: {", ".join(CATEGORIES)}.

Rules:
- confidence is 0 to 1.
- review_required must be true whenever confidence is below 0.7, or the category is Negative, \
Unsubscribe, or Invalid, or anything ambiguous.
- summary should be one or two sentences capturing what the sender actually said.
- suggested_action is a short, concrete next step for the salesperson (or "Stop outreach" for \
Unsubscribe/Negative/Invalid).
"""


class ReplyClassificationError(Exception):
    pass


def classify_reply(
    openai_api_key: str, anthropic_api_key: str, from_email: str, subject: str, body: str
) -> dict:
    if not openai_api_key and not anthropic_api_key:
        raise ReplyClassificationError("No AI provider is configured (OpenAI or Anthropic API key required).")

    user_prompt = f"From: {from_email}\nSubject: {subject}\n\nBody:\n{body}"

    try:
        return call_structured(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema_name="reply_classification",
            json_schema=RESPONSE_SCHEMA,
            api_keys={"openai": openai_api_key, "anthropic": anthropic_api_key},
        )
    except AllProvidersFailedError as exc:
        raise ReplyClassificationError(str(exc)) from exc
