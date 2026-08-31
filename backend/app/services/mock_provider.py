"""``MockProvider`` — deterministic ``LLMProvider`` used whenever there is no
``ANTHROPIC_API_KEY`` (spec, User Story 24), which in this ticket is always:
provider selection based on the environment variable is ``AnthropicProvider``'s
job (ticket 04) — this ticket wires ``MockProvider`` directly.

Matching is deliberately simple (case/whitespace-insensitive exact or
synonym match against ``app/domain/reference_data.py``) and fully
deterministic — no external calls, fixed behavior for a fixed input, as the
spec requires of ``MockProvider``. A value it cannot confidently map is
still returned (best-effort, stripped) rather than dropped, flagged
``NEEDS_REVIEW`` with a matching ambiguity — the caller does not trust
either status at face value and re-checks the result against the same
reference list (see ``app/services/validation.py``).
"""

from app.domain.reference_data import EQUIPMENT_TYPES, PURPOSES, WELDING_METHODS, ReferenceEntry
from app.schemas.llm import (
    LLMAmbiguity,
    LLMFieldResult,
    LLMNormalizationInput,
    LLMNormalizationResult,
    NormalizationStatus,
)
from app.services.llm_provider import LLMProvider


def _match(raw: str, entries: tuple[ReferenceEntry, ...]) -> tuple[str, NormalizationStatus]:
    needle = raw.strip().lower()
    for entry in entries:
        if needle == entry.label.lower() or needle in entry.synonyms:
            return entry.label, NormalizationStatus.NORMALIZED
    return raw.strip(), NormalizationStatus.NEEDS_REVIEW


class MockProvider(LLMProvider):
    async def normalize(self, data: LLMNormalizationInput) -> LLMNormalizationResult:
        matches = {
            "equipment_type": _match(data.equipment_type, EQUIPMENT_TYPES),
            "welding_method": _match(data.welding_method, WELDING_METHODS),
            "purpose": _match(data.purpose, PURPOSES),
        }

        fields = [
            LLMFieldResult(field=field_name, normalized_value=value, status=status)
            for field_name, (value, status) in matches.items()
        ]
        ambiguities = [
            LLMAmbiguity(
                field=field_name,
                description=f"Значение «{getattr(data, field_name)}» не удалось однозначно сопоставить со справочником",
            )
            for field_name, (_, status) in matches.items()
            if status == NormalizationStatus.NEEDS_REVIEW
        ]
        return LLMNormalizationResult(fields=fields, ambiguities=ambiguities)
