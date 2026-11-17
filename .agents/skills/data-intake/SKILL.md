---
name: data-intake
description: Register a new raw-data delivery — read-only copy, checksum manifest, sample-sheet rows with ontology ids, validation. Use when the user says data arrived from a core, collaborator, or public accession.
---

# Data intake

Follow `docs/data_intake_checklist.md`. The agent prepares; a human runs anything that copies,
changes permissions on, or uploads data.

1. Ask: source (core order / collaborator / accession), delivery path, controlled-access status (DUA?).
2. Propose (human runs): copy to project storage, `chmod -R a-w <delivery>`.
3. `python3 scripts/make_manifest.py create <delivery> --source "<source>" --glob "<raw_globs>" --append data/raw/MANIFEST.tsv`
   then `python3 scripts/make_manifest.py verify data/raw/MANIFEST.tsv`.
4. Add sample-sheet rows (ontology ids, md5s) and run `python3 scripts/validate_samplesheet.py --check-files`.
5. Spot-check read structure/naming against the module's expectations; report anything surprising.
6. `bash .agent/done.sh`. Record deviations from the design in `docs/experimental_design.md`.

Controlled-access data never goes to an external model API unless the DUA and UCSD policy allow it.
