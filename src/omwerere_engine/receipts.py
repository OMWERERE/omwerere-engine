"""
Tamper-evident verification receipts.

Real, working part (no network, no dependency, always available):
canonicalize the request + result into a deterministic JSON string, then
hash it with SHA-256. Anyone holding the original inputs and the hash can
recompute it and confirm the verdict hasn't been silently altered after
the fact. Only the hash ever leaves this module — the caller's actual
text is never sent anywhere by this file.

Optional, honestly-labeled part (needs network, may not always succeed):
submit that hash to a public OpenTimestamps calendar server, which anchors
it into the Bitcoin blockchain. This does NOT happen instantly — a
calendar server first returns a *pending* attestation; the underlying
Bitcoin transaction needs real confirmations (typically 10 minutes to a
few hours) before the timestamp can be upgraded into a complete,
independently verifiable proof. Upgrading a pending proof isn't built yet
(see README "Next" section) — this module only handles the submission
step. Anchoring status is reported honestly rather than pretending it's
instant or guaranteed:

  - "not_requested" — anchoring wasn't asked for (the default)
  - "pending"        — submitted to a calendar server, awaiting Bitcoin
                        confirmation
  - "unavailable"    — anchoring was requested but no calendar server
                        could be reached (network blocked, offline,
                        timeout, etc.) — the local hash is still valid
                        and returned regardless of this
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field

DEFAULT_CALENDAR_URLS = [
    "https://alice.btc.calendar.opentimestamps.org",
    "https://bob.btc.calendar.opentimestamps.org",
]


def canonical_payload(
    text: str,
    rules: list[tuple[str, list[str]]],
    default_label: str,
    result_label: str,
) -> str:
    """Deterministic JSON representation of what a receipt commits to."""
    normalized_rules = [[label, sorted(markers)] for label, markers in rules]
    payload = {
        "text": text,
        "rules": normalized_rules,
        "default_label": default_label,
        "result_label": result_label,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_receipt_hash(
    text: str,
    rules: list[tuple[str, list[str]]],
    default_label: str,
    result_label: str,
) -> str:
    """SHA-256 hex digest of the canonical payload. Deterministic, free, offline."""
    payload = canonical_payload(text, rules, default_label, result_label)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class Receipt:
    hash: str
    algorithm: str = "sha256"
    created_at: float = field(default_factory=time.time)
    anchor_status: str = "not_requested"
    anchor_detail: str | None = None
    ots_proof_hex: str | None = None  # serialized pending OTS Timestamp, if anchored

    def to_dict(self) -> dict:
        return {
            "hash": self.hash,
            "algorithm": self.algorithm,
            "created_at": self.created_at,
            "anchor_status": self.anchor_status,
            "anchor_detail": self.anchor_detail,
            "ots_proof_hex": self.ots_proof_hex,
        }


def try_anchor(receipt_hash: str, timeout: float = 3.0) -> Receipt:
    """Attempt to submit the receipt hash to a public OpenTimestamps
    calendar server. Never raises — any failure (network blocked, library
    missing, timeout, server error) is reported honestly via
    anchor_status="unavailable" rather than silently degrading to a fake
    success. Deliberately broad exception handling here is the point: this
    is best-effort network I/O layered on top of a hash that's already
    valid on its own.
    """
    receipt = Receipt(hash=receipt_hash, anchor_status="pending")
    try:
        from opentimestamps.calendar import RemoteCalendar
        from opentimestamps.core.serialize import BytesSerializationContext
    except Exception as exc:  # noqa: BLE001
        receipt.anchor_status = "unavailable"
        receipt.anchor_detail = f"anchoring library unavailable: {exc}"
        return receipt

    digest = bytes.fromhex(receipt_hash)
    last_error: Exception | None = None
    for url in DEFAULT_CALENDAR_URLS:
        try:
            calendar = RemoteCalendar(url)
            timestamp = calendar.submit(digest, timeout=timeout)
            ctx = BytesSerializationContext()
            timestamp.serialize(ctx)
            receipt.ots_proof_hex = ctx.getbytes().hex()
            receipt.anchor_detail = f"submitted to {url}, awaiting Bitcoin confirmation"
            return receipt
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            continue

    receipt.anchor_status = "unavailable"
    receipt.anchor_detail = f"no calendar server reachable: {last_error}"
    return receipt


def try_upgrade(receipt_hash: str, ots_proof_hex: str, timeout: float = 3.0) -> Receipt:
    """
    The "/receipts/upgrade" step named as "Next, not done yet" in README —
    built now. Asks the calendar servers whether a pending anchor (from
    try_anchor) has since been confirmed into a complete, Bitcoin-anchored
    proof.

      - "confirmed"    — at least one calendar returned a timestamp that now
                          contains a BitcoinBlockHeaderAttestation. The
                          re-serialized, merged proof is returned in
                          ots_proof_hex.
      - "pending"       — reachable, but still awaiting confirmation — no
                          Bitcoin attestation yet. Try again later.
      - "unavailable"   — could not reach a calendar server, or the supplied
                          proof/hash couldn't be parsed. The original
                          ots_proof_hex is returned unchanged, never
                          discarded.

    Deliberately does NOT independently verify the Bitcoin attestation
    against real blockchain data (checking the merkle path against an
    actual block header) — that would be a further, separate step. A
    "confirmed" status here means "the calendar server vouches for it,"
    which is the standard OpenTimestamps trust model, not independent
    on-chain verification. Same never-raises, honestly-degrades contract
    as try_anchor.
    """
    receipt = Receipt(hash=receipt_hash, anchor_status="pending", ots_proof_hex=ots_proof_hex)
    try:
        from opentimestamps.calendar import RemoteCalendar
        from opentimestamps.core.notary import BitcoinBlockHeaderAttestation
        from opentimestamps.core.serialize import BytesDeserializationContext, BytesSerializationContext
        from opentimestamps.core.timestamp import Timestamp
    except Exception as exc:  # noqa: BLE001
        receipt.anchor_status = "unavailable"
        receipt.anchor_detail = f"anchoring library unavailable: {exc}"
        return receipt

    try:
        msg = bytes.fromhex(receipt_hash)
        parse_ctx = BytesDeserializationContext(bytes.fromhex(ots_proof_hex))
        timestamp = Timestamp.deserialize(parse_ctx, msg)
    except Exception as exc:  # noqa: BLE001
        receipt.anchor_status = "unavailable"
        receipt.anchor_detail = f"could not parse existing proof: {exc}"
        return receipt

    last_error: Exception | None = None
    reached_any_calendar = False
    for url in DEFAULT_CALENDAR_URLS:
        try:
            calendar = RemoteCalendar(url)
            calendar_timestamp = calendar.get_timestamp(msg, timeout=timeout)
            if calendar_timestamp is not None:
                timestamp.merge(calendar_timestamp)
                reached_any_calendar = True
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            continue

    if not reached_any_calendar:
        receipt.anchor_status = "unavailable"
        receipt.anchor_detail = f"no calendar server reachable: {last_error}"
        return receipt

    has_bitcoin_attestation = any(
        isinstance(attestation, BitcoinBlockHeaderAttestation)
        for _, attestation in timestamp.all_attestations()
    )

    out_ctx = BytesSerializationContext()
    timestamp.serialize(out_ctx)
    receipt.ots_proof_hex = out_ctx.getbytes().hex()

    if has_bitcoin_attestation:
        receipt.anchor_status = "confirmed"
        receipt.anchor_detail = "confirmed by calendar server with a Bitcoin block attestation"
    else:
        receipt.anchor_status = "pending"
        receipt.anchor_detail = "reachable, still awaiting Bitcoin confirmation"

    return receipt
