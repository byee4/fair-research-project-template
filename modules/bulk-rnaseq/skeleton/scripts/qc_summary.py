#!/usr/bin/env python3
"""Build qc/qc_summary.tsv: one row per (sample, stage) + one row per merge group.

Contract (contracts/data_products.yaml#qc_summary): stage names must be exactly
raw, trimmed, aligned, filtered, dedup; each stage's numbers must come from that
stage's files ONLY (never mix counts across filtering stages).
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import pandas as pd

STAGES = ["raw", "trimmed", "aligned", "filtered", "dedup"]


def flagstat(bam: Path, threads: int) -> tuple[int, int]:
    out = subprocess.run(
        ["samtools", "flagstat", "-@", str(threads), "-O", "json", str(bam)], check=True, capture_output=True, text=True
    ).stdout
    d = json.loads(out)["QC-passed reads"]
    return d["primary"], d["primary mapped"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--threads", type=int, default=1)
    a = ap.parse_args()
    od = Path(a.outdir)
    sheet = pd.read_csv(a.sheet, sep="\t", dtype=str).fillna("")
    rows = []
    for s in sheet["sample_id"]:
        fp = json.loads((od / "trimmed" / f"{s}.fastp.json").read_text())["summary"]
        rows.append(
            dict(
                sample_id=s,
                stage="raw",
                total_reads=fp["before_filtering"]["total_reads"],
                mapped_reads="NA",
                pct_mapped="NA",
                dup_rate="NA",
            )
        )
        rows.append(
            dict(
                sample_id=s,
                stage="trimmed",
                total_reads=fp["after_filtering"]["total_reads"],
                mapped_reads="NA",
                pct_mapped="NA",
                dup_rate="NA",
            )
        )
        totals = {}
        for st in ["aligned", "filtered", "dedup"]:
            tot, mapped = flagstat(od / st / f"{s}.bam", a.threads)
            totals[st] = tot
            # dup_rate: markdup -r removes duplicates, so rate = 1 - dedup/filtered (same sample only)
            dr = round(1 - tot / totals["filtered"], 4) if st == "dedup" and totals.get("filtered") else "NA"
            rows.append(
                dict(
                    sample_id=s,
                    stage=st,
                    total_reads=tot,
                    mapped_reads=mapped,
                    pct_mapped=round(100 * mapped / tot, 2) if tot else 0,
                    dup_rate=dr,
                )
            )
    for g in sorted(set(sheet["group"]) - {""}):
        members = sheet.loc[sheet["group"] == g, "sample_id"]
        sub = [r for r in rows if r["sample_id"] in set(members) and r["stage"] == "dedup"]
        rows.append(
            dict(
                sample_id=g,
                stage="dedup",
                total_reads=sum(int(r["total_reads"]) for r in sub),
                mapped_reads=sum(int(r["mapped_reads"]) for r in sub),
                pct_mapped="NA",
                dup_rate="NA",
            )
        )
    pd.DataFrame(rows).to_csv(a.out, sep="\t", index=False)
    Path(a.out + ".lineage.json").write_text(
        json.dumps(
            {"output": a.out, "stage": "qc", "inputs": [{"path": str(od / st), "stage": st} for st in STAGES]}, indent=2
        )
    )


if __name__ == "__main__":
    main()
