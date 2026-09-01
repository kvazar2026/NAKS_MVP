"""Application settings.

Project settings use the ``NAKS_`` prefix. Vendor credentials deliberately do
not: ``ANTHROPIC_API_KEY`` is the name the vendor's own SDK and docs use, and
renaming it to ``NAKS_ANTHROPIC_API_KEY`` would surprise every operator who
already has it set — hence the explicit ``validation_alias``.
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> backend/
BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NAKS_", env_file=".env", extra="ignore")

    template_registry_path: Path = BACKEND_ROOT / "config" / "templates.yaml"
    ac_registry_path: Path = BACKEND_ROOT / "config" / "attestation_centers.yaml"
    warning_rules_path: Path = BACKEND_ROOT / "config" / "warning_rules.yaml"

    # Which LLMProvider implementation to build at startup — a provider *name*
    # from the registry, not "whichever vendor key happens to be set" (ticket
    # 04). Unknown name, or a real provider without its credentials, fails
    # startup rather than silently degrading to the mock.
    llm_provider: str = "mock"

    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    anthropic_model: str = "claude-sonnet-5"


def get_settings() -> Settings:
    return Settings()
