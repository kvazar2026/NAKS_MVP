"""``AnthropicProvider`` — the first real ``LLMProvider`` (ticket 04).

Role is the same as every other provider and no wider (ADR 0001): normalize
free-text values for the three classification-relevant fields onto the
canonical labels in ``app/domain/reference_data.py``. No engineering
calculations, no inventing missing data.

Two guarantees this file must not weaken:

- **Data minimization.** Only ``LLMNormalizationInput``'s three fields are
  ever sent. The contract makes that structural — INN, address, contact name,
  phone and email are not even reachable from here — and the prompt below
  must never be extended to ask for them.
- **No trust in the output.** The strict response schema below rejects a
  malformed answer, and the caller independently re-checks every classified
  value against the same reference lists (spec, "Недоверие к выводу LLM").
  A value arriving from a real vendor is not more trusted than a mock's.

Verified against the installed SDK (``anthropic`` 1.2.0):
``AsyncAnthropic().messages.parse(..., output_format=<pydantic model>)``
returns a response whose ``parsed_output`` is an instance of that model.
"""

from typing import Literal

import anthropic
from pydantic import BaseModel, ValidationError

from app.domain.reference_data import EQUIPMENT_TYPES, PURPOSES, WELDING_METHODS, ReferenceEntry
from app.schemas.llm import (
    LLMAmbiguity,
    LLMFieldResult,
    LLMNormalizationInput,
    LLMNormalizationResult,
    NormalizationStatus,
)
from app.services.llm_provider import LLMProvider, LLMProviderError

_CLASSIFIED_FIELDS = ("equipment_type", "welding_method", "purpose")


class _ProviderFieldResult(BaseModel):
    """Stricter than ``LLMFieldResult``: the field name is a closed set, so a
    response naming something else is rejected instead of quietly ignored.
    """

    field: Literal["equipment_type", "welding_method", "purpose"]
    normalized_value: str
    status: Literal["normalized", "needs_review"]


class _ProviderAmbiguity(BaseModel):
    field: Literal["equipment_type", "welding_method", "purpose"]
    description: str


class _ProviderResponse(BaseModel):
    fields: list[_ProviderFieldResult]
    ambiguities: list[_ProviderAmbiguity] = []


def _labels_block(title: str, entries: tuple[ReferenceEntry, ...]) -> str:
    lines = "\n".join(f"- {entry.label}" for entry in entries)
    return f"{title}:\n{lines}"


def _system_prompt() -> str:
    """Built from the reference lists themselves, so the prompt cannot drift
    away from the lists the backend validates against afterwards.
    """

    return (
        "Ты помогаешь нормализовать поля заявки на аттестацию сварочного "
        "оборудования в НАКС. Твоя единственная задача — сопоставить "
        "свободный текст пользователя с каноническими значениями из "
        "справочников ниже.\n\n"
        "Правила:\n"
        "- Возвращай ровно три поля: equipment_type, welding_method, purpose.\n"
        "- normalized_value должен быть дословно равен одной из подписей "
        "справочника, если сопоставление уверенное; тогда status = "
        '"normalized".\n'
        "- Если уверенного соответствия нет, верни исходный текст без "
        'изменений и status = "needs_review", а также добавь запись в '
        "ambiguities с описанием проблемы.\n"
        "- Ничего не вычисляй и не додумывай: режимы сварки, эквивалент "
        "углерода и любые инженерные параметры вне твоей задачи.\n"
        "- Не придумывай значения, которых нет в справочниках.\n\n"
        + _labels_block("Справочник типов оборудования (equipment_type)", EQUIPMENT_TYPES)
        + "\n\n"
        + _labels_block("Справочник способов сварки (welding_method)", WELDING_METHODS)
        + "\n\n"
        + _labels_block("Справочник назначения (purpose)", PURPOSES)
    )


def _user_prompt(data: LLMNormalizationInput) -> str:
    return (
        "Нормализуй значения:\n"
        f"equipment_type: {data.equipment_type}\n"
        f"welding_method: {data.welding_method}\n"
        f"purpose: {data.purpose}"
    )


class AnthropicProvider(LLMProvider):
    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        client: object | None = None,
        max_tokens: int = 2048,
    ) -> None:
        # `client` is an injection point for tests, which exercise this class
        # against a stub instead of the network. Production always builds the
        # real async client here.
        self._client = client if client is not None else anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    async def normalize(self, data: LLMNormalizationInput) -> LLMNormalizationResult:
        try:
            response = await self._client.messages.parse(
                model=self._model,
                max_tokens=self._max_tokens,
                # Classification is a simple task — low effort keeps latency
                # and cost down. `temperature` is deliberately absent: it is
                # rejected on this model generation.
                output_config={"effort": "low"},
                system=_system_prompt(),
                messages=[{"role": "user", "content": _user_prompt(data)}],
                output_format=_ProviderResponse,
            )
        except anthropic.AnthropicError as error:
            # Vendor exception types stop here (see LLMProviderError).
            raise LLMProviderError(f"Anthropic request failed: {type(error).__name__}") from error

        parsed = getattr(response, "parsed_output", None)
        if parsed is None:
            raise LLMProviderError("Anthropic returned no structured output")

        try:
            validated = _ProviderResponse.model_validate(parsed, from_attributes=True)
        except ValidationError as error:
            raise LLMProviderError("Anthropic response did not match the expected schema") from error

        returned_fields = {result.field for result in validated.fields}
        missing = [name for name in _CLASSIFIED_FIELDS if name not in returned_fields]
        if missing:
            # Silently defaulting a missing field would hand the caller a
            # value the model never actually classified.
            raise LLMProviderError(f"Anthropic response is missing fields: {', '.join(missing)}")

        return LLMNormalizationResult(
            fields=[
                LLMFieldResult(
                    field=result.field,
                    normalized_value=result.normalized_value,
                    status=NormalizationStatus(result.status),
                )
                for result in validated.fields
            ],
            ambiguities=[
                LLMAmbiguity(field=item.field, description=item.description)
                for item in validated.ambiguities
            ],
        )
