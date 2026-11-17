"""Custom-skeleton contract tests: lineage must show counts came from dedup BAMs, merged
groups must reach the QC report, stage names must be the declared ones."""

import json
from pathlib import Path

import pytest
import yaml
from check_contracts import CONTRACTS, dynamic, static
from conftest import ROOT

C = yaml.safe_load(CONTRACTS.read_text())
SHEET = ROOT / "tests/fixtures/mini/samples.tsv"
SIDS = ["CTRL_1", "CTRL_2", "KD_1", "KD_2"]


def _tsv(path: Path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(["\t".join(header)] + ["\t".join(map(str, r)) for r in rows]) + "\n")


def _lineage(path: Path, stage, input_stages):
    Path(str(path) + ".lineage.json").write_text(
        json.dumps({"output": str(path), "stage": stage, "inputs": [{"path": "x", "stage": s} for s in input_stages]})
    )


@pytest.fixture
def good_results(tmp_path):
    res = tmp_path / "results"
    _tsv(res / "counts/counts_matrix.tsv", ["gene_id"] + SIDS, [["G1", 1, 2, 3, 4], ["G2", 5, 6, 7, 8]])
    _lineage(res / "counts/counts_matrix.tsv", "counts", ["dedup"])
    for g in ["CTRL", "KD"]:
        p = res / f"merged/{g}.bedgraph"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("chr22\t0\t10\t1\n")
        _lineage(p, "merged", ["dedup"])
    qc = [[s, st, 100, 90, 90.0, 0.1] for s in SIDS for st in ["raw", "trimmed", "aligned", "filtered", "dedup"]]
    qc += [["CTRL", "dedup", 200, 180, "NA", "NA"], ["KD", "dedup", 200, 180, "NA", "NA"]]
    hdr = ["sample_id", "stage", "total_reads", "mapped_reads", "pct_mapped", "dup_rate"]
    _tsv(res / "qc/qc_summary.tsv", hdr, qc)
    _lineage(res / "qc/qc_summary.tsv", "qc", ["raw", "trimmed", "aligned", "filtered", "dedup"])
    _tsv(res / "diff/diff_results.tsv", ["gene_id", "log2fc", "pvalue", "padj"], [["G1", 1.2, 0.001, 0.01]])
    _lineage(res / "diff/diff_results.tsv", "diff", ["counts"])
    return res


def test_static():
    assert static(C) == []


def test_good_results_pass(good_results):
    assert dynamic(C, good_results, SHEET) == []


def test_counts_from_wrong_stage_fails(good_results):
    side = good_results / "counts/counts_matrix.tsv.lineage.json"
    rec = json.loads(side.read_text())
    rec["inputs"] = [{"path": "x", "stage": "aligned"}]
    side.write_text(json.dumps(rec))
    assert any("derived from stage" in e for e in dynamic(C, good_results, SHEET))


def test_merged_group_missing_from_report_fails(good_results):
    p = good_results / "qc/qc_summary.tsv"
    p.write_text("\n".join(ln for ln in p.read_text().splitlines() if not ln.startswith("KD\t")) + "\n")
    assert any("groups missing" in e for e in dynamic(C, good_results, SHEET))


def test_unknown_stage_name_fails(good_results):
    p = good_results / "qc/qc_summary.tsv"
    p.write_text(p.read_text().replace("\tfiltered\t", "\tpostfilter\t", 1))
    assert any("unknown stage names" in e for e in dynamic(C, good_results, SHEET))
