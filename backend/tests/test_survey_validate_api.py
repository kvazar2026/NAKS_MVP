"""HTTP-contract tests for ``POST /api/v1/survey/validate`` (ticket 02).

Hits the endpoint only — no reach into ``app.services.validation`` internals
(spec, Testing Decisions: "тесты проверяют внешнее поведение... а не
внутренние детали реализации").
"""

import logging

import pytest

from app.api.dependencies import get_llm_provider
from app.schemas.llm import LLMNormalizationInput, LLMNormalizationResult
from app.services.llm_provider import LLMProvider

ENDPOINT = "/api/v1/survey/validate"


class _ExplodingLLMProvider(LLMProvider):
    """Proves a code path never reaches the ``LLMProvider`` call: if it did,
    this raises and the endpoint would surface a 500, not a clean 200 with
    blocking errors.
    """

    async def normalize(self, data: LLMNormalizationInput) -> LLMNormalizationResult:
        raise AssertionError("LLMProvider must not be called when structural validation already failed")


def test_valid_submission_succeeds(client, valid_survey_payload):
    response = client.post(ENDPOINT, json=valid_survey_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["errors"] == []
    assert body["warnings"] == []
    normalized = body["normalized_data"]
    assert normalized["organization"]["inn"] == "7701234567"
    # equipment_type/welding_method/purpose come back as the canonical label
    # MockProvider resolved the submitted synonym to, not the raw input.
    assert normalized["equipment"]["equipment_type"] == "Источник сварочного тока"
    assert normalized["equipment"]["welding_method"] == "РД — ручная дуговая сварка покрытым электродом"
    assert normalized["equipment"]["purpose"] == "Ремонт и восстановление оборудования"
    assert "consent" not in normalized


@pytest.mark.parametrize(
    "field_path",
    [
        ("organization", "company_name"),
        ("organization", "address"),
        ("contact", "full_name"),
        ("contact", "position"),
        ("region",),
        ("equipment", "brand"),
        ("equipment", "model"),
        ("equipment", "manufacturer"),
    ],
)
def test_missing_required_field_blocks_without_calling_llm(client, valid_survey_payload, field_path):
    client.app.dependency_overrides[get_llm_provider] = lambda: _ExplodingLLMProvider()

    payload = valid_survey_payload
    target = payload
    for key in field_path[:-1]:
        target = target[key]
    target[field_path[-1]] = "   "  # blank after strip()

    response = client.post(ENDPOINT, json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert body["normalized_data"] is None
    expected_field = ".".join(field_path)
    assert any(error["field"] == expected_field and error["code"] == "required" for error in body["errors"])


def test_unregistered_attestation_center_blocks(client, valid_survey_payload):
    client.app.dependency_overrides[get_llm_provider] = lambda: _ExplodingLLMProvider()
    valid_survey_payload["attestation_center_code"] = "unknown-ac"

    response = client.post(ENDPOINT, json=valid_survey_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert any(
        error["field"] == "attestation_center_code" and error["code"] == "not_in_reference_list"
        for error in body["errors"]
    )


def test_unknown_opo_group_blocks(client, valid_survey_payload):
    client.app.dependency_overrides[get_llm_provider] = lambda: _ExplodingLLMProvider()
    valid_survey_payload["opo_group"] = "Группа X — придуманная категория"

    response = client.post(ENDPOINT, json=valid_survey_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert any(
        error["field"] == "opo_group" and error["code"] == "not_in_reference_list" for error in body["errors"]
    )


@pytest.mark.parametrize("bad_inn", ["12345", "12345678901", "not-a-number"])
def test_invalid_inn_format_blocks(client, valid_survey_payload, bad_inn):
    client.app.dependency_overrides[get_llm_provider] = lambda: _ExplodingLLMProvider()
    valid_survey_payload["organization"]["inn"] = bad_inn

    response = client.post(ENDPOINT, json=valid_survey_payload)

    body = response.json()
    assert body["valid"] is False
    assert any(
        error["field"] == "organization.inn" and error["code"] == "invalid_format" for error in body["errors"]
    )


@pytest.mark.parametrize("bad_phone", ["123", "не телефон", "+1 415 555 0100"])
def test_invalid_phone_format_blocks(client, valid_survey_payload, bad_phone):
    client.app.dependency_overrides[get_llm_provider] = lambda: _ExplodingLLMProvider()
    valid_survey_payload["contact"]["phone"] = bad_phone

    response = client.post(ENDPOINT, json=valid_survey_payload)

    body = response.json()
    assert body["valid"] is False
    assert any(error["field"] == "contact.phone" and error["code"] == "invalid_format" for error in body["errors"])


def test_invalid_email_format_blocks(client, valid_survey_payload):
    client.app.dependency_overrides[get_llm_provider] = lambda: _ExplodingLLMProvider()
    valid_survey_payload["contact"]["email"] = "not-an-email"

    response = client.post(ENDPOINT, json=valid_survey_payload)

    body = response.json()
    assert body["valid"] is False
    assert any(error["field"] == "contact.email" and error["code"] == "invalid_format" for error in body["errors"])


@pytest.mark.parametrize("direction", ["materials", "welders"])
def test_unsupported_direction_blocks(client, valid_survey_payload, direction):
    client.app.dependency_overrides[get_llm_provider] = lambda: _ExplodingLLMProvider()
    valid_survey_payload["attestation_direction"] = direction

    response = client.post(ENDPOINT, json=valid_survey_payload)

    body = response.json()
    assert body["valid"] is False
    assert any(
        error["field"] == "attestation_direction" and error["code"] == "unsupported_direction"
        for error in body["errors"]
    )


def test_missing_consent_blocks(client, valid_survey_payload):
    client.app.dependency_overrides[get_llm_provider] = lambda: _ExplodingLLMProvider()
    valid_survey_payload["consent"] = False

    response = client.post(ENDPOINT, json=valid_survey_payload)

    body = response.json()
    assert body["valid"] is False
    assert any(error["field"] == "consent" and error["code"] == "consent_required" for error in body["errors"])


def test_empty_serial_numbers_blocks(client, valid_survey_payload):
    client.app.dependency_overrides[get_llm_provider] = lambda: _ExplodingLLMProvider()
    valid_survey_payload["equipment"]["serial_numbers"] = []

    response = client.post(ENDPOINT, json=valid_survey_payload)

    body = response.json()
    assert body["valid"] is False
    assert any(error["field"] == "equipment.serial_numbers" for error in body["errors"])


def test_malformed_request_structure_returns_422(client):
    response = client.post(ENDPOINT, json={"organization": {"inn": "7701234567"}})

    assert response.status_code == 422


def test_unclassifiable_welding_method_blocks_after_llm_normalization(client, valid_survey_payload):
    # Free text MockProvider cannot map to any canonical label — the LLM call
    # does happen (this is a post-normalization reference-list failure, not a
    # pre-LLM structural one), but its NEEDS_REVIEW / best-effort output is
    # still rejected rather than trusted (spec, "Недоверие к выводу LLM").
    valid_survey_payload["equipment"]["welding_method"] = "совершенно неизвестный метод XYZ123"

    response = client.post(ENDPOINT, json=valid_survey_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert body["normalized_data"] is None
    assert any(
        error["field"] == "equipment.welding_method" and error["code"] == "not_in_reference_list"
        for error in body["errors"]
    )


def test_logs_contain_no_pii(client, valid_survey_payload, caplog):
    caplog.set_level(logging.INFO, logger="naks")

    response = client.post(ENDPOINT, json=valid_survey_payload)

    assert response.status_code == 200
    log_text = "\n".join(record.getMessage() for record in caplog.records)

    for pii_value in [
        valid_survey_payload["organization"]["inn"],
        valid_survey_payload["organization"]["company_name"],
        valid_survey_payload["organization"]["address"],
        valid_survey_payload["contact"]["full_name"],
        valid_survey_payload["contact"]["phone"],
        valid_survey_payload["contact"]["email"],
    ]:
        assert pii_value not in log_text

    assert "direction=equipment" in log_text
    assert "result=success" in log_text
