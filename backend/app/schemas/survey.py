"""Request/response contracts for ``POST /api/v1/survey/validate``.

Field coverage follows the "Заполнение опросника" user stories in the spec
(``.scratch/naks-mvp-core/spec.md``, stories 3-13). No validation/normalization
*logic* lives here — this ticket only defines the shape of the data; the
structural rule engine and LLM-backed normalization are ticket 02.
"""

from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.common import AttestationDirection


class OrganizationInfo(BaseModel):
    """Реквизиты организации (User Story 3)."""

    inn: str
    company_name: str
    address: str


class ContactInfo(BaseModel):
    """Контактное лицо (User Story 4)."""

    full_name: str
    position: str
    phone: str
    email: str


class EquipmentInfo(BaseModel):
    """Поля по направлению «оборудование» (User Story 7)."""

    equipment_type: str
    brand: str
    model: str
    manufacturer: str
    welding_method: str
    quantity: int
    serial_numbers: list[str]
    purpose: str


class SurveyData(BaseModel):
    """Fields describing the application itself, shared between the raw
    submission (``SurveyValidateRequest``) and the normalized result
    (``NormalizedSurveyData``). Consent is deliberately excluded here — it is
    a one-time submission gate, not application data to normalize/return.
    """

    organization: OrganizationInfo
    contact: ContactInfo
    attestation_center_code: str
    attestation_direction: AttestationDirection
    opo_group: str
    region: str
    equipment: EquipmentInfo


class SurveyValidateRequest(SurveyData):
    """Body of ``POST /api/v1/survey/validate`` (User Stories 3-10)."""

    consent: bool


class NormalizedSurveyData(SurveyData):
    """Data as returned after structural validation + LLM normalization."""


class ValidationIssue(BaseModel):
    """A single blocking (``error``-level) validation failure (User Story 11)."""

    field: str
    code: str
    message: str


class WarningVerificationStatus(str, Enum):
    """Статус проверки чернового правила (see ADR 0004 / CONTEXT.md)."""

    NOT_VERIFIED_BY_EXPERT = "not_verified_by_expert"
    VERIFIED = "verified"


class ValidationWarning(BaseModel):
    """A single non-blocking (``warning``-level) checklist hint
    (User Stories 12-13): explanation, source and verification status are
    mandatory per ADR 0004 — a warning without them must not be constructible
    from a well-formed config record (enforced by the rules registry loader
    in ticket 03, not by this response schema).
    """

    field: str
    code: str
    message: str
    explanation: str
    source: str
    verification_status: WarningVerificationStatus


class SurveyValidateResponse(BaseModel):
    """Response of ``POST /api/v1/survey/validate``.

    ``normalized_data`` is only present when there are no blocking ``errors``.
    """

    valid: bool
    normalized_data: NormalizedSurveyData | None = None
    errors: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[ValidationWarning] = Field(default_factory=list)
