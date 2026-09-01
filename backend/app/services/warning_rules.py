"""Checklist-derived ``warning``-level rules registry (ticket 03, ADR 0004).

The counterpart of ``app/services/validation.py``: that module holds the
blocking ``error`` rules (structure, formats, reference lists), this one holds
the non-blocking ``warning`` rules derived from the typical mistakes in
``naks-checklist-monetization.md``. The two levels stay in separate modules on
purpose — a checklist hint must never be able to block a submission, and a
structural rule must never degrade into a hint.

Rules are configuration (``backend/config/warning_rules.yaml``), not code, and
are loaded once at startup. Every record must carry the full metadata set from
the spec — code, direction, field, condition, message, explanation, source,
verification status, last review date — and ``extra="forbid"`` plus the absence
of defaults means a record missing any of them (or carrying an unknown key)
fails startup rather than being silently accepted.

Conditions are evaluated deterministically here, never by an LLM (ADR 0001):
a condition is ``all_of``/``any_of`` over field predicates, and field paths are
verified against ``SurveyData`` at load time, so a typo in a path is a startup
error instead of a rule that quietly never matches.

Deliberately not supported: nested condition groups. None of the checklist
rules need one, and a half-designed expression language is harder to review
than the flat form. Add nesting when a real rule requires it.
"""

from datetime import date
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

from app.core.yaml_config import load_yaml_list
from app.schemas.common import AttestationDirection
from app.schemas.survey import SurveyData, ValidationWarning, WarningVerificationStatus

_PREDICATE_OPERATORS = ("equals", "not_equals", "not_equals_length_of")


class FieldPredicate(BaseModel):
    """One deterministic check against a survey field.

    Exactly one operator must be set: ``equals``/``not_equals`` compare the
    field's value with a literal, ``not_equals_length_of`` compares it with the
    length of a list at another path (used for "quantity vs. number of serial
    numbers"). Ambiguous records — no operator, or several — are a config
    error.
    """

    model_config = ConfigDict(extra="forbid")

    field: str
    equals: str | None = None
    not_equals: str | None = None
    not_equals_length_of: str | None = None

    @model_validator(mode="after")
    def _exactly_one_operator(self) -> "FieldPredicate":
        used = [name for name in _PREDICATE_OPERATORS if getattr(self, name) is not None]
        if len(used) != 1:
            raise ValueError(
                f"Predicate on field '{self.field}' must use exactly one of "
                f"{', '.join(_PREDICATE_OPERATORS)}, got {len(used)}"
            )
        return self


class RuleCondition(BaseModel):
    """``all_of`` (every predicate matches) or ``any_of`` (at least one does).

    Exactly one of the two, and never an empty list: an empty ``all_of`` would
    match every submission, which is never what a checklist rule means.
    """

    model_config = ConfigDict(extra="forbid")

    all_of: list[FieldPredicate] | None = None
    any_of: list[FieldPredicate] | None = None

    @model_validator(mode="after")
    def _exactly_one_non_empty_combinator(self) -> "RuleCondition":
        used = [name for name in ("all_of", "any_of") if getattr(self, name) is not None]
        if len(used) != 1:
            raise ValueError(f"Condition must use exactly one of all_of, any_of, got {len(used)}")
        if not getattr(self, used[0]):
            raise ValueError(f"Condition '{used[0]}' must list at least one predicate")
        return self


class WarningRule(BaseModel):
    """One checklist-derived rule, with the metadata ADR 0004 requires."""

    model_config = ConfigDict(extra="forbid")

    code: str
    direction: AttestationDirection
    field: str
    condition: RuleCondition
    message: str
    explanation: str
    source: str
    verification_status: WarningVerificationStatus
    last_reviewed_at: date


def _resolve(data: SurveyData, path: str) -> Any:
    value: Any = data
    for part in path.split("."):
        value = getattr(value, part)
    return value


def _assert_path_exists(path: str) -> None:
    """Fail config loading on a field path ``SurveyData`` does not have.

    Without this a mistyped path would raise only when some submission
    happened to trigger the rule — i.e. a latent 500 instead of a startup
    error.
    """

    annotation: Any = SurveyData
    walked: list[str] = []
    for part in path.split("."):
        fields = getattr(annotation, "model_fields", None)
        if fields is None:
            raise ValueError(
                f"Invalid field path '{path}': '{'.'.join(walked)}' is not a nested object"
            )
        if part not in fields:
            raise ValueError(f"Invalid field path '{path}': survey data has no field '{part}'")
        annotation = fields[part].annotation
        walked.append(part)


def _predicate_matches(predicate: FieldPredicate, data: SurveyData) -> bool:
    value = _resolve(data, predicate.field)
    if predicate.equals is not None:
        return value == predicate.equals
    if predicate.not_equals is not None:
        return value != predicate.not_equals
    return value != len(_resolve(data, predicate.not_equals_length_of))


def _condition_matches(condition: RuleCondition, data: SurveyData) -> bool:
    if condition.all_of is not None:
        return all(_predicate_matches(predicate, data) for predicate in condition.all_of)
    return any(_predicate_matches(predicate, data) for predicate in condition.any_of)


class WarningRulesRegistry:
    """In-memory set of ``warning`` rules, evaluated against normalized data."""

    def __init__(self, rules: list[WarningRule]) -> None:
        self._rules = rules

    def evaluate(self, data: SurveyData) -> list[ValidationWarning]:
        """Warnings triggered by ``data``, in config order.

        Callers must pass data that has already been normalized and passed the
        blocking rules: matching a checklist rule against raw free text would
        compare against canonical reference-list labels the user never typed.
        """

        return [
            ValidationWarning(
                field=rule.field,
                code=rule.code,
                message=rule.message,
                explanation=rule.explanation,
                source=rule.source,
                verification_status=rule.verification_status,
            )
            for rule in self._rules
            if rule.direction == data.attestation_direction and _condition_matches(rule.condition, data)
        ]

    def __len__(self) -> int:
        return len(self._rules)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "WarningRulesRegistry":
        """Load and fully verify the rules file — any problem raises here, at
        startup, rather than at request time.
        """

        rules = [WarningRule(**raw) for raw in load_yaml_list(path)]

        codes = [rule.code for rule in rules]
        duplicates = sorted({code for code in codes if codes.count(code) > 1})
        if duplicates:
            raise ValueError(f"Duplicate warning rule codes in {path}: {', '.join(duplicates)}")

        for rule in rules:
            _assert_path_exists(rule.field)
            predicates = rule.condition.all_of if rule.condition.all_of is not None else rule.condition.any_of
            for predicate in predicates:
                _assert_path_exists(predicate.field)
                if predicate.not_equals_length_of is not None:
                    _assert_path_exists(predicate.not_equals_length_of)

        return cls(rules)
