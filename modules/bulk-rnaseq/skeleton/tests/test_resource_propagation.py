"""Every rule/process that requests CPUs must pass them to its tools.
Regression for a real agent failure: a threads param that never reached the aligner."""

import re

import pytest
from conftest import ROOT

SMK = sorted((ROOT / "workflow/snakemake").rglob("*.smk")) + [ROOT / "workflow/snakemake/Snakefile"]
NF = sorted((ROOT / "workflow/nextflow").rglob("*.nf"))


def smk_rules(text):
    for m in re.finditer(r"^rule (\w+):\n(.*?)(?=^rule |\Z)", text, re.S | re.M):
        yield m.group(1), m.group(2)


@pytest.mark.parametrize("path", [p for p in SMK if p.exists()], ids=lambda p: p.name)
def test_snakemake_threads_used(path):
    for name, body in smk_rules(path.read_text()):
        t = re.search(r"threads:\s*(.+)", body)
        if not t or t.group(1).strip() == "1":
            continue
        assert "{threads}" in body, f"rule {name} declares threads but never uses {{threads}}"


@pytest.mark.parametrize("path", NF, ids=lambda p: p.name)
def test_nextflow_cpus_used(path):
    for m in re.finditer(r"process (\w+) \{(.*?)\n\}", path.read_text(), re.S):
        name, body = m.groups()
        if "process_single" in body:
            continue
        assert "${task.cpus}" in body, f"process {name} never uses ${{task.cpus}}"
