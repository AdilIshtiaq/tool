import json

from app.services.ai_provider import AllProvidersFailedError, call_structured

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "opportunities": {"type": "array", "items": {"type": "string"}},
        "score": {"type": "number"},
        "confidence": {"type": "number"},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "missing_information": {"type": "array", "items": {"type": "string"}},
        "next_action": {"type": "string"},
        "recommended_service": {"type": "string"},
        "secondary_services": {"type": "array", "items": {"type": "string"}},
        "reasoning": {"type": "string"},
    },
    "required": [
        "summary",
        "opportunities",
        "score",
        "confidence",
        "evidence",
        "missing_information",
        "next_action",
        "recommended_service",
        "secondary_services",
        "reasoning",
    ],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """You are a business analyst for a web/marketing agency. You analyze a lead \
(a business) using ONLY the information provided to you, and recommend ONE service from the \
provided catalog that represents the best commercial opportunity.

Rules you must follow:
- Use only the provided information. Never invent facts about the business.
- If information needed to be confident is missing, list it in missing_information and lower your confidence.
- recommended_service MUST be exactly one of the names in the provided service catalog. Never invent a service.
- secondary_services must also be exact names from the catalog (can be empty).
- reasoning must clearly explain why the recommended service fits this specific business \
("Why this service?").
- confidence is 0 to 1. score is 0 to 100 (commercial opportunity size, not qualification score).
- Follow any additional analysis guidance rules provided, if present.
"""


class AIAnalysisError(Exception):
    pass


def build_user_prompt(lead_info: dict, analysis_rules: list[str], service_catalog: list[dict]) -> str:
    parts = [
        "## Lead / business information (only approved fields — do not assume anything else)",
        json.dumps(lead_info, indent=2),
        "",
        "## Service catalog (choose recommended_service and secondary_services only from these names)",
        json.dumps([s["name"] for s in service_catalog], indent=2),
    ]
    if analysis_rules:
        parts += [
            "",
            "## Additional analysis guidance rules from the admin",
            "\n".join(f"- {r}" for r in analysis_rules),
        ]
    return "\n".join(parts)


def analyze_lead(
    openai_api_key: str,
    anthropic_api_key: str,
    lead_info: dict,
    analysis_rules: list[str],
    service_catalog: list[dict],
) -> dict:
    if not openai_api_key and not anthropic_api_key:
        raise AIAnalysisError("No AI provider is configured (OpenAI or Anthropic API key required).")
    if not service_catalog:
        raise AIAnalysisError("No enabled services in the catalog to recommend from.")

    try:
        parsed = call_structured(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=build_user_prompt(lead_info, analysis_rules, service_catalog),
            schema_name="lead_analysis",
            json_schema=RESPONSE_SCHEMA,
            api_keys={"openai": openai_api_key, "anthropic": anthropic_api_key},
        )
    except AllProvidersFailedError as exc:
        raise AIAnalysisError(str(exc)) from exc

    # Validate the recommendation actually exists in the catalog we sent — AI must not invent services.
    catalog_names = {s["name"] for s in service_catalog}
    if parsed["recommended_service"] not in catalog_names:
        raise AIAnalysisError(
            f"AI recommended '{parsed['recommended_service']}', which is not in the enabled service catalog."
        )
    parsed["secondary_services"] = [s for s in parsed["secondary_services"] if s in catalog_names]

    return parsed
