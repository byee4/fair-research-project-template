## Assay notes: bulk RNA-seq (modules/bulk-rnaseq)
- Pipeline: see `workflow/pipeline.yaml` (default nf-core/rnaseq). Generate its input with
  `scripts/export_samplesheet.py`; never hand-edit `workflow/pipeline_samplesheet.csv`.
- Strandedness comes from the kit; `auto` needs a decision record if Salmon's inference disagrees.
- Lanes of one library share `sample_id` (different `lane`); they are not replicates.
- Differential expression: model/contrast come from `docs/experimental_design.md` only.
- Check `star_salmon/salmon.merged.gene_counts.tsv` has every sample before any DE analysis.
