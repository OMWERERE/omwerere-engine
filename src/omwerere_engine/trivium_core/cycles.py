"""Bounded-history repeat-detection primitives."""
from typing import Any


def push_history(history: list, entry: Any, window: int) -> list:
    """Return a NEW list (`history + [entry]`, sliced to the last `window`
    items). Does not mutate the input list."""
    new_history = history + [entry]
    return new_history[-window:]


def repeat_count(history: list, entry: Any) -> int:
    """Return the number of times `entry` appears in `history` (exact
    equality count)."""
    return history.count(entry)


def is_repeating(history: list, entry: Any, threshold: int) -> bool:
    """True if `entry` appears in `history` at least `threshold` times."""
    return repeat_count(history, entry) >= threshold
