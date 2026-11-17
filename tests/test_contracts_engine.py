"""The contract checker itself (assay-agnostic), using an inline contract."""

import pytest
from check_contracts import dynamic, static

SHEET_ROWS = "sample_id\tgroup\nA\tG1\nB\tG1\nC\tG2\n"
C = {
    "stages": {"raw": {}, "quant": {}},
    "products": {
        "matrix": {
            "path": "m.tsv",
            "stage": "quant",
            "required_columns": ["feature_id"],
            "columns_include_all": "sample_id",
        },
        "per_sample": {"path": "per/{sample}.txt", "one_per": "sample"},
        "per_group": {"path": "grp/{group}", "one_per": "group", "format": "dir", "required_entries": ["x"]},
        "report": {"path": "qc/*report.html"},
        "qc": {"path": "qc.tsv", "rows_cover": ["sample_id"], "value_ranges": {"frac": [0, 1]}},
    },
}


@pytest.fixture
def res(tmp_path):
    (tmp_path / "s.tsv").write_text(SHEET_ROWS)
    r = tmp_path / "r"
    (r / "per").mkdir(parents=True)
    (r / "m.tsv").write_text("feature_id\tA\tB\tC\nf1\t1\t2\t3\n")
    for s in "ABC":
        (r / f"per/{s}.txt").write_text("ok")
    for g in ("G1", "G2"):
        (r / f"grp/{g}/x").mkdir(parents=True)
    (r / "qc").mkdir()
    (r / "qc/multiqc_report.html").write_text("<html>")
    (r / "qc.tsv").write_text("sample_id\tfrac\nA\t0.5\nB\t0.1\nC\t0.9\n")
    return r, tmp_path / "s.tsv"


def test_static_ok():
    assert static(C) == []


def test_static_bad_stage():
    assert static({"stages": {}, "products": {"x": {"path": "p", "stage": "nope"}}})


def test_good(res):
    assert dynamic(C, *res) == []


@pytest.mark.parametrize(
    "break_it, needle",
    [
        (lambda r: (r / "per/B.txt").unlink(), "expected output missing"),
        (lambda r: (r / "m.tsv").write_text("feature_id\tA\tB\nf1\t1\t2\n"), "missing sample columns"),
        (lambda r: (r / "grp/G2/x").rmdir(), "missing entry"),
        (lambda r: (r / "qc/multiqc_report.html").unlink(), "expected output missing"),
        (lambda r: (r / "qc.tsv").write_text("sample_id\tfrac\nA\t0.5\nB\t1.4\n"), "outside"),
        (lambda r: (r / "qc.tsv").write_text("sample_id\tfrac\nA\t0.5\nB\t0.4\n"), "missing from table"),
    ],
)
def test_breakage_detected(res, break_it, needle):
    r, s = res
    break_it(r)
    assert any(needle in e for e in dynamic(C, r, s))
