"""Request/response contracts for ``POST /api/v1/documents/generate``.

On success the endpoint streams a ``.docx`` file (no JSON response body/model
for that case — see spec: ``Content-Disposition: attachment``).
``DocumentGenerateErrorResponse`` covers the documented ``400`` case, where
the backend independently re-runs the same blocking structural rules used by
``/survey/validate`` (never trusting the client's claim of prior validation)
and rejects the request, reusing the same ``ValidationIssue`` shape.
"""

from pydantic import BaseModel, Field

from app.schemas.common import AttestationDirection
from app.schemas.survey import NormalizedSurveyData, ValidationIssue


class DocumentGenerateRequest(BaseModel):
    """Body of ``POST /api/v1/documents/generate``."""

    normalized_data: NormalizedSurveyData
    attestation_direction: AttestationDirection
    attestation_center_code: str


class DocumentGenerateErrorResponse(BaseModel):
    """Body returned with HTTP 400 when structural re-validation fails."""

    detail: str
    errors: list[ValidationIssue] = Field(default_factory=list)
