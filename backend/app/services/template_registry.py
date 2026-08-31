"""``template registry``: (код АЦ, направление) -> шаблон ``.docx``.

MVP ships exactly one record: (``demo``, ``equipment``). The template file
itself (``backend/templates/...``) may not exist yet — this ticket only
defines the lookup structure and the config-loading mechanism; ticket 02
adds the actual demo ``.docx`` file.
"""

from pathlib import Path

from pydantic import BaseModel

from app.core.yaml_config import load_yaml_list
from app.schemas.common import AttestationDirection


class TemplateRegistryEntry(BaseModel):
    ac_code: str
    direction: AttestationDirection
    template_path: str
    label: str


class TemplateRegistry:
    """In-memory lookup of template records, keyed by (ac_code, direction)."""

    def __init__(self, entries: list[TemplateRegistryEntry]) -> None:
        self._entries: dict[tuple[str, AttestationDirection], TemplateRegistryEntry] = {
            (entry.ac_code, entry.direction): entry for entry in entries
        }

    def get(self, ac_code: str, direction: AttestationDirection) -> TemplateRegistryEntry | None:
        return self._entries.get((ac_code, direction))

    def __len__(self) -> int:
        return len(self._entries)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "TemplateRegistry":
        """Load registry records from a YAML file, loaded once at startup.

        Each record is validated as a ``TemplateRegistryEntry`` — a record
        missing a required field fails config loading (raises
        ``pydantic.ValidationError``) instead of being silently accepted.
        """

        raw_entries = load_yaml_list(path)
        entries = [TemplateRegistryEntry(**raw) for raw in raw_entries]
        return cls(entries)
