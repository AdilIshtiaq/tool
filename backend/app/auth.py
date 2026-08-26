from fastapi import Depends, Header, HTTPException, status

from app.config import Settings, get_settings


def verify_api_key(
    x_api_key: str = Header(default=""),
    settings: Settings = Depends(get_settings),
) -> None:
    """Require X-API-Key to match settings.api_key.

    Auth is skipped when api_key is unset, so local dev without a .env
    entry keeps working; set API_KEY before exposing the API beyond localhost.
    """
    if not settings.api_key:
        return
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
