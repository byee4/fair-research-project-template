# Assay modules

The project core is assay-agnostic. Everything specific to one kind of data lives here and is
installed by `scripts/init_project.py` at the end of the project interview.

| Module | Variants | Default pipeline(s) |
|---|---|---|
| `bulk-rnaseq` | polyA-stranded, 3prime-tag | nf-core/rnaseq (custom skeleton as fallback) |
| `spatial` | visium, visium-hd, xenium, merscope, cosmx | nf-core/spatialvi (Visium), nf-core/sopa (others) |
| `eclip` | eclip, abc-eclip, encode-eclip | YeoLab/skipper, YeoLab/Mudskipper, YeoLab/eclip |
| `scrnaseq` | 10x 3' v3/v4, Flex/Multiome, Smart-seq | nf-core/scrnaseq |

Each module contains:

| File | Installed as | Purpose |
|---|---|---|
| `module.yaml` | (read by init + interview) | variants, pipelines, interview questions, pitfalls, FAIR targets |
| `samplesheet.schema.json` | `schemas/samplesheet.assay.schema.json` | assay-specific columns, layered on the core schema |
| `rules.yaml` | merged into `schemas/samplesheet.rules.yaml` | cross-row rules (replicates, pairing, consistency) |
| `contracts/<pipeline>.yaml` | `contracts/data_products.yaml` | what the chosen pipeline must output |
| `tests/` | `tests/assay/` | pitfall tests for this assay |
| `AGENTS.snippet.md` | appended to `AGENTS.md` | assay rules for agents |
| `evals.jsonl` | appended to `evals/cases/lab_tasks.jsonl` | agent eval cases |
| `example_samples.tsv` | `config/samples.tsv` (if absent) | a valid starting sheet |
| `skeleton/` (optional) | `workflow/`, `scripts/`, `tests/` | custom pipeline, only when no community pipeline fits |

## Adding a module
Copy `_template/` to `modules/<assay>/`, fill it in (an agent can draft it during the interview),
keep `status: draft` until an assay expert reviews it, and run `pytest tests/test_modules.py`.
