"""Warning rules registry: config loading is fail-fast, evaluation is
deterministic (ticket 03, ADR 0004).

Config-loading tests write their own YAML to ``tmp_path`` so a malformed
record can be exercised without shipping a broken file. The last group checks
the file the app actually ships, since a rule that never matches anything is
indistinguishable from no rule at all.
"""

import textwrap

import pytest
import yaml

from app.core.config import get_settings
from app.schemas.survey import SurveyData, WarningVerificationStatus
from app.services.warning_rules import WarningRulesRegistry

_COMPLETE_RULE = """
- code: demo_rule
  direction: equipment
  field: equipment.purpose
  condition:
    all_of:
      - field: equipment.purpose
        equals: Ремонт и восстановление оборудования
  message: Сообщение
  explanation: Объяснение
  source: naks-checklist-monetization.md
  verification_status: not_verified_by_expert
  last_reviewed_at: 2026-09-01
"""

# The same record as data, so a test can drop exactly one key without the
# text-editing games that make it easy to delete more than intended.
_COMPLETE_RULE_RECORD = yaml.safe_load(_COMPLETE_RULE)[0]


def _registry_from(tmp_path, yaml_text: str) -> WarningRulesRegistry:
    path = tmp_path / "warning_rules.yaml"
    path.write_text(textwrap.dedent(yaml_text), encoding="utf-8")
    return WarningRulesRegistry.from_yaml(path)


def _registry_from_records(tmp_path, records: list[dict]) -> WarningRulesRegistry:
    return _registry_from(tmp_path, yaml.safe_dump(records, allow_unicode=True))


@pytest.fixture
def survey_data(valid_normalized_data) -> SurveyData:
    return SurveyData(**valid_normalized_data)


# --- config loading is fail-fast -------------------------------------------


@pytest.mark.parametrize("missing_field", sorted(_COMPLETE_RULE_RECORD))
def test_record_missing_required_metadata_fails_to_load(tmp_path, missing_field):
    record = {key: value for key, value in _COMPLETE_RULE_RECORD.items() if key != missing_field}

    with pytest.raises(ValueError, match=missing_field):
        _registry_from_records(tmp_path, [record])


def test_the_complete_record_the_previous_test_mutates_does_load(tmp_path):
    """Guards the test above: if the baseline record stopped loading, every
    "missing field" case would pass for the wrong reason.
    """

    assert len(_registry_from_records(tmp_path, [_COMPLETE_RULE_RECORD])) == 1


def test_record_with_unknown_key_fails_to_load(tmp_path):
    with pytest.raises(ValueError):
        _registry_from(tmp_path, _COMPLETE_RULE + "  severity: critical\n")


def test_unknown_field_path_fails_to_load(tmp_path):
    broken = _COMPLETE_RULE.replace("field: equipment.purpose", "field: equipment.purpsoe")

    with pytest.raises(ValueError, match="purpsoe"):
        _registry_from(tmp_path, broken)


def test_field_path_into_a_non_object_fails_to_load(tmp_path):
    broken = _COMPLETE_RULE.replace("field: equipment.purpose", "field: region.nested")

    with pytest.raises(ValueError, match="region"):
        _registry_from(tmp_path, broken)


def test_predicate_without_an_operator_fails_to_load(tmp_path):
    broken = _COMPLETE_RULE.replace("        equals: Ремонт и восстановление оборудования\n", "")

    with pytest.raises(ValueError):
        _registry_from(tmp_path, broken)


def test_predicate_with_two_operators_fails_to_load(tmp_path):
    broken = _COMPLETE_RULE.replace(
        "        equals: Ремонт и восстановление оборудования",
        "        equals: Ремонт и восстановление оборудования\n        not_equals: Монтаж оборудования",
    )

    with pytest.raises(ValueError):
        _registry_from(tmp_path, broken)


def test_empty_condition_list_fails_to_load(tmp_path):
    with pytest.raises(ValueError):
        _registry_from(
            tmp_path,
            """
            - code: demo_rule
              direction: equipment
              field: equipment.purpose
              condition:
                all_of: []
              message: Сообщение
              explanation: Объяснение
              source: naks-checklist-monetization.md
              verification_status: not_verified_by_expert
              last_reviewed_at: 2026-09-01
            """,
        )


def test_duplicate_rule_codes_fail_to_load(tmp_path):
    with pytest.raises(ValueError, match="demo_rule"):
        _registry_from(tmp_path, _COMPLETE_RULE + _COMPLETE_RULE)


# --- evaluation -------------------------------------------------------------


