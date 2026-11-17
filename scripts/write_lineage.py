#!/usr/bin/env python3
"""Write a lineage sidecar for an output file (engine-agnostic).

Snakemake:  shell: "... && python3 scripts/write_lineage.py --out {output} --stage counts \
              --inputs {input} --input-stage dedup"
Nextflow:   script: "... ; write_lineage.py --out counts_matrix.tsv --stage counts --inputs ${bams} --input-stage dedup"
"""

import argparse
import hashlib
import json
from pathlib import Path


def md5(p: Path) -> str | None:
    if not p.is_file():
        return None
    h = hashlib.md5()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--stage", required=True)
ap.add_argument("--inputs", nargs="+", required=True)
ap.add_argument("--input-stage", required=True)
ap.add_argument("--param", action="append", default=[], help="key=value")
a = ap.parse_args()
out = Path(a.out)
rec = {
    "output": str(out),
    "output_md5": md5(out),
    "stage": a.stage,
    "inputs": [{"path": i, "stage": a.input_stage, "md5": md5(Path(i))} for i in a.inputs],
    "params": dict(p.split("=", 1) for p in a.param),
}
Path(str(out) + ".lineage.json").write_text(json.dumps(rec, indent=2))
