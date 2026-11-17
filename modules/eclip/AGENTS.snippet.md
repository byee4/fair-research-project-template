## Assay notes: eCLIP (modules/eclip)
- One row per CLIP replicate, each with its size-matched input (SMInput). `group` = experiment.
- Default pipeline Skipper (Snakemake, conda-based): pin the commit; generate the manifest with
  `scripts/export_samplesheet.py` and check it against the Skipper README for that commit.
- Adapters/barcodes come from the library prep sheet, never guessed. Mismatches show up as low usable reads.
- Enrichment is always relative to SMInput; never report CLIP-only peaks as binding sites.
- RBP identity: HGNC id + antibody catalog/lot in the sample sheet (FAIR + reproducibility).