def test_matching_rule_produces_a_warning_with_full_metadata(tmp_path, survey_data):
    registry = _registry_from(tmp_path, _COMPLETE_RULE)

    warnings = registry.evaluate(survey_data)

    assert len(warnings) == 1
    warning = warnings[0]
    assert warning.code == "demo_rule"
    assert warning.field == "equipment.purpose"
    assert warning.explanation == "Объяснение"
    assert warning.source == "naks-checklist-monetization.md"
    assert warning.verification_status == WarningVerificationStatus.NOT_VERIFIED_BY_EXPERT


def test_non_matching_rule_produces_no_warning(tmp_path, survey_data):
    registry = _registry_from(tmp_path, _COMPLETE_RULE.replace("Ремонт и восстановление оборудования", "Монтаж оборудования"))

    assert registry.evaluate(survey_data) == []


def test_any_of_matches_on_a_single_predicate(tmp_path, survey_data):
    registry = _registry_from(
        tmp_path,
        _COMPLETE_RULE.replace(
            "    all_of:\n      - field: equipment.purpose\n        equals: Ремонт и восстановление оборудования",
            "    any_of:\n      - field: equipment.purpose\n        equals: Монтаж оборудования\n"
            "      - field: equipment.welding_method\n        equals: РД — ручная дуговая сварка покрытым электродом",
        ),
    )

    assert len(registry.evaluate(survey_data)) == 1


def test_all_of_needs_every_predicate(tmp_path, survey_data):
    registry = _registry_from(
        tmp_path,
        _COMPLETE_RULE.replace(
            "        equals: Ремонт и восстановление оборудования",
            "        equals: Ремонт и восстановление оборудования\n"
            "      - field: opo_group\n        equals: Группа 2 — технологические трубопроводы",
        ),
    )

    # purpose matches, opo_group does not (the fixture is group 1).
    assert registry.evaluate(survey_data) == []


def test_length_comparison_predicate(tmp_path, survey_data):
    registry = _registry_from(
        tmp_path,
        _COMPLETE_RULE.replace(
            "      - field: equipment.purpose\n        equals: Ремонт и восстановление оборудования",
            "      - field: equipment.quantity\n        not_equals_length_of: equipment.serial_numbers",
        ),
    )

    assert registry.evaluate(survey_data) == []

    mismatched = survey_data.model_copy(
        update={"equipment": survey_data.equipment.model_copy(update={"quantity": 5})}
    )
    assert len(registry.evaluate(mismatched)) == 1


def test_rules_for_another_direction_are_skipped(tmp_path, survey_data):
    registry = _registry_from(tmp_path, _COMPLETE_RULE.replace("direction: equipment", "direction: materials"))

    assert registry.evaluate(survey_data) == []


# --- the config the app actually ships --------------------------------------


def test_shipped_rules_file_loads_and_is_not_empty():
    registry = WarningRulesRegistry.from_yaml(get_settings().warning_rules_path)

    assert len(registry) >= 3


def test_shipped_rules_do_not_fire_on_a_clean_submission(survey_data):
    """The reference "everything is fine" submission must stay warning-free —
    a rule broad enough to flag it would make the hint meaningless.
    """

    registry = WarningRulesRegistry.from_yaml(get_settings().warning_rules_path)

    assert registry.evaluate(survey_data) == []


def test_shipped_rules_are_all_marked_unverified_and_sourced():
    registry = WarningRulesRegistry.from_yaml(get_settings().warning_rules_path)

    mismatched = SurveyData(
        **{
            "organization": {"inn": "7701234567", "company_name": "x", "address": "x"},
            "contact": {"full_name": "x", "position": "x", "phone": "+79001234567", "email": "a@b.cd"},
            "attestation_center_code": "demo",
            "attestation_direction": "equipment",
            "opo_group": "Группа 3 — объекты котлонадзора",
            "region": "x",
            "equipment": {
                "equipment_type": "Аппарат аргонодуговой сварки (TIG)",
                "brand": "x",
                "model": "x",
                "manufacturer": "x",
                "welding_method": "РАД — ручная аргонодуговая сварка",
                "quantity": 4,
                "serial_numbers": ["SN-1"],
                "purpose": "Сварка сосудов, работающих под давлением",
            },
        }
    )

    warnings = registry.evaluate(mismatched)

    # This submission trips several checklist rules at once.
    assert len(warnings) >= 2
    for warning in warnings:
        assert warning.source == "naks-checklist-monetization.md"
        assert warning.verification_status == WarningVerificationStatus.NOT_VERIFIED_BY_EXPERT
        assert warning.explanation
