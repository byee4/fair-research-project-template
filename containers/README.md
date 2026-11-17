# Containers

- **Community pipelines** (nf-core, etc.) ship their own pinned containers: run them with
  `-profile singularity` on TSCC. Nothing to build here.
- **Your own downstream code** (notebooks, R/Python analysis, a custom skeleton) runs in
  `analysis.def`, built from a locked conda environment:
  1. write `containers/environment.yml` (the bulk-rnaseq skeleton installs an example),
  2. `conda-lock -f containers/environment.yml -p linux-64` → commit `environment.lock.yml`,
  3. `apptainer build analysis.sif containers/analysis.def` (or `--remote`), copy to project storage,
     record `sha256sum analysis.sif` in `containers/SIF_SHA256`.
- Snakemake pipelines that use conda (e.g. Skipper) build envs on first run: pin the pipeline
  commit and the Snakemake version in `workflow/pipeline.yaml`.
