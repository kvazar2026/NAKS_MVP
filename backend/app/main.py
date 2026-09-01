"""FastAPI application factory.

Wires up the two business endpoints (``/api/v1/survey/validate``,
``/api/v1/documents/generate``): config-driven registries, the ``LLMProvider``
chosen by name from the provider registry (ticket 04), structured PII-free
logging, and a generic-message handler for unhandled errors (User Story 18).

Everything here loads at startup and fails loudly if it cannot: a malformed
registry file or a provider without credentials stops the app rather than
surfacing as a broken request later.
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
from app.services.provider_registry import build_llm_provider
from app.services.template_registry import TemplateRegistry
from app.services.warning_rules import WarningRulesRegistry


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()
    app.state.template_registry = TemplateRegistry.from_yaml(settings.template_registry_path)
    app.state.ac_registry = AttestationCenterRegistry.from_yaml(settings.ac_registry_path)
    app.state.warning_rules = WarningRulesRegistry.from_yaml(settings.warning_rules_path)
    app.state.llm_provider = build_llm_provider(settings)
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
