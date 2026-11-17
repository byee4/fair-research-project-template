# Data intake checklist (run for every delivery)

- [ ] Delivery recorded: source, order/accession id, date, contact
- [ ] Files copied to project storage; made read-only (`chmod -R a-w`)
- [ ] md5 manifest created and verified against provider checksums
- [ ] Sample sheet rows added with ontology ids (assay EFO/OBI, NCBITaxon, Cellosaurus/UBERON/CL)
- [ ] `python3 scripts/validate_samplesheet.py config/samples.tsv` passes
- [ ] Mini fixture still passes (`pytest -q`)
- [ ] Spot-check: read length, pairing, read-name format, and chromosome naming match expectations
- [ ] Mirror to S3 (if cloud compute planned) — human runs `aws s3 sync`
- [ ] Controlled-access data? Confirm DUA terms; mark in sample sheet `source`; never send to external model APIs unless the DUA and UCSD policy allow it
- [ ] Update `docs/experimental_design.md` Deviations if anything differs from plan
