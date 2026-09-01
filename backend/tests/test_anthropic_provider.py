"""``AnthropicProvider`` behaviour that must hold without a real API key.

The vendor SDK is replaced by a stub at the client boundary, so these exercise
the provider's own code — prompt construction, schema strictness, error
translation — rather than the network. The contract suite in
``test_llm_provider_contract.py`` covers the real-key run.
"""

import asyncio
from types import SimpleNamespace

import anthropic
import pytest
from pydantic import ValidationError

from app.schemas.llm import LLMNormalizationInput, NormalizationStatus
from app.services.anthropic_provider import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    AnthropicProvider,
)
from app.services.llm_provider import LLMProviderError

WELL_FORMED = {
    "fields": [
        {"field": "equipment_type", "normalized_value": "Источник сварочного тока", "status": "normalized"},
        {"field": "welding_method", "normalized_value": "РД — ручная дуговая сварка покрытым электродом", "status": "normalized"},
        {"field": "purpose", "normalized_value": "Ремонт и восстановление оборудования", "status": "needs_review"},
    ],
    "ambiguities": [{"field": "purpose", "description": "Не удалось сопоставить однозначно"}],
}


class _StubMessages:
    def __init__(self, outcome) -> None:
        self.outcome = outcome
        self.calls: list[dict] = []

    async def parse(self, **kwargs):
        self.calls.append(kwargs)
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return SimpleNamespace(parsed_output=self.outcome)


class _StubClient:
    def __init__(self, outcome) -> None:
        self.messages = _StubMessages(outcome)


def _provider(outcome) -> tuple[AnthropicProvider, _StubClient]:
    client = _StubClient(outcome)
    return AnthropicProvider(api_key="test-key", model="claude-sonnet-5", client=client), client


@pytest.fixture
def sample_input() -> LLMNormalizationInput:
    return LLMNormalizationInput(
        equipment_type="источник питания",
        welding_method="рд",
        purpose="ремонт",
    )


def test_maps_a_well_formed_response_onto_the_shared_contract(sample_input):
    provider, _ = _provider(WELL_FORMED)

    result = asyncio.run(provider.normalize(sample_input))

    assert {field.field for field in result.fields} == {"equipment_type", "welding_method", "purpose"}
    statuses = {field.field: field.status for field in result.fields}
    assert statuses["equipment_type"] == NormalizationStatus.NORMALIZED
    assert statuses["purpose"] == NormalizationStatus.NEEDS_REVIEW
    assert result.ambiguities[0].field == "purpose"


def test_request_carries_only_the_classified_values_and_no_pii(sample_input, valid_survey_payload):
    """The outgoing request must never contain INN, address, contact name,
    phone or email — checked against the values from a full survey submission,
    the ones that exist in the app but must not reach a vendor.
    """

    provider, client = _provider(WELL_FORMED)

    asyncio.run(provider.normalize(sample_input))

    sent = str(client.messages.calls[0])
    organization = valid_survey_payload["organization"]
    contact = valid_survey_payload["contact"]
    for pii_value in [
        organization["inn"],
        organization["company_name"],
        organization["address"],
        contact["full_name"],
        contact["phone"],
        contact["email"],
    ]:
        assert pii_value not in sent

    # The three values it is allowed to send are all present.
    for allowed in [sample_input.equipment_type, sample_input.welding_method, sample_input.purpose]:
        assert allowed in sent


def test_request_omits_temperature_and_asks_for_the_strict_schema(sample_input):
    provider, client = _provider(WELL_FORMED)

    asyncio.run(provider.normalize(sample_input))

    call = client.messages.calls[0]
    assert "temperature" not in call  # rejected on this model generation
    assert call["model"] == "claude-sonnet-5"
    assert call["output_format"] is not None


@pytest.mark.parametrize(
    "malformed",
    [
        pytest.param({"fields": [{"field": "equipment_type", "normalized_value": "x", "status": "normalized"}]}, id="missing-fields"),
        pytest.param(
            {"fields": [{"field": "steel_grade", "normalized_value": "x", "status": "normalized"}]},
            id="unknown-field-name",
        ),
        pytest.param(
            {"fields": [{"field": "equipment_type", "normalized_value": "x", "status": "invented-status"}]},
            id="unknown-status",
        ),
        pytest.param({"fields": "not-a-list"}, id="wrong-type"),
        pytest.param({}, id="empty"),
    ],
)
def test_malformed_response_is_rejected_rather_than_coerced(sample_input, malformed):
    provider, _ = _provider(malformed)

    with pytest.raises(LLMProviderError):
        asyncio.run(provider.normalize(sample_input))


def test_missing_structured_output_is_an_error(sample_input):
    provider, _ = _provider(None)

    with pytest.raises(LLMProviderError):
        asyncio.run(provider.normalize(sample_input))


def test_vendor_exception_is_translated_so_it_never_escapes_as_a_vendor_type(sample_input):
    provider, _ = _provider(anthropic.APIConnectionError(request=None))

    with pytest.raises(LLMProviderError):
        asyncio.run(provider.normalize(sample_input))


def test_sdk_side_json_validation_failure_is_translated_too(sample_input):
    """`messages.parse` validates the model's JSON inside the SDK and raises a
    pydantic ValidationError, which is NOT an AnthropicError — the realistic
    trigger being a `max_tokens`-truncated answer. Without its own branch it
    escapes past the "no vendor-layer exception reaches the caller" guarantee.
    """

    truncated = ValidationError.from_exception_data("_ProviderResponse", [])
    provider, _ = _provider(truncated)

    with pytest.raises(LLMProviderError):
        asyncio.run(provider.normalize(sample_input))


def test_client_is_built_with_a_bounded_timeout_and_retry_budget():
    """SDK defaults (600s read, 2 retries) would let a stalled vendor
    connection hold one user-facing /survey/validate request open for about
    half an hour.
    """

    provider = AnthropicProvider(api_key="test-key", model="claude-sonnet-5")

    assert provider._client.timeout == DEFAULT_TIMEOUT_SECONDS
    assert provider._client.max_retries == DEFAULT_MAX_RETRIES
    assert DEFAULT_TIMEOUT_SECONDS <= 60


def test_prompt_lists_the_canonical_reference_labels(sample_input):
    """The model is asked to classify into the same labels the backend
    re-checks against — if the prompt drifted from the reference lists, every
    real answer would fail the post-LLM check.
    """

    provider, client = _provider(WELL_FORMED)

    asyncio.run(provider.normalize(sample_input))

    system = client.messages.calls[0]["system"]
    assert "Источник сварочного тока" in system
    assert "РД — ручная дуговая сварка покрытым электродом" in system
    assert "Ремонт и восстановление оборудования" in system
