#!/usr/bin/env python3
"""Install an assay module into this project (run by the agent at the end of the
project interview, or by a human). Assay-specific files live only in modules/<assay>/;
this script copies the chosen ones into place and records the choice.

  init_project.py --list
  init_project.py --assay spatial --variant visium-hd --pipeline nf-core/sopa --version 1.0.1
  init_project.py --assay bulk-rnaseq --pipeline custom-skeleton --version 0.1.0 --organism NCBITaxon:9606

Never pass --version latest: look up the current release, then pin it.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULES = ROOT / "modules"
START, END = "<!-- assay:start -->", "<!-- assay:end -->"


def modules() -> dict[str, dict]:
    out = {}
    for m in sorted(MODULES.glob("*/module.yaml")):
        if m.parent.name.startswith("_"):
            continue
        out[m.parent.name] = yaml.safe_load(m.read_text())
    return out


def list_modules() -> None:
    for name, m in modules().items():
        print(f"{name}: {m['title']}")
        for vid, v in m.get("variants", {}).items():
            print(f"    variant {vid}: {v['title']}  (default pipeline: {v.get('default_pipeline')})")
        for p in m.get("pipelines", []):
            print(f"    pipeline {p['id']} [{p['engine']}]: {p['use_when']}")


def merge_rules(core: dict, extra: dict) -> dict:
    """Module rules extend core rules; keys listed in `replace:` override them instead."""
    extra = dict(extra or {})
    replace = set(extra.pop("replace", []))
    out = {k: list(v) for k, v in core.items()}
    for k, v in extra.items():
        if k in replace:
            out[k] = list(v)
            continue
        out.setdefault(k, [])
        for item in v:
            if item not in out[k]:
                out[k].append(item)
    return out


CORE_RULES = {
    "unique": [["sample_id"], ["condition", "replicate"]],
    "all_or_none": [],
    "consistent_within": [],
    "consistent_all": [],
    "min_per_value": [{"column": "condition", "min": 2, "distinct": "replicate"}],
    "path_columns": [],
}


def install_agents_snippet(text: str) -> None:
    p = ROOT / "AGENTS.md"
    body = p.read_text()
    block = f"{START}\n{text.strip()}\n{END}"
    if START in body:
        body = body[: body.index(START)] + block + body[body.index(END) + len(END) :]
    else:
        body = body.rstrip() + "\n\n" + block + "\n"
    p.write_text(body)


def append_evals(src: Path) -> None:
    dst = ROOT / "evals" / "cases" / "lab_tasks.jsonl"
    have = {json.loads(line)["id"] for line in dst.read_text().splitlines() if line.strip()}
    new = [line for line in src.read_text().splitlines() if line.strip() and json.loads(line)["id"] not in have]
    if new:
        with open(dst, "a") as fh:
            fh.write("\n".join(new) + "\n")


def copytree(src: Path, dst: Path) -> None:
    if src.exists():
        shutil.copytree(src, dst, dirs_exist_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--assay")
    ap.add_argument("--variant")
    ap.add_argument("--pipeline", help="pipeline id from module.yaml (default: the variant's default)")
    ap.add_argument("--version", help="exact release tag/commit you verified is current")
    ap.add_argument("--organism", help="NCBITaxon id, e.g. NCBITaxon:9606")
    ap.add_argument("--force", action="store_true", help="re-initialize (overwrites assay files)")
    a = ap.parse_args()
    if a.list or not a.assay:
        list_modules()
        return 0

    mods = modules()
    if a.assay not in mods:
        print(
            f"unknown assay module '{a.assay}'. Known: {sorted(mods)}. "
            f"To add one, copy modules/_template/ (see modules/README.md).",
            file=sys.stderr,
        )
        return 1
    m, mdir = mods[a.assay], MODULES / a.assay
    variants = m.get("variants", {})
    variant = a.variant or (next(iter(variants)) if len(variants) == 1 else None)
    if variants and variant not in variants:
        print(f"choose --variant from {sorted(variants)}", file=sys.stderr)
        return 1
    v = variants.get(variant, {})
    pid = a.pipeline or v.get("default_pipeline")
    pipes = {p["id"]: p for p in m.get("pipelines", [])}
    if pid not in pipes:
        print(f"choose --pipeline from {sorted(pipes)}", file=sys.stderr)
        return 1
    pipe = pipes[pid]
    if not a.version or a.version.lower() in {"latest", "main", "master", "dev"}:
        print(
            f"--version must be an exact release. Check {pipe.get('releases_url', pipe.get('url'))} "
            f"and pass the current tag.",
            file=sys.stderr,
        )
        return 1

    proj_p = ROOT / "project.yaml"
    proj = yaml.safe_load(proj_p.read_text())
    if proj.get("initialized") and not a.force:
        print("project already initialized; pass --force to re-initialize (records a new decision).", file=sys.stderr)
        return 1

    # 1. sample-sheet schema + rules
    shutil.copy(mdir / "samplesheet.schema.json", ROOT / "schemas" / "samplesheet.assay.schema.json")
    extra = yaml.safe_load((mdir / "rules.yaml").read_text()) if (mdir / "rules.yaml").exists() else {}
    (ROOT / "schemas" / "samplesheet.rules.yaml").write_text(
        f"# Generated by init_project.py from core rules + modules/{a.assay}/rules.yaml\n"
        + yaml.safe_dump(merge_rules(CORE_RULES, extra), sort_keys=False)
    )
    # 2. contracts for the chosen pipeline
    contract = mdir / "contracts" / f"{pipe['contracts']}.yaml"
    shutil.copy(contract, ROOT / "contracts" / "data_products.yaml")
    # 3. tests, evals, agent notes
    copytree(mdir / "tests", ROOT / "tests" / "assay")
    if (mdir / "evals.jsonl").exists():
        append_evals(mdir / "evals.jsonl")
    install_agents_snippet((mdir / "AGENTS.snippet.md").read_text())
    # 4. example sample sheet (never overwrite a real one)
    sheet = ROOT / "config" / "samples.tsv"
    sheet.parent.mkdir(exist_ok=True)
    if not sheet.exists():
        shutil.copy(mdir / "example_samples.tsv", sheet)
    # 5. workflow: community pipeline reference, or the custom skeleton
    wf = ROOT / "workflow"
    wf.mkdir(exist_ok=True)
    if pipe.get("skeleton"):
        sk = mdir / pipe["skeleton"]
        copytree(sk / "workflow", wf)
        copytree(sk / "scripts", ROOT / "scripts")
        copytree(sk / "tests", ROOT / "tests" / "assay")
        copytree(sk / "fixtures", ROOT / "tests" / "fixtures")
        for f in ("config.yaml", "config.schema.json", "environment.yml"):
            if (sk / f).exists():
                dest = {
                    "config.yaml": ROOT / "config",
                    "config.schema.json": ROOT / "schemas",
                    "environment.yml": ROOT / "containers",
                }[f]
                shutil.copy(sk / f, dest / f)
    pipeline_yaml = {
        "id": pid,
        "name": pipe["name"],
        "version": a.version,
        "engine": pipe["engine"],
        "url": pipe.get("url"),
        "launch": pipe.get("launch"),
        "outdir": pipe.get("outdir", "results"),
        "samplesheet_export": pipe.get("export"),
        "verified_on": dt.date.today().isoformat(),
    }
    (wf / "pipeline.yaml").write_text(
        "# Pinned pipeline for this project. Changing name/version requires a decisions/ record.\n"
        + yaml.safe_dump(pipeline_yaml, sort_keys=False)
    )
    if pipe["engine"] == "nextflow" and not pipe.get("skeleton"):
        (wf / "provenance.config").write_text(PROV_CONFIG)
    # 6. project profile + decision record
    proj["assay"].update(
        module=a.assay,
        variant=variant,
        ontology_term=v["ontology_term"] if "ontology_term" in v else m.get("ontology_term"),
    )
    proj["pipeline"].update(
        mode="custom" if pipe.get("skeleton") else "community",
        name=pipe["name"],
        version=a.version,
        engine=pipe["engine"],
        verified_on=dt.date.today().isoformat(),
    )
    if a.organism:
        proj["organism"]["taxon"] = a.organism
    proj["initialized"] = True
    proj_p.write_text(yaml.safe_dump(proj, sort_keys=False))
    write_decision(a.assay, variant, pipe, a.version, m)
    print(NEXT_STEPS.format(assay=a.assay, pipeline=pipe["name"], version=a.version))
    return 0


PROV_CONFIG = """// Added to community Nextflow pipelines with: -c workflow/provenance.config
plugins { id 'nf-prov@1.4.0' }
prov {
    enabled = true
    formats {
        wrroc {
            file = "${params.outdir}/ro-crate-metadata.json"
            overwrite = true
            agent {
                name  = "<Your Name>"
                orcid = "https://orcid.org/0000-0000-0000-0000"
            }
            license = "https://spdx.org/licenses/CC-BY-4.0"
        }
    }
}
"""

NEXT_STEPS = """
Installed assay module '{assay}' with pipeline {pipeline} @ {version}.
Next:
  0. If project.yaml assay.ontology_term is null, look the assay up in OLS (https://www.ebi.ac.uk/ols4).
  1. Review decisions/0002-assay-and-pipeline.md with your PI and fill 'Approved by'.
  2. Replace the example rows in config/samples.tsv; run: python3 scripts/validate_samplesheet.py
  3. Read the 'Assay notes' section now appended to AGENTS.md.
  4. Build the mini fixture described in modules/{assay}/README.md.
  5. pytest -q
"""


def write_decision(assay, variant, pipe, version, m) -> None:
    d = ROOT / "decisions" / "0002-assay-and-pipeline.md"
    alts = "\n".join(f"{i + 1}. {p['name']} — {p['use_when']}" for i, p in enumerate(m.get("pipelines", [])))
    d.write_text(f"""# 0002 — Assay module and pipeline

- Date: {dt.date.today().isoformat()}
- Domain: methods
- Authority level: human_approval
- Proposed by: <agent/human> during project interview
- Approved by: PENDING

## Context
Assay module `{assay}` (variant `{variant}`), from the project interview.

## Options considered
{alts}

## Decision
Use **{pipe["name"]} @ {version}** ({pipe["engine"]}). Reason: {pipe["use_when"]}

## Uncertainty
{pipe.get("caveats", "See modules/" + assay + "/README.md")}

## Consequences / re-validation triggered
Changing pipeline or version re-opens the execution gate for every claim.
""")


if __name__ == "__main__":
    sys.exit(main())
