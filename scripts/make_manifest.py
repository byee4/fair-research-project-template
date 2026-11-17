#!/usr/bin/env python3
"""Create/verify an md5 manifest for raw or reference data (FAIR: Findable + Reusable).

make_manifest.py create data/raw --source "IGM order 12345" > data/raw/MANIFEST.tsv
make_manifest.py verify data/raw/MANIFEST.tsv           # exit 1 on any mismatch
"""

import argparse
import csv
import datetime as dt
import hashlib
import sys
from pathlib import Path


def md5(p: Path) -> str:
    h = hashlib.md5()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


ap = argparse.ArgumentParser()
sub = ap.add_subparsers(dest="cmd", required=True)
c = sub.add_parser("create")
c.add_argument("dir")
c.add_argument("--source", required=True, help="core facility order, collaborator, accession")
c.add_argument("--glob", default="**/*", help="see raw_globs in modules/<assay>/module.yaml")
c.add_argument("--append", help="append rows to this manifest (header written only if new/empty)")
v = sub.add_parser("verify")
v.add_argument("manifest")
a = ap.parse_args()

if a.cmd == "create":
    out = open(a.append, "a", newline="") if a.append else sys.stdout
    w = csv.writer(out, delimiter="\t")
    if not a.append or Path(a.append).stat().st_size == 0:
        w.writerow(["path", "md5", "bytes", "source", "received_utc"])
    now = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
    for p in sorted(Path(a.dir).glob(a.glob)):
        if not p.is_file() or p.name in {"MANIFEST.tsv", "README.md"}:
            continue
        w.writerow([str(p), md5(p), p.stat().st_size, a.source, now])
else:
    bad = 0
    with open(a.manifest) as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            p = Path(row["path"])
            if not p.exists():
                print(f"MISSING {p}", file=sys.stderr)
                bad += 1
            elif md5(p) != row["md5"]:
                print(f"CHECKSUM MISMATCH {p}", file=sys.stderr)
                bad += 1
    print("manifest OK" if not bad else f"{bad} problem(s)")
    sys.exit(1 if bad else 0)
