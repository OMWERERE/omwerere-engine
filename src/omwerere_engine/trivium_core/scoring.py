"""Generic scoring primitives."""


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    """Clamp `value` into the [low, high] range."""
    return max(low, min(high, value))
