"""Реестр аттестационных центров (АЦ).

MVP ships exactly one record: ``Демо-АЦ`` (``code: demo``), no logo/branding
(CONTEXT.md). The real center list in
``docs/ИНФА ПО НАКСАМ_заполнено.csv`` stays outside the runtime registry.
"""

from pathlib import Path

from pydantic import BaseModel

from app.core.yaml_config import load_yaml_list


class AttestationCenterEntry(BaseModel):
    code: str
    name: str


class AttestationCenterRegistry:
    """In-memory lookup of attestation centers, keyed by ``code``."""

    def __init__(self, entries: list[AttestationCenterEntry]) -> None:
        self._entries: dict[str, AttestationCenterEntry] = {entry.code: entry for entry in entries}

    def get(self, code: str) -> AttestationCenterEntry | None:
        return self._entries.get(code)

    def list_all(self) -> list[AttestationCenterEntry]:
        return list(self._entries.values())

    def __len__(self) -> int:
        return len(self._entries)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "AttestationCenterRegistry":
        """Load registry records from a YAML file, loaded once at startup.

        Each record is validated as an ``AttestationCenterEntry`` — a record
        missing a required field fails config loading instead of being
        silently accepted.
        """

        raw_entries = load_yaml_list(path)
        entries = [AttestationCenterEntry(**raw) for raw in raw_entries]
        return cls(entries)
