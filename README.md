# omwerere-engine

The shared spine for every Omwerere tributary (Krechill, KREDUCATION, Chronos Honeypot, Verifier API).
Built once here, installed everywhere, instead of copying files between repos.

| Module | Was copied into | Now |
|---|---|---|
| `trivium_core` | verifier-api, kreducation, omwerere-org backend (3 copies) | one home |
| `chain` | chronos-honeypot, krechill (2 diverged copies, same construction) | one construction; existing chains still verify |
| `receipts` | verifier-api, chronos-honeypot (2 copies) | one home |

Rere Gate stays its own package (`omwerere-safety-gate`) because it has clinical sign-off rules.

```
pip install -e .
python -m pytest -q
```

Migration status lives in `../STACK-ALIGNMENT-2026-10-14.md`.
