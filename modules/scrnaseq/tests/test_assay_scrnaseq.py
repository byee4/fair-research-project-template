"""scRNA-seq pitfalls, encoded as tests (installed to tests/assay/)."""

import copy

import pytest
from conftest import ROOT, batch_confounded, read_rows, write_rows
from validate_samplesheet import check

SHEET = ROOT / "config/samples.tsv"
BASE = read_rows(SHEET)


def test_project_sheet_valid():
    assert check(SHEET) == []


def test_batch_not_confounded():
    assert not batch_confounded(BASE)


def mutated(fn):
    rows = copy.deepcopy(BASE)
    fn(rows)
    return rows


def same_donor(rs):
    for r in rs:
        if r["condition"] == rs[0]["condition"]:
            r["donor"] = rs[0]["donor"]


@pytest.mark.parametrize(
    "fn, needle",
    [
        (same_donor, "distinct donor"),  # cells/libraries from 1 donor
        (lambda rs: rs[0].__setitem__("protocol", "10XV2"), "mixes incompatible"),  # lane with other chemistry
        (lambda rs: [r.__setitem__("protocol", "10XV2") for r in rs[:2]], "identical across all rows"),
        (lambda rs: rs[0].__setitem__("material", "nuclei"), "mixes incompatible"),
        (lambda rs: rs[0].pop("fastq_2"), "'fastq_2' is a required property"),
        (lambda rs: rs.append({**rs[0]}), "duplicate sample_id/lane"),
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
    assert not todo
