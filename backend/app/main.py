"""FastAPI application factory.

Ticket 02 wires up the two business endpoints
(``/api/v1/survey/validate``, ``/api/v1/documents/generate``) on top of the
ticket 01 scaffold: config-driven registries, ``MockProvider`` as the
``LLMProvider`` (real provider selection based on ``ANTHROPIC_API_KEY`` is
ticket 04 — this ticket always uses ``MockProvider``), structured PII-free
logging, and a generic-message handler for unhandled errors (User Story 18).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.claude_monitor import router as claude_monitor_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.survey import router as survey_router
from app.core.config import get_settings
from app.core.logging import configure_logging, log_outcome
from app.services.ac_registry import AttestationCenterRegistry
from app.services.mock_provider import MockProvider
from app.services.template_registry import TemplateRegistry


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()
    app.state.template_registry = TemplateRegistry.from_yaml(settings.template_registry_path)
    app.state.ac_registry = AttestationCenterRegistry.from_yaml(settings.ac_registry_path)
    app.state.llm_provider = MockProvider()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="NAKS Prequalification API", lifespan=lifespan)
    app.include_router(health_router)
    app.include_router(claude_monitor_router)
    app.include_router(survey_router)
    app.include_router(documents_router)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, _exc: Exception) -> JSONResponse:
        # Safe, generic, non-technical message only (User Story 18) — no
        # stack trace or exception detail ever reaches the client.
        log_outcome(endpoint=request.url.path, direction="-", result="error", duration_ms=0.0, error_code="internal_error")
        return JSONResponse(
            status_code=500,
            content={"detail": "Сервис временно недоступен. Попробуйте повторить запрос позже."},
        )

    return app


app = create_app()
