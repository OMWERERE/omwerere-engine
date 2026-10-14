"""
trivium_core — zero-dependency, stdlib-only primitives, copied from
omwerere-org/app/backend/app/trivium_core for standalone reuse here.
Relative imports (not `from app...`) since this isn't nested under `app`.
"""
from .cycles import is_repeating, push_history, repeat_count
from .markers import first_match, marker_match
from .scoring import clamp

__all__ = [
    "marker_match",
    "first_match",
    "push_history",
    "repeat_count",
    "is_repeating",
    "clamp",
]
