"""Shared vocabulary types used across request/response schemas.

Terms follow CONTEXT.md (project glossary).
"""

from enum import Enum


class AttestationDirection(str, Enum):
    """Направление аттестации — one of the three survey/generation tracks.

    MVP only functionally supports ``EQUIPMENT``: the deterministic structural
    rules (ticket 02) are responsible for rejecting the other two values, not
    this type. They exist here because the direction is a fixed, closed set of
    three tracks (see CONTEXT.md) and the UI must be able to render
    "materials"/"welders" as visible-but-disabled options (User Story 6).
    """

    EQUIPMENT = "equipment"
    MATERIALS = "materials"
    WELDERS = "welders"
