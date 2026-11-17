# Choosing a pipeline (agent playbook)

Default to a **maintained community pipeline** pinned to an exact release. Write custom
pipeline code only when no maintained option fits the assay/variant, and say why in
`decisions/0002-assay-and-pipeline.md`.

Check, and tell the user, for each candidate:
- Is it maintained? Last release date; open issues trend; used by the lab already?
- Does it support this exact variant (chemistry, platform version, single/paired-end)?
- Does it run on TSCC (Apptainer/Singularity, Slurm) and/or AWS (Batch/ParallelCluster)?
- What outputs does it produce, and do they match the contracts in `modules/<m>/contracts/`?
- Can provenance be captured (nf-prov for Nextflow; `scripts/build_rocrate.py` otherwise)?

Then pin it: exact tag or commit in `workflow/pipeline.yaml`, plus `verified_on` date.
When a new release appears, upgrading is a decision (re-run the mini fixture; compare expected values).
