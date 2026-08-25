import re

from app.models import Lead, ServiceRecommendation


def build_personalization_context(
    lead: Lead, recommendation: ServiceRecommendation | None
) -> dict[str, str]:
    return {
        "business_name": lead.business_name or "",
        "category": lead.category or "",
        "city": lead.city or "",
        "country": lead.country or "",
        "website": lead.website or "",
        "recommended_service": (
            recommendation.recommended_service.name if recommendation else ""
        ),
    }


def personalize(text: str, context: dict[str, str]) -> str:
    def replace(match: re.Match) -> str:
        key = match.group(1).strip()
        return context.get(key, match.group(0))

    return re.sub(r"\{\{\s*(\w+)\s*\}\}", replace, text)
