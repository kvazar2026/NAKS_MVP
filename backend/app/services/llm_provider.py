"""Abstract ``LLMProvider`` interface.

Concrete implementations (``MockProvider`` — ticket 02, ``AnthropicProvider``
— ticket 04) are out of scope for this ticket; only the contract they must
both satisfy is defined here (spec, "LLMProvider" section; ADR 0001).
"""

from abc import ABC, abstractmethod

from app.schemas.llm import LLMNormalizationInput, LLMNormalizationResult


class LLMProviderError(RuntimeError):
    """A provider could not produce a result conforming to the contract.

    Implementations raise this instead of letting a vendor SDK's own exception
    types escape, so callers never have to know which vendor is configured.
    The API layer turns it into the one generic, non-technical message the
    user is allowed to see (User Story 18) — vendor details stay in the logs.
    """


class LLMProvider(ABC):
    """LLM role is limited to normalization and reference-list classification
    of free-text survey fields (ADR 0001) — never engineering calculations,
    never a source of truth on its own (its output is re-checked against the
    reference lists by the caller, spec "Недоверие к выводу LLM").
    """

    @abstractmethod
    async def normalize(self, data: LLMNormalizationInput) -> LLMNormalizationResult:
        """Normalize and classify the given classification-relevant fields.

        Implementations must never be passed, and must never require, PII
        (INN, address, contact full name, phone, email) — enforced by
        ``LLMNormalizationInput`` only containing classification-relevant
        fields.
        """
        raise NotImplementedError
