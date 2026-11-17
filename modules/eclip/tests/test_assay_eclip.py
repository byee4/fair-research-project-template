"""eCLIP pitfalls, encoded as tests (installed to tests/assay/)."""

import copy

import pytest
from conftest import ROOT, read_rows, write_rows
from validate_samplesheet import check

SHEET = ROOT / "config/samples.tsv"
BASE = read_rows(SHEET)


def test_project_sheet_valid():
    assert check(SHEET) == []


def mutated(fn):
    rows = copy.deepcopy(BASE)
    fn(rows)
    return rows


@pytest.mark.parametrize(
    "fn, needle",
    [
        (lambda rs: rs[0].pop("input_fastq"), "'input_fastq' is a required property"),  # no SMInput
        (lambda rs: rs.pop(1), "design requires >= 2"),  # 1 CLIP replicate
        (lambda rs: rs[1].__setitem__("rbp_target", "HGNC:12345"), "mixes incompatible"),  # 2 RBPs, one group
        (lambda rs: rs[1].__setitem__("antibody", "other antibody"), "mixes incompatible"),
        (lambda rs: rs[0].pop("clip_adapter"), "'clip_adapter' is a required property"),
        (lambda rs: rs[0].__setitem__("rbp_target", "RBFOX2"), "does not match"),  # symbol, not HGNC id
        (lambda rs: rs[1].__setitem__("replicate", "1"), "duplicate group/replicate"),
    ],
)
def test_bad_sheets_rejected(tmp_path, fn, needle):
    errs = check(write_rows(tmp_path, mutated(fn)))
    assert any(needle in e for e in errs), errs


def test_assay_term_resolved_once_data_arrive():
    manifest = ROOT / "data/raw/MANIFEST.tsv"
    has_data = manifest.exists() and len(manifest.read_text().strip().splitlines()) > 1
    todo = [r["sample_id"] for r in BASE if r.get("assay", "").startswith("TODO:")]
    if todo and not has_data:
        pytest.skip(f"assay ontology term unresolved for {todo}; look it up in OLS before data arrive")
    assert not todo, f"resolve assay ontology terms for {todo} (OLS: https://www.ebi.ac.uk/ols4)"


def test_skipper_manifest_export(tmp_path):
    """The exported Skipper manifest must carry every CLIP replicate with its input."""
    import subprocess
    import sys

    import yaml

    pipe = yaml.safe_load((ROOT / "workflow/pipeline.yaml").read_text())
    if pipe["id"] != "yeolab/skipper":
        pytest.skip("pipeline is not Skipper")
    out = tmp_path / "m.csv"
    subprocess.run([sys.executable, str(ROOT / "scripts/export_samplesheet.py"), "--out", str(out)], check=True)
    rows = out.read_text().strip().splitlines()
    assert rows[0].split(",")[:2] == ["Sample", "Experiment"]
    assert len(rows) - 1 == len(BASE)
    assert all(",," not in r for r in rows[1:]), "empty manifest field"
