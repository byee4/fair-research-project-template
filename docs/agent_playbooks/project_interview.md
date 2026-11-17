# Project interview (agent playbook)

**Purpose.** Turn a new student's project into a configured repo by asking questions,
not by guessing. Run this when `project.yaml` has `initialized: false`, or when the user
says they are starting a project. Works with any agent: follow the steps in order.

**Tone.** The user may be a first-year student. Ask one short group of questions at a time,
explain why each matters in one sentence, accept "I don't know" and record it as an open
question for their PI instead of inventing an answer.

## Step 1 — The science (record in `project.yaml: project` and `docs/experimental_design.md`)
1. In one sentence, what question does this project answer?
2. Who is your PI? Your ORCID and theirs (offer to explain ORCID if unknown)?
3. What are the conditions you are comparing, and how many biological replicates per condition?
4. Are there batches (different prep days, sequencing runs, slides)? Are conditions balanced across them?

## Step 2 — The assay (choose the module)
5. What kind of data is coming? Offer the installed modules (`python3 scripts/init_project.py --list`):
   - bulk RNA-seq → `bulk-rnaseq`
   - spatial transcriptomics (Visium, Visium HD, Xenium, MERSCOPE, CosMx) → `spatial`
   - eCLIP / CLIP-seq → `eclip`
   - single-cell / single-nucleus RNA-seq → `scrnaseq`
   - something else → go to **Step 2b**
6. Ask the module's own questions: open `modules/<module>/module.yaml` → `interview_questions`,
   ask each one, and map answers to a `variant`.

### Step 2b — No matching module
Say so plainly. Then: (a) search for a maintained community pipeline (nf-core, Snakemake
workflow catalog, the vendor's pipeline, lab repos); (b) propose creating `modules/<new-assay>/`
from `modules/_template/`; (c) mark the new module `status: draft` and tell the user a
human expert must review its schema and contracts before real data are processed.

## Step 3 — Organism, references, data sources
7. Organism (→ NCBITaxon id) and reference build/annotation the lab uses for this organism.
8. For each data source: who delivers it, expected date, file types, and whether it is
   controlled-access (dbGaP / DUA). Record in `project.yaml: data_sources`.
9. Compute: TSCC, AWS, or both? Do you have a TSCC allocation/partition/QOS?

## Step 4 — Choose the pipeline (see `docs/agent_playbooks/choose_pipeline.md`)
10. Recommend the module's default pipeline for the variant, and explain the alternatives in
    plain language. Prefer a maintained community pipeline over custom code.
11. **Look up the current release yourself** (release page / registry). Never pin "latest".
    Tell the user the version and date you checked.
12. Ask whether the lab already uses a specific version or config (a senior student or staff
    scientist often knows). If yes, use theirs and note it.

## Step 5 — Install and hand off
13. Run: `python3 scripts/init_project.py --assay <m> --variant <v> --pipeline <id> --version <tag> --organism <NCBITaxon:id>`
    If `assay.ontology_term` is still null afterwards, look the assay up in OLS (https://www.ebi.ac.uk/ols4)
    and fill it in `project.yaml` and in the sample sheet's `assay` column.
14. Fill `project.yaml` fields the script did not (name, question, people, data sources, compute).
15. Draft `docs/experimental_design.md` from the answers. Leave unknowns as `TODO(ask PI): ...`.
16. Run `pytest -q` and `python3 scripts/validate_samplesheet.py` and show the output.
17. Summarize for the user: what was set up, the 3 things to do this week
    (finish the design doc with PI; list expected samples in `config/samples.tsv`;
    build the mini fixture per `modules/<m>/README.md`), and open questions for the PI.

Do not write pipeline code during the interview.
