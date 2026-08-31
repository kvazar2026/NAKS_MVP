import copy

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    # TestClient's context manager triggers the app's lifespan (startup),
    # which is what loads the template/AC registries from YAML.
    with TestClient(create_app()) as test_client:
        yield test_client


# Single source of truth for "a submission that passes every rule": organization/
# contact fields satisfy the structural format/length rules, and equipment_type/
# welding_method/purpose are free-text synonyms MockProvider confidently maps to
# a canonical reference-list label (see app/domain/reference_data.py) so the
# normalized result also passes the post-LLM reference-list re-check.
_VALID_SURVEY_PAYLOAD = {
    "organization": {
        "inn": "7701234567",
        "company_name": 'ООО "Завод"',
        "address": "г. Москва, ул. Промышленная, д. 1",
    },
    "contact": {
        "full_name": "Иванов Иван Иванович",
        "position": "Главный сварщик",
        "phone": "+7 900 123-45-67",
        "email": "welder@example.com",
    },
    "attestation_center_code": "demo",
    "attestation_direction": "equipment",
    "opo_group": "Группа 1 — сосуды и аппараты, работающие под давлением",
    "region": "Московская область",
    "equipment": {
        "equipment_type": "источник питания",
        "brand": "ESAB",
        "model": "Origo Mig 4002i",
        "manufacturer": "ESAB AB",
        "welding_method": "РД",
        "quantity": 2,
        "serial_numbers": ["SN-001", "SN-002"],
        "purpose": "ремонт",
    },
    "consent": True,
}

# The same submission after normalization: equipment_type/welding_method/purpose
# replaced by the canonical labels MockProvider resolves the synonyms above to.
_VALID_NORMALIZED_DATA = {
    **{k: v for k, v in _VALID_SURVEY_PAYLOAD.items() if k != "consent"},
    "equipment": {
        **_VALID_SURVEY_PAYLOAD["equipment"],
        "equipment_type": "Источник сварочного тока",
        "welding_method": "РД — ручная дуговая сварка покрытым электродом",
        "purpose": "Ремонт и восстановление оборудования",
    },
}


@pytest.fixture
def valid_survey_payload() -> dict:
    """A fresh deep copy — safe for a test to mutate without affecting others."""

    return copy.deepcopy(_VALID_SURVEY_PAYLOAD)


@pytest.fixture
def valid_normalized_data() -> dict:
    return copy.deepcopy(_VALID_NORMALIZED_DATA)


@pytest.fixture
def valid_document_generate_payload(valid_normalized_data: dict) -> dict:
    return {
        "normalized_data": valid_normalized_data,
        "attestation_direction": valid_normalized_data["attestation_direction"],
        "attestation_center_code": valid_normalized_data["attestation_center_code"],
    }
