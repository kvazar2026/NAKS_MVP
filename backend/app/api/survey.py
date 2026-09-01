"""``POST /api/v1/survey/validate`` (spec, Backend section; ticket 02).

Structural rules run first and block on any failure *before* touching the
``LLMProvider`` (proven in ``tests/test_survey_validate_api.py`` by making a
failing provider dependency and asserting the request still succeeds
cleanly). Only on structural success are the three classification-relevant
fields sent to the provider — never INN/address/full name/phone/email (spec,
"Минимизация данных"; enforced structurally by ``LLMNormalizationInput``).
"""

import time

from fastapi import APIRouter, Depends

from app.api.dependencies import get_ac_registry, get_llm_provider, get_warning_rules
from app.core.logging import log_outcome
from app.schemas.llm import LLMFieldResult, LLMNormalizationInput
from app.schemas.survey import NormalizedSurveyData, SurveyValidateRequest, SurveyValidateResponse, ValidationIssue
from app.services.ac_registry import AttestationCenterRegistry
from app.services.llm_provider import LLMProvider
from app.services.validation import validate_classified_fields, validate_common_structural
from app.services.warning_rules import WarningRulesRegistry

router = APIRouter()

_ENDPOINT = "/api/v1/survey/validate"


def _field_value(fields: list[LLMFieldResult], field_name: str, fallback: str) -> str:
    for result in fields:
        if result.field == field_name:
            return result.normalized_value
    return fallback  # defensive only: a conforming LLMProvider always returns all three fields


@router.post("/api/v1/survey/validate", response_model=SurveyValidateResponse)
async def validate_survey(
    request: SurveyValidateRequest,
    ac_registry: AttestationCenterRegistry = Depends(get_ac_registry),
    llm_provider: LLMProvider = Depends(get_llm_provider),
    warning_rules: WarningRulesRegistry = Depends(get_warning_rules),
) -> SurveyValidateResponse:
    started_at = time.perf_counter()
    direction = request.attestation_direction.value

    errors: list[ValidationIssue] = validate_common_structural(request, ac_registry)
    if not request.consent:
        errors.append(
            ValidationIssue(
                field="consent",
                code="consent_required",
                message="Необходимо согласие на обработку данных (демонстрационный режим)",
            )
        )

    if errors:
        _log(started_at, direction, "blocked", errors)
        return SurveyValidateResponse(valid=False, errors=errors)

    llm_result = await llm_provider.normalize(
        LLMNormalizationInput(
            equipment_type=request.equipment.equipment_type,
            welding_method=request.equipment.welding_method,
            purpose=request.equipment.purpose,
        )
    )
    normalized_equipment_type = _field_value(llm_result.fields, "equipment_type", request.equipment.equipment_type)
    normalized_welding_method = _field_value(llm_result.fields, "welding_method", request.equipment.welding_method)
    normalized_purpose = _field_value(llm_result.fields, "purpose", request.equipment.purpose)

    # Insurance against the LLM's own verdict (spec, "Недоверие к выводу
    # LLM"): re-checked against the same reference lists regardless of the
    # per-field NORMALIZED/NEEDS_REVIEW status the provider returned.
    classified_errors = validate_classified_fields(normalized_equipment_type, normalized_welding_method, normalized_purpose)
    if classified_errors:
        _log(started_at, direction, "blocked", classified_errors)
        return SurveyValidateResponse(valid=False, errors=classified_errors)

    normalized_data = NormalizedSurveyData(
        organization=request.organization,
        contact=request.contact,
        attestation_center_code=request.attestation_center_code,
        attestation_direction=request.attestation_direction,
        opo_group=request.opo_group,
        region=request.region,
        equipment=request.equipment.model_copy(
            update={
                "equipment_type": normalized_equipment_type,
                "welding_method": normalized_welding_method,
                "purpose": normalized_purpose,
            }
        ),
    )
    # Checklist hints run last, on normalized data: they compare against the
    # canonical reference-list labels, which only exist after normalization
    # (ticket 03). They never block — a matched rule still returns valid=True
    # and the document still generates (ADR 0004).
    warnings = warning_rules.evaluate(normalized_data)

    _log(started_at, direction, "success", [])
    return SurveyValidateResponse(valid=True, normalized_data=normalized_data, warnings=warnings)


def _log(started_at: float, direction: str, result: str, errors: list[ValidationIssue]) -> None:
    duration_ms = (time.perf_counter() - started_at) * 1000
    error_code = ",".join(sorted({issue.code for issue in errors})) or None
    log_outcome(endpoint=_ENDPOINT, direction=direction, result=result, duration_ms=duration_ms, error_code=error_code)
