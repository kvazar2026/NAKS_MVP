"""Fills the demo ``.docx`` template with normalized survey data.

Uses ``docxtpl`` (Jinja2-in-.docx) per spec: "через шаблонизацию плейсхолдеров
в .docx (Jinja-подобный синтаксис в самом шаблоне), не поиском-заменой текста
напрямую". Both the template read and the rendered output are handled purely
in memory (``io.BytesIO``) — the process never writes the application content
or the generated document to disk (spec, "Хранение — отсутствует"; ADR 0002).
"""

import io

from docxtpl import DocxTemplate

from app.schemas.survey import NormalizedSurveyData


def build_template_context(normalized: NormalizedSurveyData, ac_name: str) -> dict[str, str | int]:
    """Flat placeholder dict for the demo template's ``{{ ... }}`` tags."""

    return {
        "company_name": normalized.organization.company_name,
        "inn": normalized.organization.inn,
        "address": normalized.organization.address,
        "contact_full_name": normalized.contact.full_name,
        "contact_position": normalized.contact.position,
        "contact_phone": normalized.contact.phone,
        "contact_email": normalized.contact.email,
        "ac_name": ac_name,
        "opo_group": normalized.opo_group,
        "region": normalized.region,
        "equipment_type": normalized.equipment.equipment_type,
        "brand": normalized.equipment.brand,
        "model": normalized.equipment.model,
        "manufacturer": normalized.equipment.manufacturer,
        "welding_method": normalized.equipment.welding_method,
        "quantity": normalized.equipment.quantity,
        "serial_numbers": ", ".join(normalized.equipment.serial_numbers),
        "purpose": normalized.equipment.purpose,
    }


def render_document(template_path: str, context: dict[str, str | int]) -> bytes:
    """Render ``template_path`` with ``context`` and return the resulting
    ``.docx`` file content as bytes — no file is created on disk.
    """

    template = DocxTemplate(template_path)
    template.render(context)

    buffer = io.BytesIO()
    template.save(buffer)
    return buffer.getvalue()
