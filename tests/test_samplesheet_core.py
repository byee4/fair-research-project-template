"""Core (assay-agnostic) sample-sheet rules, tested with the core schema only."""

import shutil

import pytest
import yaml
from conftest import ROOT
from init_project import CORE_RULES
from validate_samplesheet import check

HEADER = ["sample_id", "condition", "replicate", "group", "batch", "organism_taxon", "biosample", "source"]


def row(sid, cond, rep, **kw):
    r = dict(
        sample_id=sid,
        condition=cond,
        replicate=rep,
        group="",
        batch="",
        organism_taxon="NCBITaxon:9606",
        biosample="CVCL_0030",
        source="test",
    )
    r.update(kw)
    return r


@pytest.fixture
def core_only(tmp_path):
    d = tmp_path / "schemas"
    d.mkdir()
    shutil.copy(ROOT / "schemas/samplesheet.core.schema.json", d)
    (d / "samplesheet.rules.yaml").write_text(yaml.safe_dump(CORE_RULES))  # core rules only
    return d


def write(tmp_path, rows):
    p = tmp_path / "s.tsv"
    p.write_text("\n".join(["\t".join(HEADER)] + ["\t".join(str(r.get(c, "")) for c in HEADER) for r in rows]) + "\n")
    return p


GOOD = [row("C1", "control", 1), row("C2", "control", 2), row("T1", "treated", 1), row("T2", "treated", 2)]


def test_good(tmp_path, core_only):
    assert check(write(tmp_path, GOOD), schema_dir=core_only) == []


@pytest.mark.parametrize(
    "bad, needle",
    [
        ([*GOOD[:3], row("C1", "treated", 2)], "duplicate sample_id"),
        ([*GOOD[:3], row("T2", "treated", 1)], "duplicate condition/replicate"),
        ([*GOOD[:3]], "design requires >= 2"),
        ([*GOOD[:3], row("T2", "treated", 2, organism_taxon="human")], "does not match"),
        ([*GOOD[:3], row("T2", "treated", 2, biosample="HEK293")], "does not match"),
        ([*GOOD[:3], row("T-2", "treated", 2)], "does not match"),
    ],
)
def test_bad(tmp_path, core_only, bad, needle):
    errs = check(write(tmp_path, bad), schema_dir=core_only)
    assert any(needle in e for e in errs), errs
