"""Compare a real mini-fixture run against hand-verified expected values.
Skips until the pipeline has been run on the mini fixture (results_test/)."""

import csv

import pytest
import yaml
from check_contracts import CONTRACTS, dynamic
from conftest import ROOT

RES = ROOT / "results_test"
EXP = yaml.safe_load((ROOT / "tests/fixtures/mini_expected.yaml").read_text())
pytestmark = pytest.mark.skipif(not RES.exists(), reason="run the pipeline on tests/fixtures/mini first")


def test_contracts_on_mini_run():
    assert dynamic(yaml.safe_load(CONTRACTS.read_text()), RES, ROOT / "tests/fixtures/mini/samples.tsv") == []


@pytest.mark.parametrize("rel,spec", EXP["outputs"].items())
def test_outputs(rel, spec):
    p = RES / rel
    assert p.exists()
    if p.suffix == ".tsv":
        rows = list(csv.DictReader(open(p), delimiter="\t"))
        if spec.get("columns"):
            assert list(rows[0].keys()) == spec["columns"]
        if spec.get("rows") is not None:
            assert len(rows) == spec["rows"]


@pytest.mark.parametrize("sample,stage,col,expected,tol", EXP["values"])
def test_values(sample, stage, col, expected, tol):
    if expected is None:
        pytest.skip("expected value not recorded yet")
    rows = list(csv.DictReader(open(RES / "qc/qc_summary.tsv"), delimiter="\t"))
    r = next(r for r in rows if r["sample_id"] == sample and r["stage"] == stage)
    assert abs(float(r[col]) - expected) <= tol
