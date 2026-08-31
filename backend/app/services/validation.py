"""Deterministic structural (``error``-level) validation rules.

This is the shared module the spec requires both endpoints to use:
``/survey/validate`` calls it before ever touching an ``LLMProvider``, and
``/documents/generate`` independently re-runs the exact same checks instead
of trusting the client's claim that the data was already validated (spec,
"Не доверяет клиенту"; ticket 02).

Only ``error``-level rules live here: required fields, INN/phone/email
format, length limits, and reference-list membership (ADR 0004). Checklist-
derived ``warning`` rules are a separate registry, added in ticket 03 — do
not add non-blocking checks to this module.

``validate_common_structural`` covers every field except the three
classification-relevant ones (``equipment_type``, ``welding_method``,
``purpose``): those are free text until an ``LLMProvider`` normalizes them
(User Story 14), so checking them against a reference list only makes sense
*after* normalization — that is ``validate_classified_fields``.
``validate_full`` runs both passes in one call, which is what
``/documents/generate`` needs since it never calls an ``LLMProvider``.
"""

import re

from app.domain.reference_data import EQUIPMENT_TYPES, OPO_GROUPS, PURPOSES, WELDING_METHODS, labels
from app.schemas.common import AttestationDirection
from app.schemas.survey import SurveyData, ValidationIssue
from app.services.ac_registry import AttestationCenterRegistry

_INN_PATTERN = re.compile(r"^(\d{10}|\d{12})$")
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_DIGITS_PATTERN = re.compile(r"^[78]\d{10}$")

# MVP defaults, not researched limits — generous enough to never bother a
# real applicant, tight enough to keep the demo away from pathological input.
_MAX_LENGTHS: dict[str, int] = {
    "organization.company_name": 300,
    "organization.address": 500,
    "contact.full_name": 200,
    "contact.position": 200,
    "region": 200,
    "equipment.equipment_type": 200,
    "equipment.brand": 200,
    "equipment.model": 200,
    "equipment.manufacturer": 200,
    "equipment.welding_method": 200,
    "equipment.purpose": 300,
    "equipment.serial_number_item": 100,
}
_MAX_SERIAL_NUMBERS = 500


