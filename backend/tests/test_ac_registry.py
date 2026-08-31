from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import get_settings
from app.services.ac_registry import AttestationCenterRegistry


def test_loads_mvp_demo_ac_record_from_default_config():
    settings = get_settings()

    registry = AttestationCenterRegistry.from_yaml(settings.ac_registry_path)

    entry = registry.get("demo")
    assert entry is not None
    assert entry.name == "Демо-АЦ"
    assert len(registry) == 1
    assert registry.list_all() == [entry]


def test_unknown_code_is_not_found():
    settings = get_settings()
    registry = AttestationCenterRegistry.from_yaml(settings.ac_registry_path)

    assert registry.get("some-real-ac") is None


def test_record_missing_required_field_fails_config_loading(tmp_path: Path):
    bad_config = tmp_path / "attestation_centers.yaml"
    bad_config.write_text("- code: demo\n  # name missing\n", encoding="utf-8")

    with pytest.raises(ValidationError):
        AttestationCenterRegistry.from_yaml(bad_config)
