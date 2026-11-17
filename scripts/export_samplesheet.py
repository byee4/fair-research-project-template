#!/usr/bin/env python3
"""Convert the project's FAIR sample sheet (config/samples.tsv) into the input format a
community pipeline expects, using the mapping in workflow/pipeline.yaml (from the assay module).
One master sheet stays the source of truth; pipeline sheets are generated, never hand-edited.

  export_samplesheet.py [--out workflow/pipeline_samplesheet.csv]
"""

import argparse
import collections
import csv
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

ap = argparse.ArgumentParser()
ap.add_argument("--sheet", default=str(ROOT / "config" / "samples.tsv"))
ap.add_argument("--pipeline", default=str(ROOT / "workflow" / "pipeline.yaml"))
ap.add_argument("--out")
a = ap.parse_args()

pipe = yaml.safe_load(Path(a.pipeline).read_text())
spec = pipe.get("samplesheet_export")
if not spec:
    sys.exit(f"{pipe['name']} uses config/samples.tsv directly; nothing to export")
with open(a.sheet, newline="") as fh:
    rows = list(csv.DictReader(fh, delimiter="\t"))
if spec.get("filter"):
    col, val = spec["filter"].split("=")
    rows = [r for r in rows if r.get(col) == val]
out = Path(a.out or ROOT / "workflow" / spec.get("filename", "pipeline_samplesheet.csv"))
delim = "\t" if spec.get("format") == "tsv" else ","
with open(out, "w", newline="") as fh:
    w = csv.writer(fh, delimiter=delim)
    w.writerow(list(spec["columns"]))
    for r in rows:
        w.writerow(
            [
                tmpl.format_map(collections.defaultdict(str, {k: (v or "") for k, v in r.items()}))
                for tmpl in spec["columns"].values()
            ]
        )
print(f"wrote {out} ({len(rows)} rows) for {pipe['name']}")
