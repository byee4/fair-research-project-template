#!/usr/bin/env python3
"""Enforce calibrated claims: a claim's level must be supported by passed gates,
and any claim with a passed gate must point to evidence that exists."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "observation": ["execution", "design"],
    "statistical": ["execution", "design", "inference"],
    "mechanism": ["execution", "design", "inference", "biological"],
    "clinical": ["execution", "design", "inference", "biological", "external"],
}
GATE_VALUES = {"pass", "fail", "pending", "n/a"}


def allowed_level(gates: dict) -> str | None:
    best = None
    for level, req in REQUIRED.items():
        if all(gates.get(g) == "pass" for g in req):
            best = level
    return best


def main(path: str = str(ROOT / "claims" / "claims.yaml")) -> int:
    data = yaml.safe_load(Path(path).read_text()) or {}
    errs = []
    for c in data.get("claims", []):
        cid = c.get("id", "?")
        gates = c.get("gates", {})
        if c.get("level") not in REQUIRED:
            errs.append(f"{cid}: unknown level {c.get('level')}")
            continue
        for g, v in gates.items():
            if v not in GATE_VALUES:
                errs.append(f"{cid}: gate {g} has invalid value {v}")
        if not c.get("criteria_set_before_results"):
            errs.append(f"{cid}: validation criteria must be set before results are interpreted")
        any_pass = any(v == "pass" for v in gates.values())
        if any_pass:
            for e in c.get("evidence", []):
                if not (ROOT / e).exists():
                    errs.append(f"{cid}: evidence file missing: {e}")
            for d in c.get("decisions", []):
                if not (ROOT / d).exists():
                    errs.append(f"{cid}: decision record missing: {d}")
        status = "pending" if not any_pass else "active"
        if status == "active":
            ok = allowed_level(gates)
            order = list(REQUIRED)
            if ok is None or order.index(c["level"]) > order.index(ok):
                errs.append(
                    f"{cid}: claimed level '{c['level']}' exceeds what passed gates support "
                    f"('{ok or 'none — EXPLORATORY only'}'). Downgrade language or pass gates."
                )
            if c["level"] in ("mechanism", "clinical") and not c.get("reviewer"):
                errs.append(f"{cid}: {c['level']} claims need a named human reviewer")
    for e in errs:
        print(e, file=sys.stderr)
    if not errs:
        print("claims OK")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
