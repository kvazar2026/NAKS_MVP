"""Small shared helper for loading list-of-records YAML config files.

Used by the template registry and the attestation center registry (and,
later, the validation rules registry in ticket 03) so "load a list of
config records from YAML" is implemented once.
"""

from pathlib import Path

import yaml


def load_yaml_list(path: str | Path) -> list[dict]:
    """Read ``path`` and return its top-level YAML sequence as a list of dicts.

    Raises ``ValueError`` if the file's content is not a YAML list (an empty
    file yields an empty list rather than an error).
    """

    with open(path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if data is None:
        return []
    if not isinstance(data, list):
        raise ValueError(f"Expected a YAML list of records in {path}, got {type(data).__name__}")
    return data
