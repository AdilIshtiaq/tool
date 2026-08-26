from fastapi import APIRouter

from app.config import get_settings
from app.schemas import SettingsOut, SettingsUpdate
from app.services.env_file import update_env_file

router = APIRouter(prefix="/api/settings", tags=["settings"])

# Maps schema field names to their backend/.env variable names.
_ENV_KEYS = {
    "google_places_api_key": "GOOGLE_PLACES_API_KEY",
    "openai_api_key": "OPENAI_API_KEY",
    "anthropic_api_key": "ANTHROPIC_API_KEY",
    "gemini_api_key": "GEMINI_API_KEY",
    "smtp_host": "SMTP_HOST",
    "smtp_port": "SMTP_PORT",
    "smtp_user": "SMTP_USER",
    "smtp_password": "SMTP_PASSWORD",
    "smtp_from_name": "SMTP_FROM_NAME",
    "imap_host": "IMAP_HOST",
    "imap_port": "IMAP_PORT",
}


@router.get("", response_model=SettingsOut)
def get_settings_view():
    settings = get_settings()
    return SettingsOut(
        google_places_api_key_set=bool(settings.google_places_api_key),
        openai_api_key_set=bool(settings.openai_api_key),
        anthropic_api_key_set=bool(settings.anthropic_api_key),
        gemini_api_key_set=bool(settings.gemini_api_key),
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_user=settings.smtp_user,
        smtp_password_set=bool(settings.smtp_password),
        smtp_from_name=settings.smtp_from_name,
        imap_host=settings.imap_host,
        imap_port=settings.imap_port,
    )


@router.patch("", response_model=SettingsOut)
def update_settings_view(payload: SettingsUpdate):
    changes = payload.model_dump(exclude_none=True)
    if changes:
        update_env_file({_ENV_KEYS[field]: str(value) for field, value in changes.items()})
        get_settings.cache_clear()
    return get_settings_view()
