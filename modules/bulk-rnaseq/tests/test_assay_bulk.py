"""Bulk RNA-seq pitfalls, encoded as tests (installed to tests/assay/ by init_project.py)."""

import copy

import pytest
from conftest import ROOT, batch_confounded, read_rows, write_rows
from validate_samplesheet import check

SHEET = ROOT / "config/samples.tsv"
BASE = read_rows(SHEET)


def test_project_sheet_valid():
    assert check(SHEET) == []


def test_batch_not_confounded():
    assert not batch_confounded(BASE), "every batch holds a single condition: condition effect is not estimable"


def mutated(fn):
    rows = copy.deepcopy(BASE)
    fn(rows)
    return rows


@pytest.mark.parametrize(
    "fn, needle",
    [
        (lambda rs: rs[0].pop("strandedness"), "strandedness"),
        (lambda rs: rs[0].__setitem__("strandedness", "yes"), "is not one of"),
        (lambda rs: rs[0].__setitem__("fastq_2", ""), "filled for some rows"),
        (lambda rs: rs.append({**rs[0], "lane": "L002", "condition": "treatment"}), "mixes incompatible"),
        (lambda rs: rs.append({**rs[0]}), "duplicate"),
        (lambda rs: rs[1].__setitem__("fastq_1", rs[0]["fastq_1"]), "duplicate fastq_1"),
    ],
)
def test_bad_sheets_rejected(tmp_path, fn, needle):
    errs = check(write_rows(tmp_path, mutated(fn)))
    assert any(needle in e for e in errs), errs


def test_lanes_merge_ok(tmp_path):
    rows = mutated(
        lambda rs: rs.append(
            {**rs[0], "lane": "L002", "fastq_1": "data/raw/x_R1.fastq.gz", "fastq_2": "data/raw/x_R2.fastq.gz"}
        )
    )
    assert check(write_rows(tmp_path, rows)) == []
