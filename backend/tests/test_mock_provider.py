"""``MockProvider``-specific normalization behavior (beyond the shared
``LLMProvider`` shape contract already covered in
``test_llm_provider_contract.py``).
"""

import asyncio

from app.schemas.llm import LLMNormalizationInput, NormalizationStatus
from app.services.mock_provider import MockProvider


def _normalize(**overrides):
    data = LLMNormalizationInput(
        equipment_type=overrides.get("equipment_type", "источник питания"),
        welding_method=overrides.get("welding_method", "РД"),
        purpose=overrides.get("purpose", "ремонт"),
    )
    return asyncio.run(MockProvider().normalize(data))


def test_known_synonym_normalizes_to_the_canonical_label():
    result = _normalize(equipment_type="источник питания")

    field = next(f for f in result.fields if f.field == "equipment_type")
    assert field.normalized_value == "Источник сварочного тока"
    assert field.status == NormalizationStatus.NORMALIZED


def test_matching_is_case_and_whitespace_insensitive():
    result = _normalize(welding_method="   рд  ")

    field = next(f for f in result.fields if f.field == "welding_method")
    assert field.normalized_value == "РД — ручная дуговая сварка покрытым электродом"
    assert field.status == NormalizationStatus.NORMALIZED


def test_already_canonical_label_matches_itself():
    canonical = "АДС — автоматическая дуговая сварка под флюсом"
    result = _normalize(welding_method=canonical)

    field = next(f for f in result.fields if f.field == "welding_method")
    assert field.normalized_value == canonical
    assert field.status == NormalizationStatus.NORMALIZED


def test_unrecognized_value_is_flagged_needs_review_with_an_ambiguity():
    result = _normalize(purpose="полностью выдуманное назначение XYZ")

    field = next(f for f in result.fields if f.field == "purpose")
    assert field.status == NormalizationStatus.NEEDS_REVIEW
    assert field.normalized_value == "полностью выдуманное назначение XYZ"
    assert any(a.field == "purpose" for a in result.ambiguities)


def test_result_covers_exactly_the_three_classification_relevant_fields():
    result = _normalize()

    assert {f.field for f in result.fields} == {"equipment_type", "welding_method", "purpose"}