def _issue(field: str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(field=field, code=code, message=message)


def _check_required(value: str, field: str, errors: list[ValidationIssue]) -> bool:
    """Append a ``required`` issue for a blank ``value``. Returns whether the
    caller may proceed with further checks (format/length) on this field.
    """

    if not value or not value.strip():
        errors.append(_issue(field, "required", f"Поле «{field}» обязательно для заполнения"))
        return False
    return True


def _check_max_length(value: str, field: str, errors: list[ValidationIssue]) -> None:
    max_len = _MAX_LENGTHS[field]
    if len(value) > max_len:
        errors.append(
            _issue(field, "too_long", f"Поле «{field}» превышает допустимую длину ({max_len} символов)")
        )


def _check_required_and_length(value: str, field: str, errors: list[ValidationIssue]) -> None:
    if _check_required(value, field, errors):
        _check_max_length(value, field, errors)


def _check_in_reference_list(
    value: str, field: str, allowed: frozenset[str], errors: list[ValidationIssue]
) -> None:
    if value not in allowed:
        errors.append(
            _issue(field, "not_in_reference_list", f"Значение поля «{field}» не найдено в справочнике допустимых значений")
        )


def _is_valid_inn(inn: str) -> bool:
    return bool(_INN_PATTERN.match(inn.strip()))


def _is_valid_email(email: str) -> bool:
    return bool(_EMAIL_PATTERN.match(email.strip()))


def _is_valid_ru_phone(phone: str) -> bool:
    digits = re.sub(r"\D", "", phone)
    return bool(_PHONE_DIGITS_PATTERN.match(digits))


def validate_common_structural(
    data: SurveyData, ac_registry: AttestationCenterRegistry
) -> list[ValidationIssue]:
    """Every blocking rule except reference-list membership for the three
    LLM-classified equipment fields (see module docstring).
    """

    errors: list[ValidationIssue] = []

    org = data.organization
    if _check_required(org.inn, "organization.inn", errors) and not _is_valid_inn(org.inn):
        errors.append(_issue("organization.inn", "invalid_format", "ИНН должен состоять из 10 или 12 цифр"))
    _check_required_and_length(org.company_name, "organization.company_name", errors)
    _check_required_and_length(org.address, "organization.address", errors)

    contact = data.contact
    _check_required_and_length(contact.full_name, "contact.full_name", errors)
    _check_required_and_length(contact.position, "contact.position", errors)
    if _check_required(contact.phone, "contact.phone", errors) and not _is_valid_ru_phone(contact.phone):
        errors.append(
            _issue("contact.phone", "invalid_format", "Телефон должен быть в формате +7XXXXXXXXXX или 8XXXXXXXXXX")
        )
    if _check_required(contact.email, "contact.email", errors) and not _is_valid_email(contact.email):
        errors.append(_issue("contact.email", "invalid_format", "Некорректный формат email"))

    if _check_required(data.attestation_center_code, "attestation_center_code", errors):
        if ac_registry.get(data.attestation_center_code) is None:
            errors.append(
                _issue(
                    "attestation_center_code",
                    "not_in_reference_list",
                    "Указанный аттестационный центр не найден",
                )
            )

    if data.attestation_direction != AttestationDirection.EQUIPMENT:
        errors.append(
            _issue(
                "attestation_direction",
                "unsupported_direction",
                "В MVP доступно только направление «оборудование»",
            )
        )

    if _check_required(data.opo_group, "opo_group", errors):
        _check_in_reference_list(data.opo_group, "opo_group", labels(OPO_GROUPS), errors)

    _check_required_and_length(data.region, "region", errors)

    eq = data.equipment
    _check_required_and_length(eq.equipment_type, "equipment.equipment_type", errors)
    _check_required_and_length(eq.brand, "equipment.brand", errors)
    _check_required_and_length(eq.model, "equipment.model", errors)
    _check_required_and_length(eq.manufacturer, "equipment.manufacturer", errors)
    _check_required_and_length(eq.welding_method, "equipment.welding_method", errors)

    if eq.quantity < 1:
        errors.append(_issue("equipment.quantity", "invalid_value", "Количество должно быть не менее 1"))

    if not eq.serial_numbers:
        errors.append(
            _issue("equipment.serial_numbers", "required", "Укажите хотя бы один заводской номер")
        )
    elif len(eq.serial_numbers) > _MAX_SERIAL_NUMBERS:
        errors.append(
            _issue(
                "equipment.serial_numbers",
                "too_long",
                f"Список заводских номеров превышает допустимую длину ({_MAX_SERIAL_NUMBERS})",
            )
        )
    else:
        for index, serial in enumerate(eq.serial_numbers):
            field = f"equipment.serial_numbers[{index}]"
            if not serial or not serial.strip():
                errors.append(_issue(field, "required", "Заводской номер не может быть пустым"))
            elif len(serial) > _MAX_LENGTHS["equipment.serial_number_item"]:
                errors.append(
                    _issue(
                        field,
                        "too_long",
                        f"Заводской номер превышает допустимую длину ({_MAX_LENGTHS['equipment.serial_number_item']})",
                    )
                )

    _check_required_and_length(eq.purpose, "equipment.purpose", errors)

    return errors


def validate_classified_fields(equipment_type: str, welding_method: str, purpose: str) -> list[ValidationIssue]:
    """Reference-list membership for the fields an ``LLMProvider`` classifies.

    Called only *after* normalization — never trusts the LLM's "normalized"
    status by itself (spec, "Недоверие к выводу LLM"): every value is
    independently re-checked against the same reference list used elsewhere.
    """

    errors: list[ValidationIssue] = []
    _check_in_reference_list(equipment_type, "equipment.equipment_type", labels(EQUIPMENT_TYPES), errors)
    _check_in_reference_list(welding_method, "equipment.welding_method", labels(WELDING_METHODS), errors)
    _check_in_reference_list(purpose, "equipment.purpose", labels(PURPOSES), errors)
    return errors


def validate_full(data: SurveyData, ac_registry: AttestationCenterRegistry) -> list[ValidationIssue]:
    """Full blocking re-validation for data that claims to already be
    normalized (``/documents/generate``) — no ``LLMProvider`` call involved,
    the classified fields are checked as-is against the reference lists.
    """

    errors = validate_common_structural(data, ac_registry)
    errors += validate_classified_fields(data.equipment.equipment_type, data.equipment.welding_method, data.equipment.purpose)
    return errors
