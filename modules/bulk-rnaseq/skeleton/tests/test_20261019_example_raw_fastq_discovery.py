"""Example regression: an agent globbed FASTQs in the top-level directory only and
silently dropped samples delivered in per-lane subdirectories. Fix: sample sheet is the
only source of input paths; the workflow must never glob data/raw."""

from conftest import ROOT


def test_workflows_do_not_glob_raw_data():
    for p in (
        list((ROOT / "workflow").rglob("*.smk"))
        + list((ROOT / "workflow").rglob("*.nf"))
        + [ROOT / "workflow/snakemake/Snakefile"]
    ):
        txt = p.read_text()
        assert 'glob_wildcards("data/raw' not in txt and "fromPath('data/raw" not in txt, p
