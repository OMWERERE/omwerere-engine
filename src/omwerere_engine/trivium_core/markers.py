"""Marker-based text signal matching primitives.

Copied verbatim from omwerere-org/app/backend/app/trivium_core (its own
README says it's designed to be copied into another project directly).
"""
from typing import Sequence, TypeVar

LabelT = TypeVar("LabelT")


def marker_match(text: str, markers: Sequence[str]) -> bool:
    """Lowercase `text` and return True if any marker substring is present."""
    lowered = text.lower()
    return any(marker in lowered for marker in markers)


def first_match(
    text: str,
    groups: Sequence[tuple[LabelT, Sequence[str]]],
    default: LabelT,
) -> LabelT:
    """Check `groups` (ordered (label, markers) pairs) in order and return the
    label of the first group whose markers match `text` via marker_match().
    Returns `default` if no group matches."""
    for label, markers in groups:
        if marker_match(text, markers):
            return label
    return default
