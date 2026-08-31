"""Result/input contract shared by every ``LLMProvider`` implementation.

Both ``AnthropicProvider`` and ``MockProvider`` (added in later tickets) must
produce exactly this shape — see spec, "LLMProvider" section, and ADR 0001.
"""

from enum import Enum

from pydantic import BaseModel, Field


class LLMNormalizationInput(BaseModel):
    """Only classification-relevant free-text fields go into the LLM.

    Data minimization (spec, "Минимизация данных"): INN, address, contact
    full name, phone and email must NEVER be sent to an ``LLMProvider``. Using
    an explicit field list (instead of a generic ``dict[str, str]`` payload)
    makes that guarantee structural rather than a matter of caller discipline.
    """

    equipment_type: str
    welding_method: str
    purpose: str


class NormalizationStatus(str, Enum):
    """Per-field normalization outcome, as returned by an ``LLMProvider``."""

    NORMALIZED = "normalized"
    NEEDS_REVIEW = "needs_review"


class LLMFieldResult(BaseModel):
    """Normalized value for one input field, plus its normalization status.

    The status alone does not make a value trusted: the backend re-checks
    every classified value against its reference list before accepting it
    (spec, "Недоверие к выводу LLM") — that re-check happens outside this
    contract, in the structural rules module (ticket 02).
    """

    field: str
    normalized_value: str
    status: NormalizationStatus


class LLMAmbiguity(BaseModel):
    """A free-text ambiguity noticed by the provider, used as an additional
    (not primary) source of warnings — it never replaces the rules registry.
    """

    field: str
    description: str


class LLMNormalizationResult(BaseModel):
    """Uniform result contract returned by every ``LLMProvider`` implementation."""

    fields: list[LLMFieldResult]
    ambiguities: list[LLMAmbiguity] = Field(default_factory=list)
