"""FastAPI application factory.

Business endpoints (``/api/v1/survey/validate``, ``/api/v1/documents/generate``)
are not wired up yet — that is ticket 02. This ticket only exposes ``/health``
and loads the config-driven registries at startup so the loading mechanism
itself is in place and tested.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import get_settings
from app.services.ac_registry import AttestationCenterRegistry
from app.services.template_registry import TemplateRegistry


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.template_registry = TemplateRegistry.from_yaml(settings.template_registry_path)
    app.state.ac_registry = AttestationCenterRegistry.from_yaml(settings.ac_registry_path)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="NAKS Prequalification API", lifespan=lifespan)
    app.include_router(health_router)
    return app


app = create_app()
