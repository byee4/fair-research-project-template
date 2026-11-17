"""Replace with this assay's pitfall tests (see other modules for the pattern)."""

from conftest import ROOT
from validate_samplesheet import check


def test_project_sheet_valid():
    assert check(ROOT / "config/samples.tsv") == []
