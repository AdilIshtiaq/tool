import logging
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Lead, LeadSearchRun
from app.services.google_places import GooglePlacesClient, GooglePlacesError
from app.services.leads import normalize_google_place, upsert_lead

logger = logging.getLogger("nexcraft.search")


def execute_lead_search(
    db: Session,
    search_params: dict,
    mode: str,
    search_configuration_id: uuid.UUID | None = None,
) -> tuple[LeadSearchRun, list[Lead]]:
    """Runs a lead source search and persists results. Used by Manual and Semi-Automatic modes."""
    settings = get_settings()

    run = LeadSearchRun(
        mode=mode,
        search_configuration_id=search_configuration_id,
        search_config=search_params,
        status="running",
        started_at=datetime.utcnow(),
    )
    db.add(run)
    db.flush()

    source = search_params.get("source", "google_places")
    if source != "google_places":
        run.status = "failed"
        run.error_message = f"Unsupported source: {source}"
        run.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(run)
        return run, []

    client = GooglePlacesClient(api_key=settings.google_places_api_key)

    try:
        places = client.text_search(
            business_type=search_params["business_type"],
            location=search_params["location"],
            radius_meters=search_params.get("radius_meters"),
            latitude=search_params.get("latitude"),
            longitude=search_params.get("longitude"),
            max_results=search_params.get("max_results", 20),
        )
    except GooglePlacesError as exc:
        logger.error("Lead search run %s failed: %s", run.id, exc)
        run.status = "failed"
        run.error_message = str(exc)
        run.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(run)
        return run, []

    saved_leads: list[Lead] = []
    new_count = 0
    duplicate_count = 0
    failed_count = 0

    for place in places:
        try:
            normalized = normalize_google_place(place, source=source)
            lead, is_new = upsert_lead(db, normalized, raw_place=place)
            saved_leads.append(lead)
            if is_new:
                new_count += 1
            else:
                duplicate_count += 1
        except Exception:
            # one bad record must not fail the whole batch
            failed_count += 1
            logger.exception("Failed to process a place result in run %s", run.id)

    run.status = "completed"
    run.new_leads_count = new_count
    run.duplicate_count = duplicate_count
    run.failed_count = failed_count
    run.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(run)
    for lead in saved_leads:
        db.refresh(lead)

    return run, saved_leads
