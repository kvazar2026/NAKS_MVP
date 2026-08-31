"""``POST /api/v1/documents/generate`` (spec, Backend section; ticket 02).

**Never trusts the client.** Independently re-runs the exact same blocking
structural rules ``/survey/validate`` uses (``validate_full``, shared module
— see ``app/services/validation.py``) on the submitted ``normalized_data``
and rejects with ``400`` on any failure, regardless of what the client
claims about prior validation. No ``LLMProvider`` call happens here — by the
time data reaches this endpoint it is expected to already be normalized, and
the re-validation checks that claim rather than assuming it.
"""

import io
import time

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response, StreamingResponse

from app.api.dependencies import get_ac_registry, get_template_registry
from app.core.config import BACKEND_ROOT
from app.core.logging import log_outcome
from app.schemas.documents import DocumentGenerateErrorResponse, DocumentGenerateRequest
from app.schemas.survey import ValidationIssue
from app.services.ac_registry import AttestationCenterRegistry
from app.services.document_generation import build_template_context, render_document
from app.services.template_registry import TemplateRegistry
from app.services.validation import validate_full

router = APIRouter()

_ENDPOINT = "/api/v1/documents/generate"
_DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_DOWNLOAD_FILENAME = "naks-equipment-application-demo.docx"


def _rejected(direction: str, started_at: float, detail: str, errors: list[ValidationIssue]) -> JSONResponse:
    duration_ms = (time.perf_counter() - started_at) * 1000
    error_code = ",".join(sorted({issue.code for issue in errors})) or None
    log_outcome(endpoint=_ENDPOINT, direction=direction, result="blocked", duration_ms=duration_ms, error_code=error_code)
    body = DocumentGenerateErrorResponse(detail=detail, errors=errors)
    return JSONResponse(status_code=400, content=body.model_dump(mode="json"))


@router.post("/api/v1/documents/generate")
async def generate_document(
    request: DocumentGenerateRequest,
    ac_registry: AttestationCenterRegistry = Depends(get_ac_registry),
    template_registry: TemplateRegistry = Depends(get_template_registry),
) -> Response:
    started_at = time.perf_counter()
    direction = request.attestation_direction.value

    errors: list[ValidationIssue] = validate_full(request.normalized_data, ac_registry)

    # Belt-and-braces consistency check: the routing params passed alongside
    # ``normalized_data`` must agree with what that data itself claims — a
    # mismatch is exactly the kind of client claim this endpoint must not
    # take on faith.
    if request.attestation_direction != request.normalized_data.attestation_direction:
        errors.append(
            ValidationIssue(
                field="attestation_direction",
                code="mismatched_routing_field",
                message="Направление аттестации не совпадает с данными заявки",
            )
        )
    if request.attestation_center_code != request.normalized_data.attestation_center_code:
        errors.append(
            ValidationIssue(
                field="attestation_center_code",
                code="mismatched_routing_field",
                message="Код аттестационного центра не совпадает с данными заявки",
            )
        )

    if errors:
        return _rejected(direction, started_at, "Структурная проверка данных заявки не пройдена", errors)

    template_entry = template_registry.get(request.attestation_center_code, request.attestation_direction)
    ac_entry = ac_registry.get(request.attestation_center_code)
    if template_entry is None or ac_entry is None:
        # Unreachable once validate_full has passed (both registries were
        # already consulted there) — kept as a defensive guard, not a
        # reachable branch to test.
        return _rejected(direction, started_at, "Шаблон заявки не найден", [])

    context = build_template_context(request.normalized_data, ac_entry.name)
    template_path = BACKEND_ROOT / template_entry.template_path
    document_bytes = render_document(str(template_path), context)

    duration_ms = (time.perf_counter() - started_at) * 1000
    log_outcome(endpoint=_ENDPOINT, direction=direction, result="success", duration_ms=duration_ms)

    return StreamingResponse(
        io.BytesIO(document_bytes),
        media_type=_DOCX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{_DOWNLOAD_FILENAME}"'},
    )
