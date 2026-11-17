"""Spatial transcriptomics pitfalls, encoded as tests (installed to tests/assay/)."""

import copy

import pytest
from conftest import ROOT, batch_confounded, read_rows, write_rows
from validate_samplesheet import check

SHEET = ROOT / "config/samples.tsv"
BASE = read_rows(SHEET)


def test_project_sheet_valid():
    assert check(SHEET) == []


def test_slide_batch_not_confounded():
    assert not batch_confounded(BASE), "each slide/batch holds one condition: slide effects can't be separated"


def mutated(fn):
    rows = copy.deepcopy(BASE)
    fn(rows)
    return rows


@pytest.mark.parametrize(
    "fn, needle",
    [
        # two sections from the same donor are not two replicates
        (lambda rs: rs[1].__setitem__("donor", rs[0]["donor"]), "distinct donor"),
        (lambda rs: rs[2].__setitem__("panel", "other_panel_v2"), "must be identical across all rows"),
        (lambda rs: rs[2].__setitem__("platform", "merscope"), "must be identical across all rows"),
        (lambda rs: rs[0].pop("donor"), "'donor' is a required property"),
        (lambda rs: rs[1].__setitem__("section_id", rs[0]["section_id"]), "duplicate section_id"),
    ],
)
def test_bad_sheets_rejected(tmp_path, fn, needle):
    errs = check(write_rows(tmp_path, mutated(fn)))
    assert any(needle in e for e in errs), errs


def test_imaging_platform_needs_panel_and_bundle(tmp_path):
    rows = [{**r, "platform": "xenium", "panel": "panelA"} for r in copy.deepcopy(BASE)]
    assert check(write_rows(tmp_path, rows)) == []
    rows[0].pop("panel")
    rows[1].pop("data_path")
    errs = check(write_rows(tmp_path, rows))
    assert any("'panel' is a required property" in e for e in errs), errs
    assert any("'data_path' is a required property" in e for e in errs), errs


def test_visium_raw_mode_needs_image(tmp_path):
    rows = [{**r, "data_path": "", "fastq_dir": f"data/raw/{r['sample_id']}"} for r in copy.deepcopy(BASE)]
    errs = check(write_rows(tmp_path, rows))
    assert any("image" in e or "cytaimage" in e or "anyOf" in e or "not valid" in e for e in errs), errs
    for r in rows:
        r["cytaimage"] = "data/raw/img.tif"
    assert check(write_rows(tmp_path, rows)) == []


def test_assay_term_resolved_once_data_arrive():
    """TODO:<name> assay terms are allowed while waiting for data, not after intake."""
    manifest = ROOT / "data/raw/MANIFEST.tsv"
    has_data = manifest.exists() and len(manifest.read_text().strip().splitlines()) > 1
    todo = [r["sample_id"] for r in BASE if r.get("assay", "").startswith("TODO:")]
    if todo and not has_data:
        pytest.skip(f"assay ontology term unresolved for {todo}; look it up in OLS before data arrive")
    assert not todo, f"resolve assay ontology terms for {todo} (OLS: https://www.ebi.ac.uk/ols4)"
