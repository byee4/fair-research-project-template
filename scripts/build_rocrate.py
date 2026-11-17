#!/usr/bin/env python3
"""Package a pipeline run as a Workflow Run RO-Crate for any engine.
(Nextflow pipelines also get one from nf-prov via workflow/provenance.config.)

  build_rocrate.py --results results --name "<project> run YYYY-MM-DD" \
      --author "Jane Doe" --orcid https://orcid.org/0000-...
Includes: pinned pipeline reference (name, version, URL), project profile, sample sheets, schemas,
contracts, manifests, claims and decisions, and result files (large binaries referenced, not copied).
"""

import argparse
import subprocess
from pathlib import Path

import yaml
from rocrate.model.person import Person
from rocrate.rocrate import ROCrate

BIG = {".bam", ".cram", ".fastq", ".gz", ".tif", ".tiff", ".btf", ".zarr", ".h5", ".h5ad"}

ap = argparse.ArgumentParser()
ap.add_argument("--results", default="results")
ap.add_argument("--name", required=True)
ap.add_argument("--author", required=True)
ap.add_argument("--orcid", required=True)
ap.add_argument("--license", default="https://spdx.org/licenses/CC-BY-4.0")
ap.add_argument("--out", default="ro-crate")
a = ap.parse_args()

root = Path(__file__).resolve().parents[1]
crate = ROCrate()
crate.name = a.name
crate.license = a.license
person = crate.add(Person(crate, a.orcid, properties={"name": a.author}))
crate.creator = person
commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=root).stdout.strip()

pipe_p = root / "workflow" / "pipeline.yaml"
pipe = yaml.safe_load(pipe_p.read_text()) if pipe_p.exists() else {}
lang = {"nextflow": "nextflow", "snakemake": "snakemake", "cwl": "cwl"}.get(pipe.get("engine"), None)
wf = (
    crate.add_workflow(pipe_p, "workflow/pipeline.yaml", main=True, lang=lang)
    if lang
    else crate.add_file(pipe_p, "workflow/pipeline.yaml")
)
wf["name"] = pipe.get("name", "unknown")
wf["version"] = pipe.get("version", "unknown")
if pipe.get("url"):
    wf["url"] = pipe["url"]
crate.root_dataset["version"] = commit or "uncommitted"

for rel in [
    "project.yaml",
    "config/samples.tsv",
    "schemas/samplesheet.core.schema.json",
    "schemas/samplesheet.assay.schema.json",
    "schemas/samplesheet.rules.yaml",
    "contracts/data_products.yaml",
    "containers/analysis.def",
    "containers/environment.lock.yml",
    "data/raw/MANIFEST.tsv",
    "data/external/MANIFEST.tsv",
    "claims/claims.yaml",
]:
    p = root / rel
    if p.exists():
        crate.add_file(p, rel)
for p in sorted((root / "workflow").glob("*samplesheet*")) + sorted((root / "workflow").glob("*manifest*")):
    crate.add_file(p, f"workflow/{p.name}")
for p in sorted((root / "decisions").glob("*.md")):
    crate.add_file(p, f"decisions/{p.name}")
res = Path(a.results)
large = []
for p in sorted(res.rglob("*")):
    if not p.is_file():
        continue
    if p.suffix in BIG or any(part.endswith(".zarr") for part in p.parts):
        large.append(f"{p.relative_to(res.parent)}\t{p.stat().st_size}")  # referenced, not copied
    else:
        crate.add_file(p, str(p.relative_to(res.parent)))
listing = root / "logs" / "large_files.tsv"
listing.parent.mkdir(exist_ok=True)
listing.write_text("path\tbytes\n" + "\n".join(large) + "\n")
crate.add_file(
    listing,
    "large_files.tsv",
    properties={"description": "Large outputs referenced by path and size; they stay on project storage / S3"},
)
out = Path(a.out)
crate.write(out)
print(f"wrote {out}/ro-crate-metadata.json")
