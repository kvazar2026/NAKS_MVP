from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import get_settings
from app.schemas.common import AttestationDirection
from app.services.template_registry import TemplateRegistry


def test_loads_mvp_demo_equipment_record_from_default_config():
    settings = get_settings()

    registry = TemplateRegistry.from_yaml(settings.template_registry_path)

    entry = registry.get("demo", AttestationDirection.EQUIPMENT)
    assert entry is not None
    assert entry.ac_code == "demo"
    assert entry.direction == AttestationDirection.EQUIPMENT
    assert entry.template_path


def test_unknown_ac_or_direction_is_not_found():
    settings = get_settings()
    registry = TemplateRegistry.from_yaml(settings.template_registry_path)

    assert registry.get("unknown-ac", AttestationDirection.EQUIPMENT) is None
    assert registry.get("demo", AttestationDirection.MATERIALS) is None


def test_record_missing_required_field_fails_config_loading(tmp_path: Path):
    bad_config = tmp_path / "templates.yaml"
    bad_config.write_text(
        "- ac_code: demo\n  direction: equipment\n  # template_path and label missing\n",
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        TemplateRegistry.from_yaml(bad_config)
