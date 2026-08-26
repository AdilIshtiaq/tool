import logging

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import verify_api_key
from app.config import get_settings
from app.db import check_database_connection
from app.logging_config import configure_logging
from app.routers import analysis_rules as analysis_rules_router
from app.routers import calls as calls_router
from app.routers import campaigns as campaigns_router
from app.routers import dashboard as dashboard_router
from app.routers import leads as leads_router
from app.routers import messages as messages_router
from app.routers import outreach as outreach_router
from app.routers import qualification_rules as qualification_rules_router
from app.routers import runs as runs_router
from app.routers import search_configurations as search_configurations_router
from app.routers import services as services_router
from app.routers import settings as settings_router
from app.routers import tasks as tasks_router
from app.routers import templates as templates_router

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("nexcraft")

app = FastAPI(title="NexCraft Solutions - AI Sales Operating System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "env": settings.app_env}


@app.get("/api/health/db")
def health_db() -> dict:
    try:
        check_database_connection()
        return {"status": "ok"}
    except Exception as exc:  # surfaced to caller for visibility, not silently retried
        logger.error("Database health check failed: %s", exc)
        return {"status": "error", "detail": str(exc)}


_auth = [Depends(verify_api_key)]

app.include_router(leads_router.router, dependencies=_auth)
app.include_router(search_configurations_router.router, dependencies=_auth)
app.include_router(runs_router.router, dependencies=_auth)
app.include_router(qualification_rules_router.router, dependencies=_auth)
app.include_router(services_router.router, dependencies=_auth)
app.include_router(analysis_rules_router.router, dependencies=_auth)
app.include_router(templates_router.router, dependencies=_auth)
app.include_router(outreach_router.router, dependencies=_auth)
app.include_router(messages_router.router, dependencies=_auth)
app.include_router(calls_router.router, dependencies=_auth)
app.include_router(tasks_router.router, dependencies=_auth)
app.include_router(dashboard_router.router, dependencies=_auth)
app.include_router(settings_router.router, dependencies=_auth)
app.include_router(campaigns_router.router, dependencies=_auth)
