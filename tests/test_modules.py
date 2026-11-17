"""Every assay module must be internally consistent before anyone installs it."""

import json
import shutil
import sys

import pytest
import yaml
from check_contracts import static
from conftest import ROOT, read_rows

sys.path.insert(0, str(ROOT / "scripts"))
from init_project import CORE_RULES, merge_rules  # noqa: E402
from validate_samplesheet import check  # noqa: E402

MODULES = sorted(p.parent for p in (ROOT / "modules").glob("*/module.yaml"))
REAL = [m for m in MODULES if not m.name.startswith("_")]
REQUIRED = [
    "name",
    "title",
    "status",
    "variants",
    "pipelines",
    "interview_questions",
    "pitfalls",
    "fair",
    "mini_fixture",
]


@pytest.mark.parametrize("mdir", MODULES, ids=lambda p: p.name)
def test_structure(mdir):
    m = yaml.safe_load((mdir / "module.yaml").read_text())
    missing = [k for k in REQUIRED if k not in m]
    assert not missing, missing
    for f in ["samplesheet.schema.json", "AGENTS.snippet.md", "example_samples.tsv", "tests"]:
        assert (mdir / f).exists(), f"{mdir.name}: missing {f}"
    assert m["status"] in {"draft", "stable"}


@pytest.mark.parametrize("mdir", REAL, ids=lambda p: p.name)
def test_pipelines_and_contracts(mdir):
    m = yaml.safe_load((mdir / "module.yaml").read_text())
    assert m["name"] == mdir.name
    ids = {p["id"] for p in m["pipelines"]}
    for vid, v in m["variants"].items():
        assert v["default_pipeline"] in ids, f"variant {vid} default not in pipelines"
    for p in m["pipelines"]:
        for k in ("id", "name", "engine", "url", "use_when", "contracts"):
            assert k in p, f"{p.get('id')}: missing {k}"
        cfile = mdir / "contracts" / f"{p['contracts']}.yaml"
        assert cfile.exists(), cfile
        assert static(yaml.safe_load(cfile.read_text())) == [], cfile
        if p.get("skeleton"):
            assert (mdir / p["skeleton"]).is_dir()


@pytest.mark.parametrize("mdir", REAL, ids=lambda p: p.name)
def test_example_sheet_valid_under_module(mdir, tmp_path):
    d = tmp_path / "schemas"
    d.mkdir()
    shutil.copy(ROOT / "schemas/samplesheet.core.schema.json", d)
    shutil.copy(mdir / "samplesheet.schema.json", d / "samplesheet.assay.schema.json")
    extra = yaml.safe_load((mdir / "rules.yaml").read_text()) if (mdir / "rules.yaml").exists() else {}
    (d / "samplesheet.rules.yaml").write_text(yaml.safe_dump(merge_rules(CORE_RULES, extra)))
    assert check(mdir / "example_samples.tsv", schema_dir=d) == []


@pytest.mark.parametrize("mdir", REAL, ids=lambda p: p.name)
def test_exports_use_known_columns(mdir):
    import string

    m = yaml.safe_load((mdir / "module.yaml").read_text())
    cols = set(read_rows(mdir / "example_samples.tsv")[0])
    schema_cols = set(json.loads((mdir / "samplesheet.schema.json").read_text())["items"]["properties"])
    core_cols = set(json.loads((ROOT / "schemas/samplesheet.core.schema.json").read_text())["items"]["properties"])
    known = cols | schema_cols | core_cols
    for p in m["pipelines"]:
        for tmpl in (p.get("export") or {}).get("columns", {}).values():
            for _, field, _, _ in string.Formatter().parse(tmpl):
                assert field is None or field in known, f"{p['id']}: export uses unknown column '{field}'"


@pytest.mark.parametrize("mdir", REAL, ids=lambda p: p.name)
def test_evals_well_formed(mdir):
    f = mdir / "evals.jsonl"
    if not f.exists():
        pytest.skip("no eval cases")
    for line in f.read_text().splitlines():
        if line.strip():
            d = json.loads(line)
            assert {"id", "input", "target"} <= set(d)
