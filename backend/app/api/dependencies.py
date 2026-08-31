"""Shared ``Depends()`` accessors for state loaded once at startup
(``app/main.py``'s ``lifespan``), so route modules don't each repeat
``request.app.state.xxx`` and tests can override a single dependency to swap
in a test double (see ``tests/test_survey_validate_api.py``).
"""

from fastapi import Request

from app.services.ac_registry import AttestationCenterRegistry
from app.services.llm_provider import LLMProvider
from app.services.template_registry import TemplateRegistry


def get_ac_registry(request: Request) -> AttestationCenterRegistry:
    return request.app.state.ac_registry


def get_template_registry(request: Request) -> TemplateRegistry:
    return request.app.state.template_registry


def get_llm_provider(request: Request) -> LLMProvider:
    return request.app.state.llm_provider
