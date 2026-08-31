"""Application settings.

Only the paths needed to load the config-driven registries live here for now.
Provider selection (``ANTHROPIC_API_KEY`` presence, etc.) is introduced
alongside the concrete ``LLMProvider`` implementations in later tickets.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> backend/
BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NAKS_", env_file=".env", extra="ignore")

    template_registry_path: Path = BACKEND_ROOT / "config" / "templates.yaml"
    ac_registry_path: Path = BACKEND_ROOT / "config" / "attestation_centers.yaml"


def get_settings() -> Settings:
    return Settings()
