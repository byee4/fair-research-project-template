# FAIR, agent-ready project template (TSCC + AWS)

A starting point for a new lab project that works for **any assay**. The core handles what every
project needs (FAIR metadata, immutable raw data, guard rails for coding agents, validation gates,
provenance). Assay-specific pieces live in `modules/` and are installed after a short
**project interview** that your coding agent runs with you.

## Start here (first week)

1. `bash scripts/setup.sh`
2. Open your coding agent (Claude Code, Codex, Cursor, …) in this folder and say:
   **"I'm starting a new project."** It reads `AGENTS.md`, sees the project is not set up,
   and walks you through `docs/agent_playbooks/project_interview.md`: your question, assay and
   platform, replicates, organism, data sources, compute. It then recommends a maintained
   community pipeline, pins its current release, and installs the matching module.
   (No agent? `python3 scripts/init_project.py --list`, then run it with your choices.)
3. Finish `docs/experimental_design.md` with your PI **before data arrive**.
4. List your expected samples in `config/samples.tsv`; run `python3 scripts/validate_samplesheet.py`.

Everything else (tests, contracts, claims, evals, provenance) becomes useful as you go;
`docs/` and the implementation plan explain when.

## Available assay modules

| Module | Variants | Default pipeline(s) |
|---|---|---|
| `bulk-rnaseq` | polyA/rRNA-depleted stranded, 3' tag | nf-core/rnaseq |
| `spatial` | Visium, Visium HD, Xenium, MERSCOPE, CosMx | nf-core/spatialvi (Visium), nf-core/sopa |
| `eclip` | eCLIP, antibody-barcode eCLIP, ENCODE-style | YeoLab/skipper, Mudskipper, YeoLab/eclip |
| `scrnaseq` | 10x 3' v3/v4, Flex/Multiome, Smart-seq | nf-core/scrnaseq |

Not listed? The interview drafts a new module from `modules/_template/` (marked draft until an
assay expert reviews it).

## Layout

```
AGENTS.md / CLAUDE.md   agent briefing (assay notes appended at init)
project.yaml            project profile: assay, pipeline + pinned version, organism, people
docs/agent_playbooks/   project interview, choosing a pipeline
modules/<assay>/        assay-specific schema, rules, contracts, tests, notes (source of truth)
schemas/                core sample-sheet schema (+ installed assay schema and rules)
contracts/              what the pinned pipeline must output (installed from the module)
workflow/pipeline.yaml  pinned community pipeline (or a custom skeleton under workflow/)
config/samples.tsv      the one FAIR sample sheet; pipeline inputs are generated from it
policy/authority.yaml   what agents may do alone / must ask / never do
.agent/                 enforced agent control plane: hooks, done.sh, install/ (Claude, Codex, CI)
.agents/skills/         agent runbooks: project-interview, data-intake, ship-change
claims/ decisions/      claim -> evidence graph; recorded scientific decisions
data/raw/               immutable raw data + checksum manifest
evals/                  agent evaluation suites
infra/                  TSCC and AWS notes, Slurm launcher, S3 policy
```
