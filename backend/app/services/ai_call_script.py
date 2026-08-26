from app.services.ai_provider import AllProvidersFailedError, call_structured

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "opening": {"type": "string"},
        "reason_for_calling": {"type": "string"},
        "business_observation": {"type": "string"},
        "value_statement": {"type": "string"},
        "discovery_questions": {"type": "array", "items": {"type": "string"}},
        "objection_prompts": {"type": "array", "items": {"type": "string"}},
        "next_step": {"type": "string"},
    },
    "required": [
        "opening",
        "reason_for_calling",
        "business_observation",
        "value_statement",
        "discovery_questions",
        "objection_prompts",
        "next_step",
    ],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """You are writing a manual cold-call script for a salesperson to read from, based \
ONLY on the business information and analysis given to you. Never invent facts about the business, \
never invent prior relationships, never invent prices or guarantees.

Structure your output into exactly these parts:
1. opening — a short, natural way to greet and introduce yourself and the company.
2. reason_for_calling — why you're calling this specific business.
3. business_observation — one specific, true observation about the business drawn only from the \
provided data/analysis (not invented).
4. value_statement — a short statement of the value the recommended service could bring.
5. discovery_questions — 2-4 open questions to understand their needs.
6. objection_prompts — 2-3 short responses to common objections (e.g. "we already have a website", \
"not interested right now"), grounded only in the given service/analysis.
7. next_step — a clear, low-pressure ask for what happens next.
"""


class AICallScriptError(Exception):
    pass


def generate_call_script(
    openai_api_key: str,
    anthropic_api_key: str,
    gemini_api_key: str,
    lead_info: dict,
    analysis_summary: str | None,
    recommended_service: str | None,
    reasoning: str | None,
) -> dict:
    if not openai_api_key and not anthropic_api_key and not gemini_api_key:
        raise AICallScriptError("No AI provider is configured (OpenAI, Anthropic, or Gemini API key required).")

    prompt_parts = [
        "## Business information",
        json.dumps(lead_info, indent=2),
    ]
    if analysis_summary:
        prompt_parts += ["", f"## AI analysis summary: {analysis_summary}"]
    if recommended_service:
        prompt_parts += [
            "",
            f"## Recommended service: {recommended_service}",
            f"## Why this service fits: {reasoning or 'not specified'}",
        ]
    else:
        prompt_parts += [
            "",
            "## No AI analysis has been run yet for this lead — keep the script general "
            "and do not claim a specific recommended service.",
        ]

    try:
        return call_structured(
            system_prompt=SYSTEM_PROMPT,
            user_prompt="\n".join(prompt_parts),
            schema_name="call_script",
            json_schema=RESPONSE_SCHEMA,
            api_keys={
                "openai": openai_api_key,
                "anthropic": anthropic_api_key,
                "gemini": gemini_api_key,
            },
        )
    except AllProvidersFailedError as exc:
        raise AICallScriptError(str(exc)) from exc


def format_script_text(script: dict) -> str:
    lines = [
        "1. OPENING",
        script["opening"],
        "",
        "2. REASON FOR CALLING",
        script["reason_for_calling"],
        "",
        "3. BUSINESS OBSERVATION",
        script["business_observation"],
        "",
        "4. VALUE STATEMENT",
        script["value_statement"],
        "",
        "5. DISCOVERY QUESTIONS",
    ]
    lines += [f"- {q}" for q in script["discovery_questions"]]
    lines += ["", "6. OBJECTION PROMPTS"]
    lines += [f"- {o}" for o in script["objection_prompts"]]
    lines += ["", "7. NEXT STEP", script["next_step"]]
    return "\n".join(lines)
