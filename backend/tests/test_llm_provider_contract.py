import asyncio

import pytest

from app.schemas.llm import (
    LLMFieldResult,
    LLMNormalizationInput,
    LLMNormalizationResult,
    NormalizationStatus,
)
from app.services.llm_provider import LLMProvider


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
    pii_fields = {"inn", "address", "full_name", "phone", "email"}
    schema_fields = set(LLMNormalizationInput.model_fields)

    assert schema_fields.isdisjoint(pii_fields)
