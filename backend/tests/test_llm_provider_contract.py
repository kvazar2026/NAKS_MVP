"""The shared ``LLMProvider`` contract suite (spec, Testing Decisions).

Every provider in ``_PROVIDER_FACTORIES`` runs the same assertions. Adding a
vendor means adding one entry here — plus its credential variable in
``_REQUIRED_ENV`` if it needs one — not writing a new suite.

Runs that reach a real vendor need **two** things: the credentials, and
``NAKS_RUN_LIVE_LLM_TESTS=1``. Credentials alone are not enough on purpose —
a developer with a key exported for ordinary work would otherwise have a
plain ``pytest`` spend money and depend on the network, and these assertions
are about the contract, not about a vendor being reachable today. Anything
missing means skip, never fail.
"""

import asyncio
import os

import pytest

from app.schemas.llm import (
    LLMFieldResult,
    LLMNormalizationInput,
    LLMNormalizationResult,
    NormalizationStatus,
)
from app.services.anthropic_provider import AnthropicProvider
from app.services.llm_provider import LLMProvider
from app.services.mock_provider import MockProvider

CLASSIFIED_FIELDS = {"equipment_type", "welding_method", "purpose"}

_PROVIDER_FACTORIES = {
    "mock": lambda: MockProvider(),
    "anthropic": lambda: AnthropicProvider(
        api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        model=os.environ.get("NAKS_ANTHROPIC_MODEL", "claude-sonnet-5"),
    ),
}

# Providers that reach a vendor over the network, and the credential that has
# to be present for their run to be meaningful.
_REQUIRED_ENV = {"anthropic": "ANTHROPIC_API_KEY"}

# Explicit opt-in for every live vendor run, on top of the credential.
LIVE_RUN_ENV = "NAKS_RUN_LIVE_LLM_TESTS"


@pytest.fixture(params=sorted(_PROVIDER_FACTORIES))
def provider(request) -> LLMProvider:
    name = request.param
    required = _REQUIRED_ENV.get(name)
    if required:
        if os.environ.get(LIVE_RUN_ENV) != "1":
            pytest.skip(f"set {LIVE_RUN_ENV}=1 to run the live '{name}' provider contract tests")
        if not os.environ.get(required):
            pytest.skip(f"{required} is not set — skipping the live '{name}' provider contract run")
    return _PROVIDER_FACTORIES[name]()


@pytest.fixture
def sample_input() -> LLMNormalizationInput:
    return LLMNormalizationInput(
        equipment_type=" Источник питания ",
        welding_method="РД",
        purpose="Ремонт трубопроводов",
    )


# --- the contract every provider must satisfy --------------------------------


def test_provider_returns_the_shared_result_shape(provider, sample_input):
    result = asyncio.run(provider.normalize(sample_input))

    assert isinstance(result, LLMNormalizationResult)


def test_provider_classifies_exactly_the_three_fields(provider, sample_input):
    result = asyncio.run(provider.normalize(sample_input))

    assert {field.field for field in result.fields} == CLASSIFIED_FIELDS


def test_provider_returns_a_known_status_and_a_non_empty_value_per_field(provider, sample_input):
    result = asyncio.run(provider.normalize(sample_input))

    for field in result.fields:
        assert isinstance(field.status, NormalizationStatus)
        assert field.normalized_value.strip()


def test_provider_ambiguities_only_reference_classified_fields(provider, sample_input):
    result = asyncio.run(provider.normalize(sample_input))

    for ambiguity in result.ambiguities:
        assert ambiguity.field in CLASSIFIED_FIELDS


# --- properties of the contract itself ---------------------------------------


def test_llm_provider_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        LLMProvider()  # type: ignore[abstract]


class _DummyProvider(LLMProvider):
    """Smallest possible conforming implementation, used only to prove the
    abstract contract is satisfiable and enforces the right shape.
    """

    async def normalize(self, data: LLMNormalizationInput) -> LLMNormalizationResult:
        return LLMNormalizationResult(
            fields=[
                LLMFieldResult(
                    field="equipment_type",
                    normalized_value=data.equipment_type.strip().lower(),
                    status=NormalizationStatus.NORMALIZED,
                )
            ],
            ambiguities=[],
        )


def test_conforming_provider_returns_the_shared_result_shape():
    provider = _DummyProvider()
    data = LLMNormalizationInput(
        equipment_type=" Источник питания ",
        welding_method="РД",
        purpose="Ремонт трубопроводов",
    )

    result = asyncio.run(provider.normalize(data))

    assert isinstance(result, LLMNormalizationResult)
    assert result.fields[0].status == NormalizationStatus.NORMALIZED
    assert result.fields[0].normalized_value == "источник питания"


def test_llm_normalization_input_never_carries_pii_fields():
    """Data minimization is structural, not a matter of caller discipline: the
    input contract has nowhere to put PII, for any provider.
    """

    pii_fields = {"inn", "address", "full_name", "phone", "email"}
    schema_fields = set(LLMNormalizationInput.model_fields)

    assert schema_fields.isdisjoint(pii_fields)
    assert schema_fields == CLASSIFIED_FIELDS
