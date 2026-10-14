"""Hash-chained, tamper-evident log: the one construction every tributary uses.

SHA-256 over the event's fields joined with "|", then the previous event's
hash. Altering, deleting or reordering any past event breaks every hash after
it. Byte-for-byte the same construction chronos-honeypot and krechill used
before this package existed, so existing stored chains still verify.

Honest scope (unchanged): this proves a chain is internally self-consistent.
For proof to an outside party, anchor the head hash with receipts.try_anchor().
"""
from __future__ import annotations

import hashlib
from typing import Iterable

GENESIS_HASH = "0" * 64


def fmt_float(x: float) -> str:
    """Fixed float formatting, so the same value hashes the same everywhere."""
    return f"{x:.6f}"


def chain_hash(fields: Iterable[str], prev_hash: str) -> str:
    payload = "|".join([*fields, prev_hash])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
