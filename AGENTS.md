# AGENTS.md — read before doing anything

## First: is the project set up?
Open `project.yaml`. If `initialized: false`, STOP and run the project interview in
`docs/agent_playbooks/project_interview.md` with the user before writing any code.
Ask the questions; do not guess the assay, platform, organism, or pipeline.

## Rules (all assays)
- `data/raw/` is read-only. Never modify, move, or regenerate raw data.
- Never edit `results/` by hand; results come only from the pinned pipeline in `workflow/pipeline.yaml`.
- Prefer the community pipeline named in `workflow/pipeline.yaml` over writing new pipeline code.
- Do not change reference build/annotation, thresholds, statistical model, contrasts, or the
  pipeline/version without a new `decisions/` file and human approval (`policy/authority.yaml`).
- Do not submit Slurm jobs or write to S3. Propose the command; a human runs it.
- "It ran" is not "it is correct". Done = `bash .agent/done.sh` passes (the Stop hook enforces it)
  AND contracts pass on the mini fixture.
- Label biological interpretation EXPLORATORY unless `claims/claims.yaml` allows more.

## Commands
- Checks: `pre-commit run --all-files` · Tests: `pytest -q`
- Sample sheet: `python3 scripts/validate_samplesheet.py config/samples.tsv`
- Pipeline input: `python3 scripts/export_samplesheet.py`
- Contracts: `python3 scripts/check_contracts.py --results <dir>` · Claims: `python3 scripts/check_claims.py`

## Guard rails (enforced for every agent)
`.agent/hooks/pre_tool_guard.py` applies `policy/authority.yaml`: it blocks raw-data edits,
force-push/push to `main`, `--no-verify`, `.env` access; it asks before Slurm, S3, installs, and
edits to scientific config or the agent control plane. Claude Code auto mode does not bypass it.
Skills: `.agents/skills/` (project-interview, data-intake, ship-change).

## Where things are
Project profile `project.yaml` · Policy `policy/authority.yaml` · Schemas `schemas/` ·
Contracts `contracts/` · Assay module source `modules/<assay>/` · Past mistakes `tests/regressions/`

## Reporting
Finish with: files changed, tests run (paste output), open questions for the human.
