import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def read_rows(path):
    import csv

    with open(path, newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def write_rows(tmp_path, rows, name="samples.tsv"):
    cols = list(dict.fromkeys(k for r in rows for k in r))
    p = tmp_path / name
    p.write_text("\n".join(["\t".join(cols)] + ["\t".join(str(r.get(c, "")) for c in cols) for r in rows]) + "\n")
    return p


def batch_confounded(rows, cond="condition", batch="batch"):
    """True if every batch contains exactly one condition (and >1 batch exists)."""
    by_batch = {}
    for r in rows:
        if r.get(batch):
            by_batch.setdefault(r[batch], set()).add(r[cond])
    return len(by_batch) > 1 and all(len(v) == 1 for v in by_batch.values())
