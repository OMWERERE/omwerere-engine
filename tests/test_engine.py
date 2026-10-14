"""The engine keeps the promises the tributaries relied on before it existed."""
import hashlib

from omwerere_engine.chain import GENESIS_HASH, chain_hash, fmt_float
from omwerere_engine.trivium_core import clamp, push_history, repeat_count
from omwerere_engine import receipts


def test_chain_matches_the_original_krechill_construction():
    old = hashlib.sha256("|".join(["n1", "auth_success", "ok", "1.000000", GENESIS_HASH]).encode()).hexdigest()
    assert chain_hash(["n1", "auth_success", "ok", fmt_float(1.0)], GENESIS_HASH) == old


def test_chain_matches_the_original_chronos_construction():
    parts = ["1.2.3.4", "/admin", fmt_float(0.5), "probe", "log", fmt_float(2.0)]
    old = hashlib.sha256("|".join(parts + [GENESIS_HASH]).encode()).hexdigest()
    assert chain_hash(parts, GENESIS_HASH) == old


def test_any_change_breaks_the_hash():
    a = chain_hash(["x", "y"], GENESIS_HASH)
    assert a != chain_hash(["x", "z"], GENESIS_HASH)
    assert a != chain_hash(["x", "y"], a)


def test_trivium_primitives_import():
    assert clamp(150) == 100.0 and clamp(-1) == 0.0
    h = push_history([], "a", 5)
    assert repeat_count(h, "a") >= 1


def test_receipts_import():
    assert hasattr(receipts, "compute_receipt_hash") and hasattr(receipts, "try_anchor")
