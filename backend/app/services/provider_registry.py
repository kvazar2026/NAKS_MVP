"""Registry of ``LLMProvider`` implementations (ticket 04).

Adding a vendor means adding a module and one entry in ``_FACTORIES`` below.
Nothing else — not the survey endpoint, not validation, not document
generation — knows which provider is configured; they all depend on the
``LLMProvider`` interface only.

Two deliberate departures from the earlier draft in the spec:

- **Selection is by provider name** (``NAKS_LLM_PROVIDER``), not by "whichever
  vendor's API key happens to be present". With more than one vendor,
  key-presence stops being a selection rule at all — two keys set would make
  the choice arbitrary.
- **No silent fallback to the mock.** A provider named but missing its
  credentials fails startup with a message naming the variable. The earlier
  draft fell back quietly, which in a multi-vendor setup risks an operator
  believing a real model is running while fixtures answer every request.
  Running without a vendor is still fully supported — it just has to be
  chosen, by setting ``NAKS_LLM_PROVIDER=mock`` (also the default).
"""

from collections.abc import Callable

from app.core.config import Settings
from app.services.anthropic_provider import AnthropicProvider
from app.services.llm_provider import LLMProvider
from app.services.mock_provider import MockProvider

MOCK = "mock"
ANTHROPIC = "anthropic"


def _build_mock(_settings: Settings) -> LLMProvider:
    return MockProvider()


def _build_anthropic(settings: Settings) -> LLMProvider:
    if not settings.anthropic_api_key:
        raise ValueError(
            f"LLM provider '{ANTHROPIC}' is selected but ANTHROPIC_API_KEY is not set. "
            f"Set it, or set NAKS_LLM_PROVIDER={MOCK} to run without a vendor."
        )
    return AnthropicProvider(api_key=settings.anthropic_api_key, model=settings.anthropic_model)


_FACTORIES: dict[str, Callable[[Settings], LLMProvider]] = {
    MOCK: _build_mock,
    ANTHROPIC: _build_anthropic,
}


def available_providers() -> tuple[str, ...]:
    return tuple(sorted(_FACTORIES))


def build_llm_provider(settings: Settings) -> LLMProvider:
    """Build the configured provider, or raise — never return a substitute."""

    factory = _FACTORIES.get(settings.llm_provider)
    if factory is None:
        raise ValueError(
            f"Unknown LLM provider '{settings.llm_provider}'. "
            f"Available: {', '.join(available_providers())}."
        )
    return factory(settings)
