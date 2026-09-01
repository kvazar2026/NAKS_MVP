"""Provider selection is explicit and fail-fast (ticket 04)."""

import pytest

from app.core.config import Settings
from app.services.anthropic_provider import AnthropicProvider
from app.services.mock_provider import MockProvider
from app.services.provider_registry import available_providers, build_llm_provider


def _settings(**overrides) -> Settings:
    # _env_file=None keeps a developer's real .env out of these assertions.
    return Settings(_env_file=None, **overrides)


def test_default_provider_is_the_mock():
    assert _settings().llm_provider == "mock"
    assert isinstance(build_llm_provider(_settings()), MockProvider)


def test_registry_lists_its_providers():
    assert set(available_providers()) == {"mock", "anthropic"}


def test_anthropic_is_built_when_its_credentials_are_present():
    provider = build_llm_provider(_settings(llm_provider="anthropic", anthropic_api_key="test-key"))

    assert isinstance(provider, AnthropicProvider)


def test_unknown_provider_name_fails_instead_of_falling_back():
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        build_llm_provider(_settings(llm_provider="gpt-9000"))


def test_error_for_an_unknown_name_lists_the_available_ones():
    with pytest.raises(ValueError, match="anthropic"):
        build_llm_provider(_settings(llm_provider="gpt-9000"))


def test_real_provider_without_credentials_fails_instead_of_using_the_mock():
    """The silent fallback the spec originally described is deliberately gone:
    an operator who asked for a vendor must not get fixtures instead and
    believe a model answered.
    """

    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        build_llm_provider(_settings(llm_provider="anthropic", anthropic_api_key=None))


def test_credential_failure_message_names_the_way_out():
    with pytest.raises(ValueError, match="NAKS_LLM_PROVIDER=mock"):
        build_llm_provider(_settings(llm_provider="anthropic", anthropic_api_key=None))
