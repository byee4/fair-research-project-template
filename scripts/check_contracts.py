#!/usr/bin/env python3
"""Check data-product contracts (assay-agnostic engine; assay modules supply the contract file).

  check_contracts.py                                     static: contract file well-formed
  check_contracts.py --results DIR [--samplesheet TSV]   dynamic: real outputs satisfy contracts

Product fields (all optional except path):
  path: "counts/{sample}.tsv"   templates: {sample} (sample_id), {group}; "*" globs (>=1 match)
  one_per: sample | group       expand the path per sample / per group
  format: tsv | csv | h5ad | dir | zarr | file   (inferred from suffix if omitted)
  stage / must_derive_from / require_lineage     lineage sidecars (<output>.lineage.json)
  required_columns, columns_include_all: sample_id, min_rows, row_id_column,
  rows_cover: [sample_id, group], stage_column_values, value_ranges: {col: [lo, hi]}
  obs_required, obs_sample_column (h5ad)        required_entries (dir/zarr)
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "data_products.yaml"


def read_table(p: Path) -> list[dict]:
    delim = "," if p.suffix == ".csv" else "\t"
    with open(p, newline="") as fh:
        return list(csv.DictReader(fh, delimiter=delim))


def fmt(p: dict, path: str) -> str:
    if p.get("format"):
        return p["format"]
    for suf, f in ((".tsv", "tsv"), (".txt", "tsv"), (".csv", "csv"), (".h5ad", "h5ad"), (".zarr", "zarr")):
        if path.endswith(suf):
            return f
    return "file"


def static(c: dict) -> list[str]:
    errs = []
    stages = set(c.get("stages", {}))
    for name, p in (c.get("products") or {}).items():
        if "path" not in p:
            errs.append(f"{name}: missing 'path'")
        if p.get("stage") and p["stage"] not in stages:
            errs.append(f"{name}: stage '{p['stage']}' not declared in stages")
        for s in p.get("must_derive_from", []):
            if s not in stages:
                errs.append(f"{name}: must_derive_from '{s}' not declared in stages")
        if p.get("require_lineage") and not p.get("must_derive_from"):
            errs.append(f"{name}: require_lineage set but must_derive_from is empty")
        if p.get("one_per") not in (None, "sample", "group"):
            errs.append(f"{name}: one_per must be 'sample' or 'group'")
    return errs


def lineage_errs(out: Path, allowed: list[str]) -> list[str]:
    side = Path(str(out) + ".lineage.json")
    if not side.exists():
        return [f"{out}: missing lineage sidecar {side.name}"]
    bad = {i["stage"] for i in json.loads(side.read_text()).get("inputs", [])} - set(allowed)
    return [f"{out}: derived from stage(s) {sorted(bad)}, contract allows {allowed}"] if bad else []


def table_errs(name: str, p: dict, rows: list[dict], sids: list[str], groups: list[str]) -> list[str]:
    errs = []
    cols = list(rows[0].keys()) if rows else []
    errs += [f"{name}: missing column '{c}'" for c in p.get("required_columns", []) if c not in cols]
    if p.get("columns_include_all") == "sample_id":
        miss = [s for s in sids if s not in cols]
        if miss:
            errs.append(f"{name}: missing sample columns {miss}")
    if len(rows) < p.get("min_rows", 0):
        errs.append(f"{name}: {len(rows)} rows < min_rows {p['min_rows']}")
    if vals := p.get("stage_column_values"):
        seen = {r.get("stage") for r in rows}
        if extra := seen - set(vals):
            errs.append(f"{name}: unknown stage names {sorted(extra)}")
        if missing := set(vals) - seen:
            errs.append(f"{name}: stages absent from report {sorted(missing)}")
    idcol = p.get("row_id_column", "sample_id")
    ids = {r.get(idcol) for r in rows}
    for what, expected in (("sample_id", sids), ("group", groups)):
        if what in p.get("rows_cover", []):
            miss = [x for x in expected if x not in ids]
            if miss:
                errs.append(f"{name}: {what}s missing from table {miss}")
    for col, (lo, hi) in (p.get("value_ranges") or {}).items():
        for i, r in enumerate(rows):
            v = r.get(col)
            if v in (None, "", "NA"):
                continue
            try:
                f = float(v)
            except ValueError:
                errs.append(f"{name}: row {i} {col}={v!r} not numeric")
                break
            if not lo <= f <= hi:
                errs.append(f"{name}: row {i} {col}={f} outside [{lo},{hi}]")
                break
    return errs


def h5ad_errs(name: str, p: dict, path: Path, sids: list[str]) -> list[str]:
    try:
        import anndata
    except ImportError:
        return [f"{name}: install 'anndata' to check {path.name} (skipping is not allowed)"]
    ad = anndata.read_h5ad(path, backed="r")
    errs = [f"{name}: obs missing column '{c}'" for c in p.get("obs_required", []) if c not in ad.obs.columns]
    sc = p.get("obs_sample_column")
    if sc and sc in ad.obs.columns:
        miss = sorted(set(sids) - set(map(str, ad.obs[sc].unique())))
        if miss:
            errs.append(f"{name}: samples absent from obs['{sc}']: {miss}")
    if ad.n_obs < p.get("min_rows", 1):
        errs.append(f"{name}: only {ad.n_obs} observations")
    return errs


def dynamic(c: dict, results: Path, sheet: Path | None) -> list[str]:
    errs = []
    samples = read_table(sheet) if sheet and sheet.exists() else []
    sids = [s["sample_id"] for s in samples]
    groups = sorted({s["group"] for s in samples if s.get("group")})
    for name, p in (c.get("products") or {}).items():
        per = p.get("one_per")
        keys = sids if per == "sample" else groups if per == "group" else [None]
        if per and not keys:
            errs.append(f"{name}: one_per={per} but sample sheet has no {per}s")
        for k in keys:
            rel = p["path"].format(sample=k, group=k) if k else p["path"]
            targets = sorted(results.glob(rel)) if "*" in rel else [results / rel]
            if not targets or not targets[0].exists():
                errs.append(f"{name}: expected output missing: {results / rel}")
                continue
            for t in targets:
                errs += check_one(name, p, t, rel, k, sids, groups)
    return errs


def check_one(name: str, p: dict, t: Path, rel: str, k: str | None, sids: list[str], groups: list[str]) -> list[str]:
    errs = []
    if p.get("require_lineage"):
        errs += lineage_errs(t, p["must_derive_from"])
    f = fmt(p, rel)
    if f in ("tsv", "csv"):
        errs += table_errs(name, p, read_table(t), [] if k else sids, [] if k else groups)
    elif f == "h5ad":
        errs += h5ad_errs(name, p, t, [k] if k else sids)
    elif f in ("dir", "zarr"):
        if not t.is_dir():
            errs.append(f"{name}: {t} should be a directory")
        errs += [f"{name}: {t} missing entry '{e}'" for e in p.get("required_entries", []) if not (t / e).exists()]
    elif t.is_file() and t.stat().st_size == 0:
        errs.append(f"{name}: {t} is empty")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contracts", default=str(CONTRACTS))
    ap.add_argument("--results")
    ap.add_argument("--samplesheet", default=str(ROOT / "config" / "samples.tsv"))
    a = ap.parse_args()
    c = yaml.safe_load(Path(a.contracts).read_text()) or {}
    errs = static(c)
    if a.results:
        errs += dynamic(c, Path(a.results), Path(a.samplesheet))
    for e in errs:
        print(e, file=sys.stderr)
    if not errs:
        print("contracts OK")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
