import re
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Lead, LeadSourceRecord


def normalize_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    return digits or None


def normalize_website(website: str | None) -> str | None:
    if not website:
        return None
    value = website.strip().lower()
    value = re.sub(r"^https?://", "", value)
    value = re.sub(r"^www\.", "", value)
    value = value.rstrip("/")
    return value or None


def normalize_google_place(place: dict, source: str = "google_places") -> dict:
    location = place.get("location") or {}
    address_components = place.get("addressComponents") or []

    city = None
    country = None
    for component in address_components:
        types = component.get("types", [])
        if "locality" in types and city is None:
            city = component.get("longText")
        if "country" in types and country is None:
            country = component.get("longText")

    types = place.get("types") or []
    category = types[0].replace("_", " ").title() if types else None

    phone = place.get("nationalPhoneNumber") or place.get("internationalPhoneNumber")
    website = place.get("websiteUri")

    return {
        "business_name": (place.get("displayName") or {}).get("text") or "Unknown business",
        "category": category,
        "address": place.get("formattedAddress"),
        "city": city,
        "country": country,
        "latitude": location.get("latitude"),
        "longitude": location.get("longitude"),
        "phone": phone,
        "normalized_phone": normalize_phone(phone),
        "email": None,
        "website": website,
        "normalized_website": normalize_website(website),
        "social_links": None,
        "source": source,
        "source_id": place["id"],
        "source_url": place.get("googleMapsUri"),
        "rating": place.get("rating"),
        "review_count": place.get("userRatingCount"),
    }


def find_existing_lead(db: Session, normalized: dict) -> Lead | None:
    """Duplicate check order per spec: source ID, normalized website, normalized phone, name+address."""
    lead = db.scalar(
        select(Lead).where(
            Lead.source == normalized["source"],
            Lead.source_id == normalized["source_id"],
        )
    )
    if lead:
        return lead

    if normalized.get("normalized_website"):
        lead = db.scalar(
            select(Lead).where(Lead.normalized_website == normalized["normalized_website"])
        )
        if lead:
            return lead

    if normalized.get("normalized_phone"):
        lead = db.scalar(
            select(Lead).where(Lead.normalized_phone == normalized["normalized_phone"])
        )
        if lead:
            return lead

    if normalized.get("business_name") and normalized.get("address"):
        lead = db.scalar(
            select(Lead).where(
                Lead.business_name == normalized["business_name"],
                Lead.address == normalized["address"],
            )
        )
        if lead:
            return lead

    return None


def upsert_lead(db: Session, normalized: dict, raw_place: dict) -> tuple[Lead, bool]:
    """Returns (lead, is_new)."""
    existing = find_existing_lead(db, normalized)
    now = datetime.utcnow()

    if existing:
        existing.last_seen = now
        db.add(
            LeadSourceRecord(
                lead_id=existing.id,
                source=normalized["source"],
                source_id=normalized["source_id"],
                raw_data=raw_place,
            )
        )
        return existing, False

    lead = Lead(**normalized, first_seen=now, last_seen=now)
    db.add(lead)
    db.flush()
    db.add(
        LeadSourceRecord(
            lead_id=lead.id,
            source=normalized["source"],
            source_id=normalized["source_id"],
            raw_data=raw_place,
        )
    )
    return lead, True
