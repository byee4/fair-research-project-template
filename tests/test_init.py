"""Smoke test: installing each module's pipelines into a fresh copy yields a passing project."""

import os
import shutil
import subprocess
import sys

import pytest
import yaml
from conftest import ROOT

if os.environ.get("INIT_SMOKE"):
    pytest.skip("inside an init smoke copy", allow_module_level=True)

CASES = []
for mf in sorted((ROOT / "modules").glob("*/module.yaml")):
    if mf.parent.name.startswith("_"):
        continue
    m = yaml.safe_load(mf.read_text())
    for p in m["pipelines"]:
        variant = next(
            (vid for vid, v in m["variants"].items() if v["default_pipeline"] == p["id"]), next(iter(m["variants"]))
        )
        CASES.append((m["name"], variant, p["id"]))

IGNORE = shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", ".ruff_cache", "results_test", ".snakemake")


@pytest.mark.parametrize("assay,variant,pipeline", CASES, ids=["/".join(c) for c in CASES])
def test_init_then_tests_pass(tmp_path, assay, variant, pipeline):
    repo = tmp_path / "repo"
    shutil.copytree(ROOT, repo, ignore=IGNORE)
    for p in ("config/samples.tsv", "logs/agent/audit.jsonl"):
        (repo / p).unlink(missing_ok=True)
    py = sys.executable
    r = subprocess.run(
        [
            py,
            "scripts/init_project.py",
            "--assay",
            assay,
            "--variant",
            variant,
            "--pipeline",
            pipeline,
            "--version",
            "0.0.0-smoke",
            "--organism",
            "NCBITaxon:9606",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    proj = yaml.safe_load((repo / "project.yaml").read_text())
    assert proj["initialized"] and proj["assay"]["module"] == assay
    assert (repo / "schemas/samplesheet.assay.schema.json").exists()
    assert "<!-- assay:start -->" in (repo / "AGENTS.md").read_text()
    # second init without --force must refuse
    r2 = subprocess.run(
        [
            py,
            "scripts/init_project.py",
            "--assay",
            assay,
            "--variant",
            variant,
            "--pipeline",
            pipeline,
            "--version",
            "0.0.0-smoke",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert r2.returncode == 1
    env = {**os.environ, "INIT_SMOKE": "1"}
    t = subprocess.run(
        [py, "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=repo, capture_output=True, text=True, env=env
    )
    assert t.returncode == 0, t.stdout[-3000:]


def test_version_latest_refused(tmp_path):
    repo = tmp_path / "repo"
    shutil.copytree(ROOT, repo, ignore=IGNORE)
    r = subprocess.run(
        [
            sys.executable,
            "scripts/init_project.py",
            "--assay",
            "bulk-rnaseq",
            "--variant",
            "polyA-stranded",
            "--version",
            "latest",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 1 and "exact release" in r.stderr
