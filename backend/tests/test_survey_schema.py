"""Confirms the request/response schemas actually cover the full field set
from the spec's user stories — this doubles as executable documentation of
the contract this ticket is required to produce.
"""

from app.schemas.common import AttestationDirection
from app.schemas.documents import DocumentGenerateErrorResponse, DocumentGenerateRequest
from app.schemas.survey import (
    NormalizedSurveyData,
    SurveyValidateRequest,
    SurveyValidateResponse,
    ValidationIssue,
    ValidationWarning,
    WarningVerificationStatus,
)

VALID_EQUIPMENT_SURVEY_PAYLOAD = {
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
    "opo_group": "Б1",
    "region": "Московская область",
    "equipment": {
        "equipment_type": "Источник питания",
        "brand": "ESAB",
        "model": "Origo Mig 4002i",
        "manufacturer": "ESAB AB",
        "welding_method": "МП (МИГ/МАГ)",
        "quantity": 2,
        "serial_numbers": ["SN-001", "SN-002"],
        "purpose": "Сварка трубопроводов",
    },
    "consent": True,
}


def test_survey_validate_request_covers_the_full_equipment_field_set():
    request = SurveyValidateRequest(**VALID_EQUIPMENT_SURVEY_PAYLOAD)

    assert request.organization.inn == "7701234567"
    assert request.contact.email == "welder@example.com"
    assert request.attestation_direction == AttestationDirection.EQUIPMENT
    assert request.equipment.serial_numbers == ["SN-001", "SN-002"]
    assert request.consent is True


def test_normalized_survey_data_excludes_consent_but_keeps_application_fields():
    payload = {k: v for k, v in VALID_EQUIPMENT_SURVEY_PAYLOAD.items() if k != "consent"}

    normalized = NormalizedSurveyData(**payload)

    assert not hasattr(normalized, "consent")
    assert normalized.equipment.equipment_type == "Источник питания"


def test_survey_validate_response_success_shape():
    normalized = NormalizedSurveyData(
        **{k: v for k, v in VALID_EQUIPMENT_SURVEY_PAYLOAD.items() if k != "consent"}
    )

    response = SurveyValidateResponse(valid=True, normalized_data=normalized)

    assert response.errors == []
    assert response.warnings == []


def test_survey_validate_response_error_and_warning_shapes():
    response = SurveyValidateResponse(
        valid=False,
        errors=[ValidationIssue(field="organization.inn", code="required", message="ИНН обязателен")],
        warnings=[
            ValidationWarning(
                field="equipment.welding_method",
                code="checklist.method-vs-opo-mismatch",
                message="Способ сварки обычно не применяется для этой группы ОПО",
                explanation="По данным типовых ошибок заявок НАКС...",
                source="naks-checklist-monetization.md",
                verification_status=WarningVerificationStatus.NOT_VERIFIED_BY_EXPERT,
            )
        ],
    )

    assert response.normalized_data is None
    assert response.errors[0].code == "required"
    assert response.warnings[0].verification_status == WarningVerificationStatus.NOT_VERIFIED_BY_EXPERT


def test_document_generate_request_and_error_response_shapes():
    normalized = NormalizedSurveyData(
        **{k: v for k, v in VALID_EQUIPMENT_SURVEY_PAYLOAD.items() if k != "consent"}
    )

    request = DocumentGenerateRequest(
        normalized_data=normalized,
        attestation_direction=AttestationDirection.EQUIPMENT,
        attestation_center_code="demo",
    )
    error_response = DocumentGenerateErrorResponse(
        detail="Структурная проверка не пройдена",
        errors=[ValidationIssue(field="equipment.quantity", code="required", message="Укажите количество")],
    )

    assert request.attestation_center_code == "demo"
    assert error_response.errors[0].field == "equipment.quantity"
