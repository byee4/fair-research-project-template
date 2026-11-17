#!/usr/bin/env python3
"""Validate a sample sheet against the core schema + the installed assay schema
(schemas/samplesheet.assay.schema.json, if present) + cross-row rules
(schemas/samplesheet.rules.yaml). Exit 1 on any error.

  validate_samplesheet.py [SHEET ...] [--check-files]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


def load_schema(schema_dir: Path = SCHEMAS) -> dict:
    core = json.loads((schema_dir / "samplesheet.core.schema.json").read_text())
    assay_p = schema_dir / "samplesheet.assay.schema.json"
    if not assay_p.exists():
        return core
    assay = json.loads(assay_p.read_text())
    return {"type": "array", "items": {"allOf": [core["items"], assay["items"]]}}


def load_rules(schema_dir: Path = SCHEMAS) -> dict:
    p = schema_dir / "samplesheet.rules.yaml"
    return yaml.safe_load(p.read_text()) if p.exists() else {}


def integer_fields(schema: dict) -> set[str]:
    items = schema["items"]
    parts = items.get("allOf", [items])
    return {k for part in parts for k, v in part.get("properties", {}).items() if v.get("type") == "integer"}


def load(path: Path, ints: set[str]) -> list[dict]:
    delim = "," if path.suffix == ".csv" else "\t"
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter=delim))
    for r in rows:
        for k in list(r):
            if r[k] in ("", None):
                del r[k]
            elif k in ints:
                try:
                    r[k] = int(r[k])
                except ValueError:
                    pass
    return rows


def key(r: dict, cols: list[str]):
    return tuple(r.get(c) for c in cols)


def apply_rules(rows: list[dict], rules: dict) -> list[str]:
    errs = []
    for cols in rules.get("unique", []):
        cols = [cols] if isinstance(cols, str) else cols
        c = Counter(key(r, cols) for r in rows if all(r.get(x) is not None for x in cols))
        errs += [f"duplicate {'/'.join(cols)} {k}" for k, n in c.items() if n > 1]
    for col in rules.get("all_or_none", []):
        has = {col in r for r in rows}
        if len(has) > 1:
            errs.append(f"column '{col}' is filled for some rows but not others (e.g. mixed single/paired-end)")
    for spec in rules.get("consistent_within", []):
        seen = defaultdict(set)
        for r in rows:
            if r.get(spec["by"]):
                seen[r[spec["by"]]].add(key(r, spec["columns"]))
        for g, vals in seen.items():
            if len(vals) > 1:
                errs.append(f"{spec['by']} {g} mixes incompatible {spec['columns']}: {sorted(map(str, vals))}")
    for cols in rules.get("consistent_all", []):
        vals = {r.get(cols) for r in rows}
        if len(vals) > 1:
            errs.append(
                f"'{cols}' must be identical across all rows to compare samples; found {sorted(map(str, vals))}"
            )
    for spec in rules.get("min_per_value", []):
        distinct = spec.get("distinct")
        seen = defaultdict(set)
        for i, r in enumerate(rows):
            seen[r.get(spec["column"])].add(r.get(distinct) if distinct else i)
        unit = f"distinct {distinct}" if distinct else "row(s)"
        for v, ids in seen.items():
            if len(ids) < spec["min"]:
                errs.append(f"{spec['column']}={v} has {len(ids)} {unit}; design requires >= {spec['min']}")
    return errs


def check(path: Path, schema_dir: Path = SCHEMAS, check_files: bool = False, root: Path = ROOT) -> list[str]:
    schema = load_schema(schema_dir)
    rows = load(path, integer_fields(schema))
    if not rows:
        return [f"{path}: no rows"]
    errs = [
        f"row {'/'.join(map(str, e.absolute_path))}: {e.message}"
        for e in Draft202012Validator(schema).iter_errors(rows)
    ]
    rules = load_rules(schema_dir)
    errs += apply_rules(rows, rules)
    if check_files:
        for r in rows:
            for col in rules.get("path_columns", []):
                for p in str(r.get(col, "")).split():
                    if p and not (Path(p) if Path(p).is_absolute() else root / p).exists():
                        errs.append(f"{r.get('sample_id')}: {col} path not found: {p}")
    return errs


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("sheets", nargs="*")
    ap.add_argument("--check-files", action="store_true", help="also check that path columns exist")
    a = ap.parse_args(argv)
    paths = [Path(p) for p in a.sheets] or [ROOT / "config" / "samples.tsv"]
    bad = 0
    for p in paths:
        if not p.exists():
            print(f"{p}: not found (run the project interview / init_project.py first)", file=sys.stderr)
            bad += 1
            continue
        errs = check(p, check_files=a.check_files)
        for e in errs:
            print(f"{p}: {e}", file=sys.stderr)
        bad += bool(errs)
    if not bad:
        print("sample sheet OK")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
